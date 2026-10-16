"""Live transport smoke test, isolated from publication evidence and user config.

The short YouTube upload is historical: this test does not satisfy freshness or
assignment live-run requirements. No fake adapters are used here.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    destination = Path(tempfile.mkdtemp(prefix='ps04-live-smoke-'))
    for folder, names in {
        'lib':['common.sh','records.py'], 'data':['store.sh','versioning.py'],
        'collectors':['support.py','fetch_feeds.sh','fetch_feeds.py','fetch_podcasts.sh','fetch_podcasts.py','fetch_youtube.sh','fetch_youtube.py'],
        'processing':['extract_content.sh','extract_content.py','media.py','transcripts.py'],
    }.items():
        (destination/folder).mkdir(parents=True)
        for name in names:
            shutil.copyfile(ROOT/folder/name,destination/folder/name)
    run = destination/'runs/live-smoke'
    (run/'config').mkdir(parents=True)
    now = datetime.now(timezone.utc)
    (run/'run.json').write_text(json.dumps({'run_id':'live-smoke','mode':'example',
        'purpose':'REAL TRANSPORT SMOKE TEST ONLY; NOT PUBLICATION EVIDENCE',
        'started_at':now.isoformat().replace('+00:00','Z'),'as_of_date':now.date().isoformat(),'previous_run_id':None}))
    (run/'config/sources.json').write_text(json.dumps([
        {'source_id':'smoke-youtube','publisher_id':'jawed','kind':'youtube','url':'https://www.youtube.com/watch?v=jNQXAC9IVRw'},
        {'source_id':'smoke-podcast','publisher_id':'npr','kind':'podcast','url':'https://feeds.npr.org/500005/podcast.xml'},
    ],indent=2))
    env = dict(os.environ, PATH=str(Path(sys.executable).parent)+os.pathsep+os.environ['PATH'],
               RUN_DIR='runs/live-smoke', WHISPER_MODEL='base', WHISPER_DEVICE='cpu', WHISPER_COMPUTE_TYPE='int8',
               HF_HOME=os.getenv('HF_HOME',str(destination/'.model-cache')), PYTHONDONTWRITEBYTECODE='1')
    env.pop('PYTHONPATH',None)
    records = []
    def execute(args, input='', output=None):
        print('$ '+' '.join(args),flush=True)
        result = subprocess.run(args,cwd=destination,env=env,input=input,text=True,capture_output=True)
        if output:
            (run/output).write_text(result.stdout)
        records.append({'command':args,'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
        print('exit='+str(result.returncode),flush=True)
        for line in result.stdout.splitlines():
            try:
                item=json.loads(line)
                print(json.dumps({k:item[k] for k in ('item_id','kind','title','duration_seconds','transcript_method','transcript_model','version_id','change','extraction_reused') if k in item},ensure_ascii=False),flush=True)
            except ValueError:
                print(line,flush=True)
        if result.stderr:
            print(result.stderr.strip(),flush=True)
        (run/'smoke_results.json').write_text(json.dumps(records,indent=2))
        return result
    execute(['/bin/bash','data/store.sh','init'])
    failed=False
    for kind in ('youtube','podcasts'):
        collector='collectors/fetch_'+kind+'.sh'
        discovered=execute(['/bin/bash',collector,'runs/live-smoke','--max-items','1','--max-duration-minutes','6'],output=kind+'-candidates.jsonl')
        if not discovered.stdout:
            failed=True
        else:
            extracted=execute(['/bin/bash','processing/extract_content.sh','runs/live-smoke','--max-items','1','--max-duration-minutes','6'],input=discovered.stdout,output=kind+'-items.jsonl')
            failed=failed or extracted.returncode!=0
            if extracted.stdout:
                execute(['/bin/bash','data/store.sh','upsert','runs/live-smoke'],input=extracted.stdout,output=kind+'-changes.jsonl')
        piped=execute(['/bin/bash','-c',
            'set -o pipefail; bash "$1" "$2" --max-items 1 --max-duration-minutes 6 | bash processing/extract_content.sh "$2" --max-items 1 --max-duration-minutes 6',
            'smoke',collector,'runs/live-smoke'],output=kind+'-piped-items.jsonl')
        failed=failed or discovered.returncode!=0 or piped.returncode!=0
    print('Retained smoke test: '+str(destination),flush=True)
    return 1 if failed else 0


if __name__=='__main__':
    sys.exit(main())
