"""Construct explicitly fictional evidence and canned model outputs for tests."""
import json
import os
import shutil
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from data.versioning import version_id


def build(location):
    repo = (location / 'repo').resolve()
    for folder in ('lib','data','editorial','content','workflows','review','publishing','reporting'):
        (repo/folder).mkdir(parents=True,exist_ok=True)
        # Explicit implementation files only; never copy/access an evidence index.
        for source in (ROOT/folder).glob('*'):
            if source.is_file() and source.suffix in ('.py','.sh'):
                shutil.copyfile(source,repo/folder/source.name)
    for name in ('run.sh','run_setup.py'):
        shutil.copyfile(ROOT/name,repo/name)
    run=repo/'runs/fictional-series'
    for folder in ('config','prompts'):
        (run/folder).mkdir(parents=True)
    (run/'run.json').write_text(json.dumps({'run_id':'fictional-series','mode':'example','as_of_date':'2026-10-14',
        'started_at':'2026-10-14T12:00:00Z','previous_run_id':None}))
    shutil.copyfile(ROOT/'tests/fixtures/orchestration/project.json',run/'config/project.json')
    shutil.copyfile(ROOT/'tests/fixtures/editorial/policy.md',run/'config/editorial_policy.md')
    for name in ('select_items','create_briefs','write_articles','write_video_scripts'):
        shutil.copyfile(ROOT/'tests/fixtures/editorial/prompt.md',run/'prompts'/f'{name}.md')
    assets=repo/'data/assets'
    assets.mkdir()
    shutil.copyfile(ROOT/'tests/fixtures/editorial/text.txt',assets/'FICTIONAL-text.txt')
    shutil.copyfile(ROOT/'tests/fixtures/editorial/segments.json',assets/'FICTIONAL-segments.json')
    items=[]
    for index in range(12):
        kind=('feed','youtube','podcast')[index%3]
        item={'item_id':f'fixture:{index:02}', 'source_id':f'fixture-source-{index%6}',
              'publisher_id':f'fictional-publisher-{index%6}', 'kind':kind,'title':f'FICTIONAL item {index}',
              'url':f'https://fictional.example/{index}', 'published_at':'2026-10-03T12:00:00Z',
              'retrieved_at':'2026-10-14T12:00:00Z','media_url':None,
              'text_path':'data/assets/FICTIONAL-text.txt',
              'segments_path':None if kind=='feed' else 'data/assets/FICTIONAL-segments.json','fixture':True}
        item['version_id']=version_id(item,repo)
        items.append(item)
    stream=''.join(json.dumps(item)+'\n' for item in items)
    (run/'eligible.jsonl').write_text(stream)
    (run/'items.jsonl').write_text(stream)
    (run/'config/sources.json').write_text(json.dumps([{'source_id':f'fixture-source-{i}','publisher_id':f'fictional-publisher-{i}',
        'kind':('feed','youtube','podcast')[i%3],'url':f'https://fictional.example/source/{i}'} for i in range(6)]))
    decisions=[{'item_id':item['item_id'],'version_id':item['version_id'],
                'decision':'accept' if i<3 else 'reject' if i<9 else 'defer',
                'reason':'FICTIONAL canned decision for contract testing',
                'piece_ids':['01','02','03'] if i<3 else []} for i,item in enumerate(items)]
    evidence=[{'item_id':item['item_id'],'version_id':item['version_id'],
               'locator':{'type':'text','quote':'FICTIONAL report: the imaginary lab omitted setup time.'} if item['kind']=='feed'
               else {'type':'segment','segment_id':'s-001'}} for item in items[:3]]
    briefs=[]
    for piece,title,argument in (
        ('01','FICTIONAL changes','FICTIONAL selected sources leave setup effort unresolved.'),
        ('02','FICTIONAL scrutiny','FICTIONAL examples cannot prove claims about real deployment.'),
        ('03','FICTIONAL implications','FICTIONAL fixtures show how a watchlist could be structured.')):
        briefs.append({'piece_id':piece,'title':title,'question':title+'?', 'argument':argument,
                       'synthesis':'FICTIONAL synthesis connects the invented lab omission with invented media discussion.',
                       'limitations':'All sources are fictional fixtures; this establishes no real-world conclusion.',
                       'claims':[{'claim_id':piece+'-c1','statement':argument,'type':'inference','evidence':evidence}]})
    model_dir=repo/'model-fixtures'
    model_dir.mkdir()
    transport_briefs = deepcopy(briefs)
    for brief, expected, kind, ref, suffix in zip(transport_briefs, briefs, ('feed','youtube','podcast'), evidence, ('91','92','93')):
        anchor = dict(deepcopy(brief['claims'][0]), claim_id=brief['piece_id']+'-c'+suffix, evidence=[deepcopy(ref)])
        brief[kind+'_claim'] = anchor
        expected['claims'].append(deepcopy(anchor))
    documents=[{'piece_id':b['piece_id'],'markdown':'# '+b['title']+'\n\n'+b['argument']+' '+
                ' '.join('['+c['claim_id']+']' for c in b['claims'])+'\n\nFICTIONAL example only.',
                'claim_ids':[c['claim_id'] for c in b['claims']],'claims':b['claims']} for b in briefs]
    for name,output in {'select_items':{'decisions':decisions},'create_briefs':{'briefs':transport_briefs},
                         'write_articles':{'documents':documents},'write_video_scripts':{'documents':documents}}.items():
        (model_dir/f'{name}.json').write_text(json.dumps({'fixture':True,'output':output,'usage':{'prompt_tokens':100,'completion_tokens':50}}))
    env=dict(os.environ,PATH=str(Path(sys.executable).parent)+os.pathsep+os.environ['PATH'],RUN_DIR='runs/fictional-series',
             MODEL_PROVIDER='fixture',MODEL_FIXTURE_DIR='model-fixtures',MODEL_NAME='FICTIONAL-model',
             MODEL_INPUT_USD_PER_MILLION='0.5',MODEL_OUTPUT_USD_PER_MILLION='1.5',PYTHONDONTWRITEBYTECODE='1')
    env.pop('PYTHONPATH',None)
    def command(script,*args,input=''):
        return subprocess.run(['/bin/bash',script,*args],cwd=repo,env=env,input=input,text=True,capture_output=True)
    assert command('data/store.sh','init').returncode==0
    assert command('data/store.sh','upsert','runs/fictional-series',input=stream).returncode==0
    return repo,run,env,items,decisions,briefs,command
