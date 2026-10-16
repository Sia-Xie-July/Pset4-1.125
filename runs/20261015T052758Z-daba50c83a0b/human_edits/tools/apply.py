import json, os, re, sys, copy
WORK = os.path.expanduser('~/work'); REPO = os.path.expanduser('~/mnt/ps04')
sys.path.insert(0, WORK); os.chdir(REPO); sys.path.insert(0, REPO)
from fixes import BRIEFS, EVIDENCE_REMAP_03   # ~/work/content.py
from lib.evidence import Evidence, accepted_by_piece
from lib.records import canonical
R = 'runs/20261015T052758Z-daba50c83a0b'
OUT = os.path.join(WORK, 'out'); os.makedirs(OUT + '/articles', exist_ok=True); os.makedirs(OUT + '/video_scripts', exist_ok=True)

# Stub evidence built from eligible.jsonl + retained assets (same data store.sh returns).
items = [json.loads(l) for l in open(R + '/human_edits/original/../../eligible.jsonl')]
ev = Evidence.__new__(Evidence); ev.items = {}; ev.text = {}; ev.segments = {}
for it in items:
    k = (it['item_id'], it['version_id']); ev.items[k] = it
    ev.text[k] = open(it['text_path'], encoding='utf-8').read() if it.get('text_path') else None
    ev.segments[k] = json.load(open(it['segments_path'])) if it.get('segments_path') else []
decisions = [json.loads(l) for l in open(R + '/decisions.jsonl')]
accepted = accepted_by_piece(ev, decisions)

orig = {b['piece_id']: b for b in map(json.loads, open(R + '/human_edits/original/briefs.jsonl'))}
new_briefs = []
for pid in ('01', '02', '03'):
    b = copy.deepcopy(orig[pid]); spec = BRIEFS[pid]
    for f in ('question', 'argument', 'synthesis', 'limitations'):
        b[f] = spec[f]
    if pid == '03':
        by_host = {}
        for c in orig['03']['claims'][:3]:
            for e in c['evidence']:
                host = re.match(r'feed:https://([^/]+)', e['item_id']).group(1)
                by_host[host] = c['evidence']
        for c in b['claims']:
            if c['claim_id'] in EVIDENCE_REMAP_03:
                c['evidence'] = copy.deepcopy(by_host[EVIDENCE_REMAP_03[c['claim_id']]])
    for c in b['claims']:
        c['type'], c['statement'] = spec['claims'][c['claim_id']]
    new_briefs.append(b)
ev.briefs(new_briefs, accepted)   # raises if any reference/publisher/kind rule fails
with open(OUT + '/briefs.jsonl', 'w') as fh:
    for b in new_briefs:
        fh.write(canonical(b) + '\n')

# Scripts: narration = rendered Google Vids text (production/NN.txt) + inspection markers.
MARK = {'01': {2: '01-c1', 4: '01-c2', 5: '01-c3', 6: '01-c4'},
        '02': {2: '02-c1', 3: '02-c2', 5: '02-c3', 6: '02-c4'},
        '03': {2: '03-c1', 3: '03-c2', 4: '03-c3', 5: '03-c4'}}
for b in new_briefs:
    pid = b['piece_id']; notes = ev.source_notes(b)
    art = open(os.path.join(WORK, 'art', pid + '.md'), encoding='utf-8').read().rstrip('\n')
    open(f'{OUT}/articles/{pid}.md', 'w', encoding='utf-8').write(art + '\n\n' + notes)
    paras = [p.strip() for p in open(f'{R}/production/{pid}.txt', encoding='utf-8').read().split('\n\n') if p.strip()]
    lines = [f"# {b['title']}", '',
             f'Production note: narration below is the text of the rendered Google Vids review draft (`production/{pid}.txt`, AI voice). Claim markers are for inspection and are not spoken.', '']
    for i, p in enumerate(paras):
        m = MARK[pid].get(i)
        if i == 0:
            visual = 'Title card, as-of date, AI-voice disclosure.'
        elif m:
            visual = 'Source card: publisher, date, timestamp.'
        else:
            visual = 'One-line text card.'
        lines += [f'Visual: {visual}', '', f'Narration: {p}' + (f' [{m}]' if m else ''), '']
    lines += ['As of: 2026-10-15 (UTC).', '']
    open(f'{OUT}/video_scripts/{pid}.md', 'w', encoding='utf-8').write('\n'.join(lines) + '\n' + notes)
print('built', OUT)

# ---- local mechanical check mirroring review/check_content.py (stub evidence) ----
from content.validation import validate_documents
problems = []; docs = {'articles': [], 'video_scripts': []}
for folder in docs:
    for b in new_briefs:
        pid = b['piece_id']; body = open(f'{OUT}/{folder}/{pid}.md', encoding='utf-8').read()
        ids = {c['claim_id'] for c in b['claims']}
        if set(re.findall(r'\b(?:01|02|03)-c[1-9]\d*\b', body)) != ids: problems.append((folder, pid, 'markers'))
        if '2026-10-15' not in body: problems.append((folder, pid, 'as_of'))
        if ev.source_notes(b).strip() not in body: problems.append((folder, pid, 'notes'))
        words = len(body.split('## Sources')[0].split())
        if folder == 'articles' and not 600 <= words <= 900: problems.append((folder, pid, f'words {words}'))
        if folder == 'video_scripts' and not 390 <= words <= 750: problems.append((folder, pid, f'script words {words}'))
        docs[folder].append({'piece_id': pid, 'markdown': body.split('## Sources')[0], 'claim_ids': sorted(ids), 'claims': b['claims']})
    for w in validate_documents(docs[folder], new_briefs, ev, accepted):
        problems.append((folder, w['piece_id'], w['explanation']))
print('PROBLEMS:', problems or 'none')
