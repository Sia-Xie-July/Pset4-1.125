"""Retained FICTIONAL dry run through the actual collection-only entry point.

Offline HTTP/yt-dlp fixtures only. No project editorial settings/index are changed.
"""
import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_collection import harness
from test_orchestration import orchestration


def tree(directory, prefix=""):
    entries = sorted(directory.iterdir(), key=lambda p: (not p.is_dir(), p.name))
    for index, path in enumerate(entries):
        last = index == len(entries)-1
        branch = "└── " if last else "├── "
        if path.name == "logs":
            print(prefix+branch+f"logs/ ({len(list(path.glob('*.json')))} unique receipt files)")
        else:
            print(prefix+branch+path.name+("/" if path.is_dir() else ""))
            if path.is_dir():
                tree(path, prefix+("    " if last else "│   "))


def main():
    parser=argparse.ArgumentParser(description="FICTIONAL collection dry run")
    parser.add_argument('--simulate-failure',action='store_true')
    args=parser.parse_args()
    location=Path(tempfile.mkdtemp(prefix='ps04-collection-dry-run-'))
    fixture=harness.__wrapped__(location)
    try:
        context=orchestration.__wrapped__(next(fixture))
        repo, original, env, state, command, configure, receipts=context
        if args.simulate_failure:
            source_path=original/'config/sources.json'
            sources=json.loads(source_path.read_text())
            sources.append(dict(sources[0],source_id='FICTIONAL-simulated-failure',url=sources[0]['url'].replace('/feed.xml','/failed')))
            source_path.write_text(json.dumps(sources))
        print('FICTIONAL fixtures only — not collected publication evidence',flush=True)
        print('$ bash run.sh --collection-only --mode example --config-dir runs/fictional/config --prompts-dir fixture-prompts',flush=True)
        result=command('run.sh','--collection-only','--mode','example','--config-dir','runs/fictional/config','--prompts-dir','fixture-prompts')
        print('exit='+str(result.returncode))
        if result.stderr:
            print(result.stderr.strip())
        summary=json.loads(result.stdout)
        print(json.dumps({key:summary[key] for key in ('run_id','mode','collection_status','collector_exit_codes','counts','coverage_incomplete','pipeline_complete')},indent=2))
        run=repo/summary['run_dir']
        print('\nRetained run: '+str(run))
        print(summary['run_dir']+'/')
        tree(run)
        expected=1 if args.simulate_failure else 0
        assert result.returncode==expected, result.stderr
        assert summary['counts']['new']==3 and summary['counts']['eligible']==3
        return 0
    finally:
        fixture.close()  # stops the localhost server; artifacts/index remain


if __name__=='__main__':
    raise SystemExit(main())
