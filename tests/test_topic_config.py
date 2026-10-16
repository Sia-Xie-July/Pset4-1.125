"""Real topic configuration structure; discovery tests use FICTIONAL data only."""
import json
from pathlib import Path
import pytest
from collectors.support import run_collector
from lib.records import safe_public_url, reject_credentials

ROOT = Path(__file__).resolve().parents[1]


def test_project_policy_prompts_and_source_entry_points_are_populated():
    project = json.loads((ROOT/'config/project.json').read_text())
    assert all(isinstance(project[k],str) and project[k].strip() for k in
               ('publication_name','topic','audience','central_question'))
    assert project['language']=='English'
    sources = json.loads((ROOT/'config/sources.json').read_text())
    assert {s['kind'] for s in sources}=={'feed','youtube','podcast'}
    assert len({s['source_id'] for s in sources})==len(sources)
    assert len({s['publisher_id'] for s in sources})>=6  # Declared groups, not verified independence.
    for source in sources:
        safe_public_url(source['url']);reject_credentials(source)
        assert type(source['max_entries']) is int and source['max_entries']>0
    for name in ('select_items','create_briefs','write_articles','write_video_scripts'):
        assert (ROOT/'prompts'/f'{name}.md').read_text().strip()
    assert (ROOT/'config/editorial_policy.md').read_text().strip()


def test_actual_topic_configuration_passes_snapshot_validation(tmp_path):
    from run_setup import configure
    run = tmp_path/'FICTIONAL-config-validation-only'
    run.mkdir()
    (run/'run.json').write_text(json.dumps({'run_id':'FICTIONAL-config-validation-only',
        'mode':'example','started_at':'2026-10-14T12:00:00Z','as_of_date':'2026-10-14',
        'previous_run_id':None}))
    configure(run,['--mode','example','--config-dir',str(ROOT/'config'),'--prompts-dir',str(ROOT/'prompts')])
    for path in (ROOT/'config').iterdir():
        assert path.read_bytes()==(run/'config'/path.name).read_bytes()
    for path in (ROOT/'prompts').glob('*.md'):
        assert path.read_bytes()==(run/'prompts'/path.name).read_bytes()


def setup_discovery(tmp_path,monkeypatch,sources):
    run = tmp_path/'FICTIONAL-run'
    (run/'config').mkdir(parents=True)
    (run/'config/sources.json').write_text(json.dumps(sources))
    metrics = tmp_path/'FICTIONAL-metrics.json'
    monkeypatch.setenv('RECEIPT_METRICS',str(metrics))
    monkeypatch.setenv('MAX_ITEMS','0')
    monkeypatch.setenv('MAX_DURATION_MINUTES','20')
    monkeypatch.setattr('sys.argv',['fetch_feeds.py',str(run)])
    return metrics


def test_per_source_bounds_leave_room_for_other_publishers(tmp_path,monkeypatch,capsys):
    sources = [{'source_id':str(i),'publisher_id':'FICTIONAL-'+str(i),'kind':'feed',
                'url':'https://fictional.example/feed/'+str(i),'max_entries':1} for i in range(2)]
    metrics = setup_discovery(tmp_path,monkeypatch,sources)
    def discover(source,args):
        for i in range(3):
            yield {'item_id':source['source_id']+':'+str(i),'kind':'feed','url':'https://fictional.example/'+str(i),
                   'source_id':source['source_id'],'media_url':None,'fixture':True}
    assert run_collector('feed',discover)==0
    rows = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert [r['item_id'] for r in rows]==['0:0','1:0']
    saved = json.loads(metrics.read_text())
    assert saved['limited'] and saved['output_count']==2
    assert all(s['discovery_limit']==1 for s in saved['sources'])


@pytest.mark.parametrize('limit',[0,-1,True,'two'])
def test_invalid_source_bound_is_config_error(tmp_path,monkeypatch,capsys,limit):
    metrics = setup_discovery(tmp_path,monkeypatch,[{'source_id':'FICTIONAL','publisher_id':'FICTIONAL',
        'kind':'feed','url':'https://fictional.example/feed','max_entries':limit}])
    assert run_collector('feed',lambda *a:iter(()))==2
    assert capsys.readouterr().out==''
    assert json.loads(metrics.read_text())['errors']


@pytest.mark.parametrize('ids', [[], [''], 'one', [1], ['same', 'same']])
def test_invalid_podcast_episode_ids_are_config_errors(tmp_path, monkeypatch, capsys, ids):
    metrics = setup_discovery(tmp_path, monkeypatch, [{'source_id':'FICTIONAL','publisher_id':'FICTIONAL',
        'kind':'podcast','url':'https://fictional.example/feed','episode_ids':ids}])
    assert run_collector('podcast', lambda *a: iter(())) == 2
    assert capsys.readouterr().out == ''
    assert json.loads(metrics.read_text())['errors']
