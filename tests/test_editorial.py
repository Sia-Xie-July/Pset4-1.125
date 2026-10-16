"""Fixture-only editorial/content contract tests; no paid/model API calls."""
import json
import os
from copy import deepcopy
from pathlib import Path

import pytest
from editorial_fixture import build
from lib.model_provider import ask
from lib.schemas import RESPONSES


@pytest.fixture
def series(tmp_path):
    return build(tmp_path)


def stream(values):
    return ''.join(json.dumps(value)+'\n' for value in values)


def fixture_response(repo,stage,change):
    path=repo/'model-fixtures'/f'{stage}.json'
    fixture=json.loads(path.read_text())
    change(fixture)
    path.write_text(json.dumps(fixture))


def prepare(run,decisions,briefs):
    (run/'decisions.jsonl').write_text(stream(decisions))
    (run/'briefs.jsonl').write_text(stream(briefs))


def receipt(run,stage):
    files=list((run/'logs').glob(stage+'-*-completed.json'))+list((run/'logs').glob(stage+'-*-failed.json'))
    return json.loads(max(files,key=lambda p:p.stat().st_mtime_ns).read_text())


def test_all_stages_and_workflow_with_verified_refs(series):
    repo,run,env,items,decisions,briefs,command=series
    result=command('workflows/create_series.sh','runs/fictional-series')
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout)['status']=='awaiting_review'
    assert len((run/'decisions.jsonl').read_text().splitlines())==12
    assert len((run/'briefs.jsonl').read_text().splitlines())==3
    for stage,folder in [('write_articles','articles'),('write_video_scripts','video_scripts')]:
        assert len((run/(folder+'.jsonl')).read_text().splitlines())==3
        for piece in ('01','02','03'):
            text=(run/folder/(piece+'.md')).read_text()
            assert 'EXAMPLE/REPLAY OUTPUT' in text and piece+'-c1' in text
            assert '## Sources' in text and '0–3 seconds' in text
            assert '2026-10-14' in text
        log=receipt(run,stage)
        assert log['models'][0]['name']=='FICTIONAL-model'
        assert log['model_calls'][0]['input_tokens']==100 and log['model_calls'][0]['output_tokens']==50
        assert log['cost_usd']==0 and log['simulated_cost_usd']==pytest.approx(0.000125)
        assert log['model_duration_seconds']>=0 and log['duration_seconds']>=log['model_duration_seconds']
    review=json.loads((run/'review.json').read_text())
    assert review['passed'] and review['human_review_required']
    assert not (run/'approval.json').exists()
    audits=list((run/'prompts/rendered').glob('*.json'))
    assert len(audits)==4
    for path in audits:
        audit=json.loads(path.read_text())
        assert (run/'config/editorial_policy.md').read_text() in audit['messages'][0]['content']
        assert (run/'prompts/select_items.md').read_text() in audit['messages'][0]['content']
        assert audit['fixture'] is True


def test_resume_from_briefs_preserves_decisions(series):
    repo,run,env,items,decisions,briefs,command=series
    prepare(run,decisions,briefs)
    original=(run/'decisions.jsonl').read_bytes()
    result=command('run.sh','--resume-series','runs/fictional-series')
    assert result.returncode==0,result.stderr
    report=json.loads(result.stdout)
    assert report['status']=='awaiting_review'
    assert not report['unmatched_running_stages']
    assert (run/'decisions.jsonl').read_bytes()==original
    assert not list((run/'logs').glob('select_items-*.json'))
    assert list((run/'attempts').glob('*/briefs.jsonl'))


@pytest.mark.parametrize('fault',['json','shape','missing_decision','wrong_version'])
def test_selection_rejects_malformed_output_and_preserves_usage(series,fault):
    repo,run,env,items,decisions,briefs,command=series
    def alter(f):
        if fault=='json': f['content']='{bad'
        elif fault=='shape': f['output']['decisions'][0]['decision']='invent'
        elif fault=='missing_decision': f['output']['decisions'].pop()
        else: f['output']['decisions'][0]['version_id']='not-stored'
    fixture_response(repo,'select_items',alter)
    result=command('editorial/select_items.sh','runs/fictional-series',input=stream(items))
    assert result.returncode==2 and result.stdout==''
    log=receipt(run,'select_items')
    assert log['output_count']==0 and log['errors']
    assert log['model_calls'][0]['input_tokens']==100
    assert list((run/'model_outputs').glob('select_items-*.txt'))


@pytest.mark.parametrize('fault',['quote','segment','version','unknown_source','duplicate_piece','two_briefs'])
def test_briefs_reject_invented_evidence_and_bad_shapes(series,fault):
    repo,run,env,items,decisions,briefs,command=series
    def alter(f):
        output=f['output']['briefs']
        refs=output[0]['claims'][0]['evidence']
        if fault=='quote': refs[0]['locator']['quote']='Invented quotation absent from all retained text'
        elif fault=='segment': refs[1]['locator']['segment_id']='nonexistent-segment'
        elif fault=='version': refs[0]['version_id']='fabricated-version'
        elif fault=='unknown_source': refs[0]['item_id']='invented-source'
        elif fault=='duplicate_piece': output[1]['piece_id']='01'
        else: output.pop()
    fixture_response(repo,'create_briefs',alter)
    result=command('editorial/create_briefs.sh','runs/fictional-series',input=stream(decisions))
    assert result.returncode==2 and result.stdout==''
    assert receipt(run,'create_briefs')['output_count']==0


def test_insufficient_accepted_evidence_exits_one_before_model(series):
    repo,run,env,items,decisions,briefs,command=series
    decisions[2]['decision']='defer'; decisions[2]['piece_ids']=[]
    result=command('editorial/create_briefs.sh','runs/fictional-series',input=stream(decisions))
    assert result.returncode==1 and result.stdout==''
    assert 'Insufficient accepted evidence' in result.stderr
    assert receipt(run,'create_briefs')['model_calls']==[]
    assert not (run/'model_outputs').exists()


@pytest.mark.parametrize('stage',['write_articles','write_video_scripts'])
@pytest.mark.parametrize('fault',['unsupported_claim','missing_marker'])
def test_content_rejects_unsupported_output_before_files(series,stage,fault):
    repo,run,env,items,decisions,briefs,command=series
    prepare(run,decisions,briefs)
    def alter(f):
        doc=f['output']['documents'][0]
        if fault=='unsupported_claim': doc['claims'][0]['statement']='An invented claim absent from the brief'
        else: doc['markdown']=doc['markdown'].replace('01-c1','')
    fixture_response(repo,stage,alter)
    result=command('content/'+stage+'.sh','runs/fictional-series',input=stream(briefs))
    assert result.returncode==2 and result.stdout==''
    assert not (run/('articles' if stage=='write_articles' else 'video_scripts')).exists()


def test_quote_marked_prose_warns_without_blocking_drafts(series):
    repo,run,env,items,decisions,briefs,command=series
    fixture_response(repo,'write_articles',lambda f:f['output']['documents'][0].update(
        markdown=f['output']['documents'][0]['markdown']+'\nSuggested pilot label: "review first".'))
    result=command('workflows/create_series.sh','runs/fictional-series')
    assert result.returncode==0,result.stderr
    assert receipt(run,'write_articles')['warnings']
    review=json.loads((run/'review.json').read_text())
    assert review['passed'] and review['human_review_required']
    assert any(i['severity']=='warning' and 'Quotation-marked' in i['explanation'] for i in review['issues'])


def test_valid_direct_quote_preserved_and_failed_rerun_leaves_old_drafts(series):
    repo,run,env,items,decisions,briefs,command=series
    prepare(run,decisions,briefs)
    quote=briefs[0]['claims'][0]['evidence'][0]['locator']['quote']
    fixture_response(repo,'write_articles',lambda f:f['output']['documents'][0].update(markdown=f['output']['documents'][0]['markdown']+'\n"'+quote+'"'))
    good=command('content/write_articles.sh','runs/fictional-series',input=stream(briefs))
    assert good.returncode==0,good.stderr
    old=(run/'articles/01.md').read_bytes()
    fixture_response(repo,'write_articles',lambda f:f['output']['documents'][0].update(markdown='Broken output'))
    bad=command('content/write_articles.sh','runs/fictional-series',input=stream(briefs))
    assert bad.returncode==2 and (run/'articles/01.md').read_bytes()==old


def test_allowed_extra_claim_metadata_does_not_change_reference_contract(series):
    repo,run,env,items,decisions,briefs,command=series
    briefs[0]['claims'][0]['fixture_note']='Additional metadata permitted by the architecture'
    prepare(run,decisions,briefs)
    result=command('content/write_articles.sh','runs/fictional-series',input=stream(briefs))
    assert result.returncode==0,result.stderr
    assert len(result.stdout.splitlines())==3


def test_fixture_mode_cannot_be_used_as_live_evidence(series):
    repo,run,env,items,decisions,briefs,command=series
    meta=json.loads((run/'run.json').read_text());meta['mode']='live';(run/'run.json').write_text(json.dumps(meta))
    result=command('editorial/select_items.sh','runs/fictional-series',input=stream(items))
    assert result.returncode==2 and result.stdout==''
    assert receipt(run,'select_items')['model_calls']==[]


def test_workflow_stops_on_malformed_selection_and_archives_resume(series):
    repo,run,env,items,decisions,briefs,command=series
    first=command('workflows/create_series.sh','runs/fictional-series')
    assert first.returncode==0,first.stderr
    prior=set((run/'logs').glob('*.json'))
    fixture_response(repo,'select_items',lambda f:f.update(content='{bad'))
    second=command('workflows/create_series.sh','runs/fictional-series')
    assert second.returncode==2 and json.loads(second.stdout)['failed_stage']=='editorial/select_items.sh'
    assert not (run/'briefs.jsonl').exists() and not (run/'review.json').exists()
    assert list((run/'attempts').glob('*/articles/01.md'))
    assert prior <= set((run/'logs').glob('*.json'))


def test_review_fingerprint_changes_and_assessment_returns_zero(series):
    repo,run,env,items,decisions,briefs,command=series
    assert command('workflows/create_series.sh','runs/fictional-series').returncode==0
    old=json.loads((run/'review.json').read_text())['review_id']
    path=run/'articles/01.md';path.write_text(path.read_text().replace('01-c1','unsupported-marker'))
    checked=command('review/check_content.sh','runs/fictional-series')
    assert checked.returncode==0 and json.loads(checked.stdout)['passed'] is False
    assert json.loads(checked.stdout)['review_id']!=old


def test_workflow_refuses_insufficient_acceptances_without_drafts(series):
    repo,run,env,items,decisions,briefs,command=series
    def alter(f):
        f['output']['decisions'][2]['decision']='defer'
        f['output']['decisions'][2]['piece_ids']=[]
    fixture_response(repo,'select_items',alter)
    result=command('workflows/create_series.sh','runs/fictional-series')
    assert result.returncode==1 and json.loads(result.stdout)['failed_stage']=='editorial/create_briefs.sh'
    assert receipt(run,'create_briefs')['model_calls']==[]
    assert not (run/'articles').exists() and not (run/'video_scripts').exists()


@pytest.mark.parametrize('mode',['json_schema','json_object'])
def test_http_adapter_structured_output_usage_cost_and_secret_exclusion(series,monkeypatch,mode):
    repo,run,env,items,decisions,briefs,command=series
    monkeypatch.chdir(repo)
    for key,value in env.items():
        if key.startswith('MODEL_'): monkeypatch.setenv(key,value)
    monkeypatch.setenv('MODEL_PROVIDER','openai_compatible')
    monkeypatch.setenv('MODEL_BASE_URL','https://api.example.invalid/v1')
    monkeypatch.setenv('MODEL_API_KEY','FICTIONAL_HEADER_SECRET')
    monkeypatch.setenv('MODEL_RESPONSE_FORMAT',mode)
    monkeypatch.setenv('INVOCATION_ID','fixture-http-'+mode)
    captured={}
    def post(url,**kwargs):
        captured.update(kwargs)
        class Response:
            text=json.dumps({'model':'unit-http-model','choices':[{'finish_reason':'stop','message':{'content':json.dumps({'decisions':decisions})}}],
                             'usage':{'prompt_tokens':120,'completion_tokens':80}})
            def raise_for_status(self): pass
        return Response()
    monkeypatch.setattr('lib.model_provider.requests.post',post)
    metrics={'models':[],'model_calls':[]}
    result=ask('select_items',run,{'mode':'example'},'FICTIONAL POLICY','FICTIONAL PROMPT',{'input':'fixture'},RESPONSES['select_items'],metrics)
    assert result['decisions']==decisions
    assert captured['json']['response_format']['type']==mode
    assert captured['headers']['Authorization']=='Bearer FICTIONAL_HEADER_SECRET'
    assert metrics['cost_usd']==pytest.approx(0.00018) and metrics['cost_is_estimate']
    assert metrics['models'][0]['name']=='unit-http-model'
    assert metrics['model_calls'][0]['duration_seconds']>=0
    for folder in ('prompts/rendered','model_outputs'):
        for path in (run/folder).glob('*'):
            assert 'FICTIONAL_HEADER_SECRET' not in path.read_text()


def test_fixture_cost_unknown_rates_and_schema_failure_accounting(series,monkeypatch):
    repo,run,env,items,decisions,briefs,command=series
    monkeypatch.chdir(repo)
    for key in ('MODEL_PROVIDER','MODEL_FIXTURE_DIR','MODEL_NAME'):
        monkeypatch.setenv(key,env[key])
    monkeypatch.delenv('MODEL_INPUT_USD_PER_MILLION',raising=False)
    monkeypatch.delenv('MODEL_OUTPUT_USD_PER_MILLION',raising=False)
    monkeypatch.setenv('INVOCATION_ID','fixture-unknown-price')
    metrics={'models':[],'model_calls':[]}
    ask('select_items',run,{'mode':'example'},'TEST POLICY','TEST PROMPT',{},RESPONSES['select_items'],metrics)
    assert metrics['cost_usd']==0 and metrics['simulated_cost_usd'] is None
    assert metrics['model_calls'][0]['request_attempted'] is False
