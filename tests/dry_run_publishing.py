"""Retained FICTIONAL smoke demonstration with SIMULATED approval only."""
import json
import tempfile
from pathlib import Path
from editorial_fixture import build
from test_publishing import approve

repo, run, env, items, decisions, briefs, command = build(Path(tempfile.mkdtemp(prefix='ps04-publication-fixture-')))
print('FICTIONAL evidence and SIMULATED approvals; no API calls or publication.')
result = command('workflows/create_series.sh','runs/fictional-series')
assert result.returncode == 0, result.stderr
for script in ('review/check_content.sh','reporting/summarize_run.sh'):
    result = command(script,'runs/fictional-series')
    assert result.returncode == 0, result.stderr
    value = json.loads(result.stdout)
    print('$ bash '+script+' runs/fictional-series')
    print(json.dumps({k:value[k] for k in ('review_id','passed','status','counts') if k in value}))
approve(run)
result = command('publishing/prepare_package.sh','runs/fictional-series')
print('$ bash publishing/prepare_package.sh runs/fictional-series')
assert result.returncode == 0, result.stderr
print('exit=0; package assets='+str(len(json.loads(result.stdout)['assets'])))
links = run/'package/publication_links.json'
data = json.loads(links.read_text()); data[0]['substack_url']='https://fictional.example/SIMULATED-link'
links.write_text(json.dumps(data)+'\n'); saved = links.read_bytes()
result = command('run.sh','--package','runs/fictional-series')
print('$ bash run.sh --package runs/fictional-series')
assert result.returncode == 0, result.stderr
print('exit=0; status='+json.loads(result.stdout)['status']+'; publication links preserved='+str(saved==links.read_bytes()))
draft = run/'articles/01.md'
draft.write_text(draft.read_text()+'\nFICTIONAL changed draft after approval.\n')
result = command('publishing/prepare_package.sh','runs/fictional-series')
print('$ [modify articles/01.md] then bash publishing/prepare_package.sh runs/fictional-series')
print('exit='+str(result.returncode)+'; '+result.stderr.strip())
assert result.returncode == 1 and 'Stale review' in result.stderr
result = command('run.sh','--package','runs/fictional-series')
print('$ bash run.sh --package runs/fictional-series (stale approval)')
print('exit='+str(result.returncode)+'; status='+json.loads(result.stdout)['status'])
print(result.stderr.strip())
assert result.returncode == 1 and 'Stale approval' in result.stderr
print('Retained FICTIONAL run: '+str(run))
for path in sorted((run/'package').rglob('*')):
    if path.is_file(): print(path.relative_to(run))
