"""FICTIONAL review approvals for offline contract tests, never human publication approval."""
import json
import pytest
from editorial_fixture import build


@pytest.fixture
def completed(tmp_path):
    values = build(tmp_path)
    repo, run, env, items, decisions, briefs, command = values
    result = command('workflows/create_series.sh', 'runs/fictional-series')
    assert result.returncode == 0, result.stderr
    return values


def approve(run):
    review = json.loads((run/'review.json').read_text())
    assert review['passed']
    (run/'approval.json').write_text(json.dumps({'review_id':review['review_id'], 'decision':'approve',
        'reviewer':'FICTIONAL TEST REVIEWER', 'reviewed_at':'2026-10-14T13:00:00Z',
        'notes':'SIMULATED approval solely for offline tests; not a student decision.'}))


def test_package_standalone_and_preserved_links(completed):
    repo, run, env, items, decisions, briefs, command = completed
    approve(run)
    result = command('publishing/prepare_package.sh', 'runs/fictional-series')
    assert result.returncode == 0, result.stderr
    manifest = json.loads(result.stdout)
    assert len(manifest['assets']) == 9
    assert {a['piece_id'] for a in manifest['assets']} == {'01','02','03'}
    assert manifest['videos_rendered'] is False
    for asset in manifest['assets']:
        assert (repo/asset['path']).is_file()
    links = run/'package/publication_links.json'
    data = json.loads(links.read_text())
    assert all(row['substack_url'] is None and row['youtube_url'] is None for row in data)
    data[0]['substack_url'] = 'https://fictional.example/SIMULATED-publication'
    links.write_text(json.dumps(data, indent=2)+'\n')
    before = links.read_bytes()
    assert command('publishing/prepare_package.sh', 'runs/fictional-series').returncode == 0
    assert links.read_bytes() == before
    summary = command('reporting/summarize_run.sh','runs/fictional-series')
    assert summary.returncode == 0, summary.stderr
    report = json.loads(summary.stdout)
    assert report['status'] == 'ready_for_production'
    assert report['publication_links'] == data
    assert report['publication_verified'] is False


def test_modified_draft_rejects_stale_approval_direct_and_entry(completed):
    repo, run, env, items, decisions, briefs, command = completed
    approve(run)
    old = json.loads((run/'review.json').read_text())['review_id']
    draft = run/'articles/01.md'
    draft.write_text(draft.read_text()+'\nFICTIONAL revised editorial wording.\n')
    direct = command('publishing/prepare_package.sh','runs/fictional-series')
    assert direct.returncode == 1 and 'Stale review' in direct.stderr
    assert not (run/'package').exists()
    protected = {str(p):p.read_bytes() for folder in ('config','prompts','articles','video_scripts')
                 for p in (run/folder).rglob('*') if p.is_file()}
    entry = command('run.sh','--package','runs/fictional-series')
    assert entry.returncode == 1 and 'Stale approval' in entry.stderr
    assert json.loads(entry.stdout)['status'] == 'failed'
    assert json.loads((run/'review.json').read_text())['review_id'] != old
    assert all(open(path,'rb').read()==content for path,content in protected.items())
    assert not list((run/'logs').glob('fetch_*.json'))
    approve(run)
    recovered = command('run.sh','--package','runs/fictional-series')
    assert recovered.returncode == 0, recovered.stderr
    assert json.loads(recovered.stdout)['status'] == 'ready_for_production'


def test_summary_awaiting_and_counts(completed):
    repo, run, env, items, decisions, briefs, command = completed
    result = command('reporting/summarize_run.sh','runs/fictional-series')
    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary['status'] == 'awaiting_review'
    assert summary['counts']['discovered'] is None
    assert summary['counts']['accepted'] == 3
    assert summary['counts']['rejected'] == 6
    assert summary['counts']['deferred'] == 3
    assert summary['counts']['articles'] == summary['counts']['video_scripts'] == 3
    assert summary['cost_usd'] == 0 and summary['unknown_cost_stages']
    (run/'candidates.jsonl').write_text('')
    result = command('reporting/summarize_run.sh','runs/fictional-series')
    assert json.loads(result.stdout)['counts']['discovered'] == 0


@pytest.mark.parametrize('change', ['missing','revise','invalid_timestamp'])
def test_reject_missing_or_nonapproving_decision(completed, change):
    repo, run, env, items, decisions, briefs, command = completed
    if change != 'missing':
        approve(run)
        path = run/'approval.json'
        value = json.loads(path.read_text())
        if change == 'revise': value['decision'] = 'revise'
        else: value['reviewed_at'] = 'unknown'
        path.write_text(json.dumps(value))
    result = command('publishing/prepare_package.sh','runs/fictional-series')
    assert result.returncode == 1, result.stderr
    assert not (run/'package').exists()


def test_invalid_publication_links_preserve_package(completed):
    repo, run, env, items, decisions, briefs, command = completed
    approve(run)
    assert command('publishing/prepare_package.sh','runs/fictional-series').returncode == 0
    path = run/'package/publication_links.json'
    path.write_text('[]')
    before = (run/'package/manifest.json').read_bytes()
    result = command('publishing/prepare_package.sh','runs/fictional-series')
    assert result.returncode == 2
    assert path.read_text() == '[]' and (run/'package/manifest.json').read_bytes() == before


def test_incomplete_summary_and_reconciled_duplicates(completed):
    repo, run, env, items, decisions, briefs, command = completed
    (run/'collection_status.json').write_text(json.dumps({'exit_code':1,'stages':[
        {'stage':'fetch_podcasts','exit_code':1}], 'collector_exit_codes':{'fetch_podcasts':1}}))
    (run/'candidates.jsonl').write_text(json.dumps({'item_id':'fixture:00'})+'\n'+json.dumps({'item_id':'fixture:copy'})+'\n')
    items[0]['aliases'] = [{'item_id':'fixture:copy','basis':'FICTIONAL test same recording'}]
    (run/'items.jsonl').write_text(''.join(json.dumps(i)+'\n' for i in items))
    report = command('reporting/summarize_run.sh','runs/fictional-series')
    assert report.returncode == 0, report.stderr
    value = json.loads(report.stdout)
    assert value['status'] == 'failed' and value['coverage_incomplete']
    assert value['counts']['discovered'] == 2 and value['duplicate_observations'] == 1
    assert value['source_coverage']['distinct_items'] == 12
    assert value['failed_or_incomplete_stages'][0]['stage'] == 'fetch_podcasts'


@pytest.mark.parametrize('artifact', ['briefs.jsonl','video_scripts/02.md','data_asset','date'])
def test_fingerprint_changes_for_all_review_inputs(completed, artifact):
    repo, run, env, items, decisions, briefs, command = completed
    old = json.loads((run/'review.json').read_text())['review_id']
    if artifact == 'data_asset': path = repo/'data/assets/FICTIONAL-text.txt'
    elif artifact == 'date':
        path = run/'run.json'
        value = json.loads(path.read_text()); value['as_of_date'] = '2026-10-15'
        path.write_text(json.dumps(value))
    else: path = run/artifact
    if artifact != 'date': path.write_text(path.read_text()+'\nFICTIONAL changed bytes\n')
    result = command('review/check_content.sh','runs/fictional-series')
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['review_id'] != old


def test_incomplete_malformed_and_unmeasured_summary(tmp_path):
    repo, run, env, items, decisions, briefs, command = build(tmp_path)
    (run/'decisions.jsonl').write_text('')
    (run/'logs/FICTIONAL-failed-selection.json').write_text(json.dumps({
        'invocation_id':'FICTIONAL-invocation','stage':'select_items','status':'failed','exit_code':2,
        'cost_usd':None,'errors':['FICTIONAL simulated failure']}))
    (run/'briefs.jsonl').write_text('MALFORMED FICTIONAL TEST INPUT\n')
    result = command('reporting/summarize_run.sh','runs/fictional-series')
    assert result.returncode == 0, result.stderr
    value = json.loads(result.stdout)
    assert value['status'] == 'failed'
    assert value['counts']['accepted'] is None
    assert value['counts']['articles'] is None
    assert value['cost_usd'] is None
    assert value['failed_or_incomplete_stages']


def test_fresh_passing_review_resolves_prior_review_failure(completed):
    repo, run, env, items, decisions, briefs, command = completed
    (run/'series_status.json').write_text(json.dumps({'exit_code':1,'status':'failed','failed_stage':'review/check_content'}))
    approve(run)
    result = command('run.sh','--package','runs/fictional-series')
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['status'] == 'ready_for_production'


def test_normal_entry_calls_collection_and_real_series(tmp_path):
    repo, run, env, items, decisions, briefs, command = build(tmp_path)
    # FICTIONAL collection handoff stub isolates entry-point coordination. The
    # real collectors/pipes have separate offline HTTP integration tests.
    (repo/'workflows/collect_sources.sh').write_text('''#!/usr/bin/env bash
set -euo pipefail
source lib/common.sh
common_init collect_sources "$1"
cp runs/fictional-series/eligible.jsonl "$1/eligible.jsonl"
cp runs/fictional-series/items.jsonl "$1/items.jsonl"
cp runs/fictional-series/items.jsonl "$1/candidates.jsonl"
printf '%s\\n' '{"exit_code":0,"status":"completed","stages":[],"fixture":true}' > "$1/collection_status.json"
''')
    result = command('run.sh','--mode','example','--config-dir','runs/fictional-series/config',
                     '--prompts-dir','runs/fictional-series/prompts')
    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary['status'] == 'awaiting_review'
    assert summary['counts']['articles'] == summary['counts']['video_scripts'] == 3
    new_run = repo/summary['run_dir']
    assert new_run != run
    assert (new_run/'series_status.json').is_file()
    assert not (new_run/'approval.json').exists()


def test_review_rejects_altered_source_note_passage(completed):
    repo, run, env, items, decisions, briefs, command = completed
    path = run/'articles/01.md'
    path.write_text(path.read_text().replace('FICTIONAL report: the imaginary lab omitted setup time.',
                                           'FICTIONAL invented replacement quotation.'))
    result = command('review/check_content.sh','runs/fictional-series')
    assert result.returncode == 0, result.stderr
    review = json.loads(result.stdout)
    assert not review['passed']
    assert any('Source notes differ' in i['explanation'] for i in review['issues'])
