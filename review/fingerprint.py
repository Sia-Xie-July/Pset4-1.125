"""Fingerprint saved review inputs; receipts and approvals are deliberately excluded."""
import hashlib
from pathlib import Path
from lib.records import asset_path, canonical, load_json


def fingerprint(run):
    inputs = {}
    names = ['run.json', 'briefs.jsonl', 'decisions.jsonl', 'eligible.jsonl',
             'articles.jsonl', 'video_scripts.jsonl']
    names += [f'{folder}/{piece}.md' for folder in ('articles', 'video_scripts')
              for piece in ('01', '02', '03')]
    for name in names:
        try:
            inputs[name] = hashlib.sha256((run / name).read_bytes()).hexdigest()
        except OSError:
            inputs[name] = None
    try:
        inputs['as_of_date'] = load_json((run/'run.json').read_text())['as_of_date']
        for line in (run/'eligible.jsonl').read_text().splitlines():
            item = load_json(line)
            for field in ('text_path', 'segments_path'):
                path = item.get(field)
                if isinstance(path, str):
                    try:
                        inputs['asset:'+path] = hashlib.sha256(asset_path(Path.cwd(), path).read_bytes()).hexdigest()
                    except (OSError, ValueError):
                        inputs['asset:'+path] = None
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        inputs['invalid_inputs'] = True
    return hashlib.sha256(canonical(inputs).encode()).hexdigest()
