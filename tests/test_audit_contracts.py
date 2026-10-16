"""Audit regressions using explicitly fictional isolated repositories."""
import json
import shutil
from pathlib import Path
import pytest
from editorial_fixture import build, ROOT

COMPONENTS = ['run.sh','workflows/collect_sources.sh','workflows/create_series.sh',
              'collectors/fetch_feeds.sh','collectors/fetch_youtube.sh','collectors/fetch_podcasts.sh',
              'processing/extract_content.sh','processing/filter_items.sh','data/store.sh',
              'editorial/select_items.sh','editorial/create_briefs.sh','content/write_articles.sh',
              'content/write_video_scripts.sh','review/check_content.sh',
              'publishing/prepare_package.sh','reporting/summarize_run.sh']


def fixture_repo(tmp_path):
    values = build(tmp_path)
    repo = values[0]
    for folder in ('collectors','processing'):
        (repo/folder).mkdir(exist_ok=True)
        for path in (ROOT/folder).glob('*'):
            if path.suffix in ('.py','.sh'):
                shutil.copyfile(path,repo/folder/path.name)
    return values


@pytest.mark.parametrize('script',COMPONENTS)
def test_standalone_argument_failure_and_receipt(tmp_path, script):
    repo, run, env, items, decisions, briefs, command = fixture_repo(tmp_path)
    if script == 'run.sh': result = command(script,'--UNKNOWN-FICTIONAL-ARG')
    elif script == 'data/store.sh': result = command(script,'list','UNEXPECTED')
    else: result = command(script,'runs/fictional-series','--UNKNOWN-FICTIONAL-ARG')
    assert result.returncode == 2, result.stderr
    finals = [json.loads(path.read_text()) for path in (repo/'runs').glob('*/logs/*-failed.json')]
    assert any(row['exit_code']==2 and row['errors'] for row in finals)
    assert all(row['exit_code'] in (0,1,2) for row in finals)


def test_missing_retained_asset_is_operational(tmp_path):
    repo, run, env, items, decisions, briefs, command = fixture_repo(tmp_path)
    (repo/items[0]['text_path']).unlink()
    result = command('processing/extract_content.sh','runs/fictional-series')
    assert result.returncode == 1, result.stderr
    assert 'retained-asset' in result.stderr


def test_absolute_run_argument_produces_relative_record_path(tmp_path):
    repo, run, env, items, decisions, briefs, command = fixture_repo(tmp_path)
    result = command('reporting/summarize_run.sh',str(run))
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['run_dir'] == 'runs/fictional-series'


def test_credential_candidate_is_rejected_without_leaking(tmp_path):
    repo, run, env, items, decisions, briefs, command = fixture_repo(tmp_path)
    env['MODEL_API_KEY'] = 'FICTIONAL_ACTIVE_CANARY_ONLY'
    candidate = {k:v for k,v in items[0].items() if k not in ('version_id','text_path','segments_path')}
    candidate['url'] = 'https://fictional.example/page?api_key='+env['MODEL_API_KEY']
    result = command('processing/extract_content.sh','runs/fictional-series',input=json.dumps(candidate)+'\n')
    assert result.returncode == 2 and result.stdout == ''
    assert env['MODEL_API_KEY'] not in result.stderr
    for path in (run/'logs').glob('*.json'):
        assert env['MODEL_API_KEY'] not in path.read_text()


def test_credential_snapshot_is_rejected_before_persistence(tmp_path):
    repo, run, env, items, decisions, briefs, command = fixture_repo(tmp_path)
    env['MODEL_API_KEY'] = 'FICTIONAL_ACTIVE_CANARY_ONLY'
    project = json.loads((run/'config/project.json').read_text())
    project['topic'] = env['MODEL_API_KEY']
    (run/'config/project.json').write_text(json.dumps(project))
    result = command('run.sh','--mode','example','--config-dir','runs/fictional-series/config',
                     '--prompts-dir','runs/fictional-series/prompts')
    assert result.returncode == 2
    assert env['MODEL_API_KEY'] not in result.stderr+result.stdout
    created = repo/json.loads(result.stdout)['run_dir']
    assert not (created/'config/project.json').exists()


def test_feed_recording_route_is_not_counted_as_written_evidence(tmp_path):
    repo, run, env, items, decisions, briefs, command = fixture_repo(tmp_path)
    candidate = {k:v for k,v in items[0].items() if k not in ('version_id','text_path','segments_path')}
    candidate['url'] = 'https://www.youtube.com/watch?v=fixture1234'
    result = command('processing/extract_content.sh','runs/fictional-series',input=json.dumps(candidate)+'\n')
    assert result.returncode == 1 and result.stdout == ''
    assert 'RSS discovery route' in result.stderr


def test_nonstore_receipt_home_cannot_be_canonical_index(tmp_path):
    repo, run, env, items, decisions, briefs, command = fixture_repo(tmp_path)
    # Store init created the directory through its own interface. This test never
    # opens, lists, reads or writes any index file itself.
    result = command('review/check_content.sh','data/evidence')
    assert result.returncode == 2 and result.stdout == ''
    assert 'outside the evidence index' in result.stderr


def test_model_response_metadata_cannot_persist_active_credential(tmp_path, monkeypatch):
    from lib.model_provider import ask
    from lib.schemas import RESPONSES
    from types import SimpleNamespace
    repo, run, env, items, decisions, briefs, command = fixture_repo(tmp_path)
    monkeypatch.chdir(repo)
    for key,value in env.items():
        if key.startswith('MODEL_'): monkeypatch.setenv(key,value)
    monkeypatch.setenv('MODEL_PROVIDER','openai_compatible')
    monkeypatch.setenv('MODEL_BASE_URL','https://fictional.example/v1')
    monkeypatch.setenv('MODEL_API_KEY','FICTIONAL_ACTIVE_CANARY_ONLY')
    monkeypatch.setenv('INVOCATION_ID','FICTIONAL-canary-response')
    envelope = {'model':'FICTIONAL_ACTIVE_CANARY_ONLY', 'choices':[]}
    monkeypatch.setattr('lib.model_provider.requests.post',lambda *a,**k:SimpleNamespace(
        text=json.dumps(envelope),raise_for_status=lambda:None))
    metrics = {'models':[],'model_calls':[]}
    with pytest.raises(ValueError):
        ask('select_items',run,{'mode':'example'},'FICTIONAL policy','FICTIONAL prompt',
            {'fixture':True},RESPONSES['select_items'],metrics)
    assert 'FICTIONAL_ACTIVE_CANARY_ONLY' not in json.dumps(metrics)
    for folder in ('model_outputs','prompts/rendered'):
        for path in (run/folder).glob('*'):
            assert 'FICTIONAL_ACTIVE_CANARY_ONLY' not in path.read_text()


def test_publication_link_cannot_contain_credential(monkeypatch):
    from publishing.prepare_package import publication_links
    monkeypatch.setenv('MODEL_API_KEY','FICTIONAL_ACTIVE_CANARY_ONLY')
    value = [{'piece_id':p,'substack_url':None,'youtube_url':None} for p in ('01','02','03')]
    value[0]['substack_url']='https://fictional.example/p?token=FICTIONAL_ACTIVE_CANARY_ONLY'
    with pytest.raises(ValueError): publication_links(value)
