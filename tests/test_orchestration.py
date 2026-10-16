"""Collection-only entry/workflow integration tests with fictional inputs."""
import json
import shutil
from pathlib import Path

import pytest
from test_collection import harness

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def orchestration(harness):
    repo, run, env, state, command, configure, receipts = harness
    for folder, names in {'': ['run.sh', 'run_setup.py'],
                          'lib': ['candidate_stream.py'],
                          'review': ['fingerprint.py'],
                          'processing': ['filter_items.sh', 'filter_items.py'],
                          'workflows': ['collect_sources.sh'],
                          'reporting': ['summarize_run.sh', 'summarize_run.py']}.items():
        (repo/folder).mkdir(exist_ok=True)
        for name in names:
            shutil.copyfile(ROOT/folder/name, repo/folder/name)
    definitions = []
    for kind in ('feed','youtube','podcast'):
        configure(kind)
        definitions += json.loads((run/'config/sources.json').read_text())
    (run/'config/sources.json').write_text(json.dumps(definitions))
    for name in ('project.json','editorial_policy.md'):
        shutil.copyfile(ROOT/'tests/fixtures/orchestration'/name, run/'config'/name)
    prompts = repo/'fixture-prompts'
    prompts.mkdir()
    for name in ('select_items.md','create_briefs.md','write_articles.md','write_video_scripts.md'):
        shutil.copyfile(ROOT/'tests/fixtures/orchestration/prompt.md', prompts/name)
    return repo, run, env, state, command, configure, receipts


def invoke(command):
    return command('run.sh','--collection-only','--mode','example','--config-dir','runs/fictional/config','--prompts-dir','fixture-prompts')


def test_workflow_standalone_and_resume(orchestration):
    repo, run, env, state, command, configure, receipts = orchestration
    first = command('workflows/collect_sources.sh','runs/fictional')
    assert first.returncode == 0, first.stderr
    status = json.loads(first.stdout)
    assert set(status['collector_exit_codes'].values()) == {0}
    assert len((run/'candidates.jsonl').read_text().splitlines()) == 3
    for name in ('items','changes','corpus','eligible','exclusions'):
        assert (run/(name+'.jsonl')).is_file()
    first_receipts = set((run/'logs').glob('*.json'))
    resumed = command('workflows/collect_sources.sh','runs/fictional')
    assert resumed.returncode == 0, resumed.stderr
    assert all(json.loads(line)['change']=='unchanged' for line in (run/'changes.jsonl').read_text().splitlines())
    assert first_receipts <= set((run/'logs').glob('*.json'))
    assert list((run/'attempts').glob('*/items.jsonl'))


def test_run_metadata_snapshots_and_previous_run(orchestration):
    repo, original, env, state, command, configure, receipts = orchestration
    first = invoke(command)
    assert first.returncode == 0, first.stderr
    summary = json.loads(first.stdout)
    assert summary['collection_status']=='completed' and summary['counts']['new']==3
    assert summary['counts']['accepted'] is None and summary['pipeline_complete'] is False
    run = repo/summary['run_dir']
    metadata = json.loads((run/'run.json').read_text())
    assert metadata['mode']=='example' and metadata['started_at'].startswith(metadata['as_of_date'])
    for path in (original/'config').iterdir():
        assert path.read_bytes()==(run/'config'/path.name).read_bytes()
    for path in (repo/'fixture-prompts').iterdir():
        assert path.read_bytes()==(run/'prompts'/path.name).read_bytes()
    second = invoke(command)
    assert second.returncode == 0, second.stderr
    next_summary = json.loads(second.stdout)
    next_run = repo/next_summary['run_dir']
    assert next_run != run
    assert json.loads((next_run/'run.json').read_text())['previous_run_id']==metadata['run_id']
    assert next_summary['counts']['new']==0 and next_summary['counts']['unchanged']==3


def test_partial_collector_failure_is_preserved(orchestration):
    repo, original, env, state, command, configure, receipts = orchestration
    sources=json.loads((original/'config/sources.json').read_text())
    sources.append(dict(sources[0],source_id='fictional-failed',url=sources[0]['url'].replace('/feed.xml','/failed')))
    (original/'config/sources.json').write_text(json.dumps(sources))
    result=invoke(command)
    assert result.returncode==1, result.stderr
    summary=json.loads(result.stdout)
    assert summary['collector_exit_codes']['fetch_feeds']==1
    assert summary['collector_exit_codes']['fetch_youtube']==0
    assert summary['collector_exit_codes']['fetch_podcasts']==0
    assert summary['collection_status']=='incomplete' and summary['coverage_incomplete']
    assert summary['counts']['discovered']==3 and summary['counts']['new']==3
    assert summary['counts']['eligible']==3
    run=repo/summary['run_dir']
    assert (run/'eligible.jsonl').is_file()
    errors=[json.loads(p.read_text()) for p in (run/'logs').glob('fetch_feeds-*-failed.json')]
    assert errors and errors[0]['errors'] and errors[0]['output_count']==1


def test_invalid_config_still_receipted_and_summarized(orchestration):
    repo, original, env, state, command, configure, receipts = orchestration
    project=json.loads((original/'config/project.json').read_text())
    project['audience']=''
    (original/'config/project.json').write_text(json.dumps(project))
    result=invoke(command)
    assert result.returncode==2, result.stderr
    summary=json.loads(result.stdout)
    assert summary['collection_status']=='not_run' and summary['counts']['discovered'] is None
    run=repo/summary['run_dir']
    assert (run/'summary.json').is_file()
    assert list((run/'logs').glob('run-*-failed.json'))
    assert not list((run/'logs').glob('store.init-*.json'))


def test_pipe_failure_preserved_and_stale_outputs_archived(orchestration):
    repo, run, env, state, command, configure, receipts = orchestration
    assert command('workflows/collect_sources.sh','runs/fictional').returncode==0
    metadata=json.loads((run/'run.json').read_text())
    metadata['as_of_date']='invalid-date'
    (run/'run.json').write_text(json.dumps(metadata))
    result=command('workflows/collect_sources.sh','runs/fictional')
    assert result.returncode==2, result.stderr
    stages=json.loads(result.stdout)['stages']
    assert next(s['exit_code'] for s in stages if s['stage']=='filter_items')==2
    assert not (run/'exclusions.jsonl').exists()
    assert list((run/'attempts').glob('*/exclusions.jsonl'))
    reported=command('reporting/summarize_run.sh','runs/fictional')
    assert reported.returncode==0, reported.stderr
    summary=json.loads(reported.stdout)
    assert summary['collection_status']=='incomplete'
    assert summary['counts']['eligible'] is None and summary['counts']['excluded'] is None
