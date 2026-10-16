"""Approved production handoff. Never supplies the student's human decision."""
import hashlib
import os
import shutil
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlsplit
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.records import canonical, load_json, utc_timestamp, safe_public_url
from lib.stage_runtime import InvalidInput, OperationalFailure, run_directory, run_stage
from lib.evidence import eligible
from review.check_content import assess

MANUAL_STEPS = [
    'Review audience-facing citations, interpretations, limitations, and AI attribution.',
    'Produce each 3–5 minute video in Google Vids or HeyGen; inspect narration, visuals, and timing.',
    'Publish three shareable Substack articles without a paid subscription requirement.',
    'Upload three public or unlisted YouTube videos; link article, video, and evidence references both ways.',
    'Enter real URLs in publication_links.json and verify course staff can open all six links.'
]


def approval_matches(approval, review_id):
    if not isinstance(approval, dict) or any(not isinstance(approval.get(k), str) or not approval[k].strip()
        for k in ('review_id', 'decision', 'reviewer', 'reviewed_at')) or not isinstance(approval.get('notes'), str):
        raise OperationalFailure('Missing or invalid human approval fields')
    try:
        utc_timestamp(approval['reviewed_at'])
    except ValueError:
        raise OperationalFailure('Human approval reviewed_at must be an ISO 8601 UTC timestamp') from None
    if approval['review_id'] != review_id:
        raise OperationalFailure('Stale approval: review_id differs from current reviewed inputs')
    if approval['decision'] != 'approve':
        raise OperationalFailure('Human approval decision must be approve; revisions remain pending')


def publication_links(value):
    if not isinstance(value, list) or len(value) != 3 or {r.get('piece_id') for r in value if isinstance(r, dict)} != {'01','02','03'}:
        raise InvalidInput('publication_links.json requires exactly three piece records')
    for row in value:
        for key in ('substack_url', 'youtube_url'):
            url = row.get(key, False)
            if url is not None and (not isinstance(url, str) or urlsplit(url).scheme not in ('http','https') or not urlsplit(url).hostname):
                raise InvalidInput('Publication URLs must be HTTP(S) strings or null')
            if url is not None:
                safe_public_url(url)
    return value


def main(metrics):
    run = run_directory()
    try:
        saved = load_json((run/'review.json').read_text())
        approval = load_json((run/'approval.json').read_text())
    except (OSError, ValueError):
        raise OperationalFailure('Passing review.json and matching human approval.json are required') from None
    current = assess(run, metrics)
    if not current['passed'] or saved.get('passed') is not True:
        raise OperationalFailure('Current content review has blocking errors')
    if saved.get('review_id') != current['review_id']:
        raise OperationalFailure('Stale review: reviewed inputs changed; rerun checks and obtain matching approval')
    approval_matches(approval, current['review_id'])
    package = run/'package'
    links = package/'publication_links.json'
    links_bytes = links.read_bytes() if links.exists() else (canonical([
        {'piece_id':p,'substack_url':None,'youtube_url':None} for p in ('01','02','03')])+'\n').encode()
    publication_links(load_json(links_bytes.decode()))
    metadata = load_json((run/'run.json').read_text())
    evidence = eligible(run, metadata)
    briefs = [load_json(line) for line in (run/'briefs.jsonl').read_text().splitlines()]
    staging = Path(tempfile.mkdtemp(prefix='.package-', dir=run))
    try:
        assets = []
        for brief in briefs:
            piece = brief['piece_id']
            for folder in ('articles','video_scripts','source_notes'):
                target = staging/folder/(piece+'.md')
                target.parent.mkdir(exist_ok=True)
                if folder == 'source_notes':
                    target.write_text(evidence.source_notes(brief), encoding='utf-8')
                else:
                    shutil.copyfile(run/folder/(piece+'.md'), target)
                assets.append({'piece_id':piece,'kind':folder,
                    'path':(package/folder/target.name).relative_to(Path.cwd()).as_posix(),
                    'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
        manifest = {'run_id':metadata['run_id'],'review_id':current['review_id'],
                    'as_of_date':metadata['as_of_date'],'mode':metadata['mode'],
                    'assets':assets,'manual_steps':MANUAL_STEPS,
                    'publication_links_path':(package/'publication_links.json').relative_to(Path.cwd()).as_posix(),
                    'videos_rendered':False,'publication_verified':False}
        (staging/'manifest.json').write_text(canonical(manifest)+'\n')
        (staging/'publication_links.json').write_bytes(links_bytes)
        (staging/'MANUAL_STEPS.md').write_text('# Production handoff\n\n'+'\n'.join('- '+s for s in MANUAL_STEPS)+'\n')
        if package.exists():
            archive = run/'attempts'/os.environ['INVOCATION_ID']
            archive.mkdir(parents=True, exist_ok=True)
            package.rename(archive/'package')
        staging.rename(package)
        print(canonical(manifest))
        metrics.update(input_count=6, output_count=1, asset_count=9)
    finally:
        if staging.exists():
            shutil.rmtree(staging)


if __name__ == '__main__':
    sys.exit(run_stage(main))
