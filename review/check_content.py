"""Mechanical review needed by create_series; human reasoning review stays open."""
import hashlib
import re
import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lib.evidence import accepted_by_piece, eligible
from lib.records import asset_path, canonical, load_json
from lib.schemas import MANIFEST, validate
from lib.stage_runtime import InvalidInput, OperationalFailure, records, run_directory, run_stage
from content.validation import validate_documents
from review.fingerprint import fingerprint as review_fingerprint


def assess(run, metrics):
    issues=[]
    fingerprint={}
    def issue(severity,artifact,message,piece=None):
        issues.append({'piece_id':piece,'artifact':artifact,'severity':severity,'explanation':message})
    def read(name,jsonl=False):
        path=run/name
        try:
            raw=path.read_bytes()
            fingerprint[name]=hashlib.sha256(raw).hexdigest()
            return [load_json(line) for line in raw.decode().splitlines()] if jsonl else load_json(raw.decode())
        except (OSError,ValueError,UnicodeError):
            fingerprint.setdefault(name,None)
            issue('error',(run/name).relative_to(Path.cwd()).as_posix(),'Required artifact is missing or malformed')
            return None
    metadata=read('run.json')
    briefs=read('briefs.jsonl',True)
    decisions=read('decisions.jsonl',True)
    evidence_rows=read('eligible.jsonl',True)
    for item in evidence_rows or []:
        if not isinstance(item,dict): continue
        for field in ('text_path','segments_path'):
            path=item.get(field)
            if isinstance(path,str):
                try:
                    fingerprint['asset:'+path]=hashlib.sha256(asset_path(Path.cwd(),path).read_bytes()).hexdigest()
                except (OSError,ValueError):
                    fingerprint['asset:'+path]=None
    manifests={folder:read(name,True) for folder,name in [('articles','articles.jsonl'),('video_scripts','video_scripts.jsonl')]}
    try:
        if metadata is None or briefs is None or decisions is None:
            raise InvalidInput('Run metadata, decisions and three briefs are required')
        evidence=eligible(run,metadata)
        accepted=accepted_by_piece(evidence,decisions)
        evidence.briefs(briefs,accepted)
        kinds=Counter(item['kind'] for item in evidence.items.values())
        publishers={item['publisher_id'] for item in evidence.items.values()}
        if len(evidence.items)<12 or len(publishers)<6 or any(kinds[k]<2 for k in ('feed','youtube','podcast')):
            issue('error','eligible.jsonl','Collection coverage needs 12 distinct items, six independent publishers, and two items per required kind')
        for key,item in evidence.items.items():
            fingerprint['evidence:'+canonical(key)]={'version_id':item['version_id'],
                'text':hashlib.sha256((evidence.text[key] or '').encode()).hexdigest(),
                'segments':hashlib.sha256(canonical(evidence.segments[key]).encode()).hexdigest()}
        for folder,rows in manifests.items():
            if rows is None or len(rows)!=3 or {row.get('piece_id') for row in rows if isinstance(row,dict)}!={'01','02','03'}:
                issue('error',folder,'Exactly three content manifests are required'); continue
            assessed_documents=[]
            for row in rows:
                validate(MANIFEST,row)
                piece=row['piece_id']
                brief=next(b for b in briefs if b['piece_id']==piece)
                ids={claim['claim_id'] for claim in brief['claims']}
                expected=(run/folder/(piece+'.md')).relative_to(Path.cwd()).as_posix()
                if row['path']!=expected or set(row['claim_ids'])!=ids or len(row['claim_ids'])!=len(ids):
                    issue('error',folder,'Manifest path or claims differ from the brief',piece); continue
                try:
                    body=asset_path(Path.cwd(),row['path']).read_text(encoding='utf-8')
                    fingerprint[row['path']]=hashlib.sha256(body.encode()).hexdigest()
                except OSError:
                    issue('error',row['path'],'Draft/script file is missing',piece); continue
                markers=set(re.findall(r'\b(?:01|02|03)-c[1-9]\d*\b',body))
                if markers!=ids:
                    issue('error',row['path'],'Claim markers differ from the brief',piece)
                if metadata['as_of_date'] not in body:
                    issue('error',row['path'],'As-of date is absent',piece)
                if '## Sources' not in body:
                    issue('error',row['path'],'Source notes are absent',piece)
                elif evidence.source_notes(brief).strip() not in body:
                    issue('error',row['path'],'Source notes differ from the verified exact-version passages and locators',piece)
                for claim in brief['claims']:
                    for ref in claim['evidence']:
                        if ref['version_id'] not in body or evidence.items[ref['item_id'],ref['version_id']]['url'] not in body:
                            issue('error',row['path'],'Exact source version/link is absent from source notes',piece)
                words=len(body.split('## Sources')[0].split())
                if folder=='articles' and not 600<=words<=900:
                    issue('warning',row['path'],f'Approximate article length is {words} words; target 600–900 excluding references',piece)
                if folder=='video_scripts' and not 390<=words<=750:
                    issue('warning',row['path'],'Script length may fall outside 3–5 minutes; verify actual narration duration',piece)
                assessed_documents.append({'piece_id':piece,'markdown':body.split('## Sources')[0],
                    'claim_ids':row['claim_ids'],'claims':brief['claims']})
            if len(assessed_documents)==3:
                for warning in validate_documents(assessed_documents,briefs,evidence,accepted):
                    issue('warning',folder,warning['explanation'],warning['piece_id'])
    except (InvalidInput,ValueError,KeyError,TypeError,AttributeError,OperationalFailure,OSError):
        issue('error','briefs/evidence','Briefs, selection, or exact evidence references could not be validated')
    metrics['input_count']=len(fingerprint)
    fingerprint['as_of_date']=metadata.get('as_of_date') if isinstance(metadata,dict) else None
    issue('warning','series','Human review must judge claim entailment, original synthesis, credibility, counterarguments, and article/script meaning consistency')
    if isinstance(metadata,dict) and metadata.get('mode') in ('example','replay'):
        issue('warning','series','Example/replay material is not collected publication evidence')
    result={'review_id':review_fingerprint(run),
                     'passed':not any(i['severity']=='error' for i in issues),'issues':issues,
                     'checks_scope':'mechanical','human_review_required':True}
    metrics['output_count']=1
    return result


def main(metrics):
    print(canonical(assess(run_directory(), metrics)))


if __name__=='__main__':
    sys.exit(run_stage(main))
