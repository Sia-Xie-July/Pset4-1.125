"""Retained FICTIONAL standalone editorial/content and workflow demonstration."""
import argparse
import json
import tempfile
from pathlib import Path
from editorial_fixture import build


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--stage',choices=('select_items','create_briefs','write_articles','write_video_scripts','workflow'),default='workflow')
    args=parser.parse_args()
    repo,run,env,items,decisions,briefs,command=build(Path(tempfile.mkdtemp(prefix='ps04-editorial-fixture-')))
    print('FICTIONAL fixtures only; no model API calls.',flush=True)
    stages=[('editorial/select_items.sh','eligible.jsonl','decisions.jsonl'),
            ('editorial/create_briefs.sh','decisions.jsonl','briefs.jsonl'),
            ('content/write_articles.sh','briefs.jsonl','articles.jsonl'),
            ('content/write_video_scripts.sh','briefs.jsonl','video_scripts.jsonl')]
    if args.stage=='workflow':
        print('$ bash workflows/create_series.sh runs/fictional-series',flush=True)
        result=command('workflows/create_series.sh','runs/fictional-series')
        print('exit='+str(result.returncode)); print(result.stdout or result.stderr)
        if result.returncode: return result.returncode
    else:
        for script,source,target in stages:
            print('$ bash '+script+' runs/fictional-series < '+source,flush=True)
            result=command(script,'runs/fictional-series',input=(run/source).read_text())
            print('exit='+str(result.returncode))
            if result.returncode:
                print(result.stderr); return result.returncode
            (run/target).write_text(result.stdout)
            print('records='+str(len(result.stdout.splitlines())))
            print('sample='+result.stdout.splitlines()[0])
            if Path(script).stem==args.stage: break
    print('Retained fixture run: '+str(run))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
