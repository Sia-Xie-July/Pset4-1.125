"""Read-only audit of owned files; never opens the canonical evidence directory.

Prints finding locations only, never matched credentials. Patterns plus active
credential canaries are detection evidence, not a guarantee of secret absence.
"""
import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lib.records import SECRET_FIELD, SECRET_VALUE

ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = ['run.sh','workflows/collect_sources.sh','workflows/create_series.sh',
    'collectors/fetch_feeds.sh','collectors/fetch_youtube.sh','collectors/fetch_podcasts.sh',
    'processing/extract_content.sh','processing/filter_items.sh','data/store.sh',
    'editorial/select_items.sh','editorial/create_briefs.sh','content/write_articles.sh',
    'content/write_video_scripts.sh','review/check_content.sh','publishing/prepare_package.sh',
    'reporting/summarize_run.sh']
OMIT = {'.git','.venv','node_modules','__pycache__','.pytest_cache'}
active = [v.encode() for k,v in os.environ.items() if SECRET_FIELD.search(k) and len(v)>=8]
findings = []
checked = 0


def secrets(raw, location):
    global checked
    checked += 1
    if any(value in raw for value in active) or SECRET_VALUE.search(raw.decode('utf-8',errors='ignore')):
        findings.append({'check':'secrets','location':location,'detail':'Potential credential; value withheld'})


for directory, folders, names in os.walk(ROOT):
    base = Path(directory)
    folders[:] = [name for name in folders if name not in OMIT and base/name != ROOT/'data/evidence']
    for name in names:
        path = base/name
        if path.is_symlink():
            findings.append({'check':'scope','location':path.relative_to(ROOT).as_posix(),'detail':'Symlink not followed'})
            continue
        if path.suffix in ('.pyc','.sqlite3','.db'):
            continue
        raw = path.read_bytes()
        label = path.relative_to(ROOT).as_posix()
        secrets(raw,label)
        if path.suffix == '.py' and label != 'tests/audit_repo.py':
            tree = ast.parse(raw,filename=label)
            imports = [n for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom))]
            if any((getattr(n,'module','') or '').startswith('sqlite3') or
                   any(a.name=='sqlite3' for a in getattr(n,'names',[])) for n in imports):
                findings.append({'check':'index_ownership','location':label,'detail':'Direct SQLite import outside store.sh'})

for name in COMPONENTS:
    path = ROOT/name
    if not path.exists():
        findings.append({'check':'bash','location':name,'detail':'Missing required entry point'})
        continue
    text = path.read_text()
    if not text.startswith('#!/usr/bin/env bash\nset -euo pipefail\n'):
        findings.append({'check':'bash','location':name,'detail':'Missing shebang or strict shell mode'})
    result = subprocess.run(['/bin/bash','-n',str(path)],capture_output=True)
    if result.returncode:
        findings.append({'check':'bash','location':name,'detail':'Bash syntax check failed'})
    if re.search(r'declare\s+-A|\b(?:mapfile|readarray|sha256sum)\b|\$\{[^}]*,,\}',text):
        findings.append({'check':'bash32','location':name,'detail':'Nonportable shell feature'})

git_objects = subprocess.run(['git','rev-list','--objects','--all'],cwd=ROOT,capture_output=True,text=True,check=True)
historical = 0
for row in git_objects.stdout.splitlines():
    oid, _, name = row.partition(' ')
    if not name or name.startswith('data/evidence/'):
        continue
    result = subprocess.run(['git','cat-file','blob',oid],cwd=ROOT,capture_output=True)
    if result.returncode == 0:
        secrets(result.stdout,'git-history:'+name)
        historical += 1
config = subprocess.run(['git','rev-parse','--git-path','config'],cwd=ROOT,capture_output=True,text=True,check=True)
config_path = Path(config.stdout.strip())
if not config_path.is_absolute(): config_path = ROOT/config_path
if config_path.is_file(): secrets(config_path.read_bytes(),'git-config')

print(json.dumps({'required_bash_files':len(COMPONENTS),'files_or_blobs_scanned':checked,
    'historical_blobs_scanned':historical,'findings':findings,
    'scope':'Owned working files, hidden settings, Git history blobs and Git config; excludes installed dependencies, canonical evidence index and symlink targets',
    'limitations':'Unknown credential formats cannot be proven absent. SQLite access ownership also requires source review and store-interface tests.'},indent=2))
sys.exit(1 if findings else 0)
