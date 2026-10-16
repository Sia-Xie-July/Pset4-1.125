"""Offline contract tests, using only labeled fixtures and temporary stores."""
import hashlib
import http.server
import json
import os
import shutil
import subprocess
import sys
import threading
from pathlib import Path

import pytest
from processing.transcripts import parse

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests/fixtures/collection'


@pytest.fixture
def harness(tmp_path):
    repo = tmp_path / 'repo'
    for folder, names in {
        'lib': ['common.sh', 'records.py'],
        'data': ['store.sh', 'versioning.py'],
        'collectors': ['support.py', 'fetch_feeds.sh', 'fetch_feeds.py', 'fetch_podcasts.sh', 'fetch_podcasts.py', 'fetch_youtube.sh', 'fetch_youtube.py'],
        'processing': ['extract_content.sh', 'extract_content.py', 'media.py', 'transcripts.py'],
    }.items():
        (repo / folder).mkdir(parents=True, exist_ok=True)
        for name in names:
            shutil.copyfile(ROOT / folder / name, repo / folder / name)
    run = repo / 'runs/fictional'
    (run / 'config').mkdir(parents=True)
    (run / 'run.json').write_text(json.dumps({'run_id':'fictional', 'mode':'example', 'started_at':'2026-10-14T12:00:00Z', 'as_of_date':'2026-10-14', 'previous_run_id':None}))
    audio = tmp_path / 'audio.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=3', str(audio)], check=True)
    mirror_audio = tmp_path / 'mirror.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-i', str(audio), '-metadata', 'comment=FICTIONAL mirror container', str(mirror_audio)], check=True)
    state = {'untimed': False, 'changed': False, 'mirror': False, 'auto': False}
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def do_GET(self):
            base = f'http://127.0.0.1:{self.server.server_port}'
            if self.path == '/audio.wav':
                body = audio.read_bytes()
            elif self.path == '/mirror.wav':
                if state.get('media_unavailable'):
                    self.send_error(503); return
                body = mirror_audio.read_bytes()
            elif self.path == '/youtube.json':
                body = json.dumps({'id':'fixture1234', 'title':'FICTIONAL YouTube video', 'webpage_url':base+'/youtube.json',
                    'duration':3, 'timestamp':1791979200, '_fixture_media_url':base+'/mirror.wav',
                    'description':base+'/episode' if state['mirror'] else '',
                    'subtitles':{} if state['auto'] else {'en':[{'ext':'vtt','url':base+'/captions.vtt'}]},
                    'automatic_captions': {'en':[{'ext':'vtt','url':base+'/rolling.vtt'}]} if state['auto'] else {}}).encode()
            elif self.path == '/captions.vtt' and state['untimed']:
                if state['untimed'] == 'xml':
                    body = b'<transcript><broken'
                elif state['untimed'] == 'oversize':
                    body = b'WEBVTT\n\n00:00:00.000 --> 00:01:00.000\nFICTIONAL invalid interval\n'
                else:
                    body = b'FICTIONAL transcript with no usable timestamps'
            elif (FIXTURES / self.path.lstrip('/')).is_file():
                body = (FIXTURES / self.path.lstrip('/')).read_bytes().replace(b'{{BASE}}', base.encode())
                if self.path == '/captions.vtt' and state['changed']:
                    body = body.replace(b'These words are invented.', b'Changed FICTIONAL words.')
                if self.path == '/podcast.xml' and state['mirror']:
                    body = body.replace(b'FICTIONAL test episode', b'https://www.youtube.com/watch?v=fixture1234')
            else:
                self.send_error(503); return
            self.send_response(200); self.end_headers(); self.wfile.write(body)
    server = http.server.ThreadingHTTPServer(('127.0.0.1',0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    base = f'http://127.0.0.1:{server.server_port}'
    env = dict(os.environ, PATH=str(Path(sys.executable).parent)+os.pathsep+os.environ['PATH'],
               RUN_DIR='runs/fictional', PYTHONPATH=str(ROOT/'tests/fixtures/fake_tools'),
               PYTHONDONTWRITEBYTECODE='1', WHISPER_MODEL='base', WHISPER_DEVICE='cpu', WHISPER_COMPUTE_TYPE='int8')
    def command(script, *args, input=''):
        return subprocess.run(['/bin/bash',script,*args], cwd=repo, env=env, input=input, text=True, capture_output=True)
    assert command('data/store.sh','init').returncode == 0
    def configure(kind, broken=False):
        path = {'feed':'feed.xml', 'podcast':'podcast.xml', 'youtube':'youtube.json'}[kind]
        definitions = [{'source_id':'fictional-'+kind,'publisher_id':'fictional-producer','kind':kind,'url':base+'/'+path}]
        if broken:
            definitions.append(dict(definitions[0], source_id='fictional-failed', url=base+'/failed'))
        (run/'config/sources.json').write_text(json.dumps(definitions))
    def receipts(stage):
        return [json.loads(p.read_text()) for p in (run/'logs').glob(stage+'-*.json') if not p.name.endswith('-running.json')]
    yield repo, run, env, state, command, configure, receipts
    server.shutdown(); server.server_close()


@pytest.mark.parametrize('kind', ['feed','youtube','podcast'])
def test_collectors_standalone_partial_failure_and_pipe(harness, kind):
    repo, run, env, state, command, configure, receipts = harness
    configure(kind)
    script = 'collectors/fetch_'+('feeds' if kind=='feed' else 'podcasts' if kind=='podcast' else 'youtube')+'.sh'
    found = command(script,'runs/fictional','--max-items','1')
    assert found.returncode == 0, found.stderr
    candidate = json.loads(found.stdout)
    assert candidate['kind'] == kind
    if kind == 'podcast':
        assert candidate['media_url'].endswith('/audio.wav') and candidate['transcript_urls']
    extracted = command('processing/extract_content.sh','runs/fictional','--max-items','1', input=found.stdout)
    assert extracted.returncode == 0, extracted.stderr
    item = json.loads(extracted.stdout)
    assert item['version_id'] and (repo/item['text_path']).is_file()
    if kind != 'feed':
        assert item['transcript_method']=='native_captions' and item['transcript_model'] is None
        assert (repo/item['media_path']).is_file()
        assert len(json.loads((repo/item['segments_path']).read_text())) == 2
    else:
        assert 'controlled conditions' in (repo/item['text_path']).read_text()
    # Real shell pipe between independently runnable components.
    pipe = subprocess.run(['/bin/bash','-c','set -o pipefail; bash "$1" "$2" --max-items 1 | bash processing/extract_content.sh "$2" --max-items 1','fixture',script,'runs/fictional'],
                          cwd=repo, env=env, text=True,capture_output=True)
    assert pipe.returncode == 0, pipe.stderr
    assert json.loads(pipe.stdout)['version_id'] == item['version_id']
    configure(kind, broken=True)
    failed = command(script,'runs/fictional')
    assert failed.returncode == 1 and len(failed.stdout.splitlines()) == 1
    assert any(r['errors'] and r['exit_code']==1 for r in receipts('fetch_'+('feeds' if kind=='feed' else 'podcasts' if kind=='podcast' else 'youtube')))


def test_reuse_changed_assets_and_cpu_fallback(harness):
    repo, run, env, state, command, configure, receipts = harness
    configure('podcast')
    candidates = command('collectors/fetch_podcasts.sh','runs/fictional').stdout
    first = command('processing/extract_content.sh','runs/fictional',input=candidates)
    assert first.returncode == 0, first.stderr
    original = json.loads(first.stdout)
    old_bytes = (repo/original['segments_path']).read_bytes()
    assert command('data/store.sh','upsert','runs/fictional',input=first.stdout).returncode == 0
    replay = command('processing/extract_content.sh','runs/fictional',input=candidates)
    assert replay.returncode == 0, replay.stderr
    assert json.loads(replay.stdout)['extraction_reused']
    assert json.loads(replay.stdout)['version_id'] == original['version_id']
    state['changed'] = True
    changed = command('processing/extract_content.sh','runs/fictional',input=candidates)
    new = json.loads(changed.stdout)
    assert new['version_id'] != original['version_id'] and new['segments_path'] != original['segments_path']
    assert (repo/original['segments_path']).read_bytes() == old_bytes
    state['untimed'] = True
    fallback = command('processing/extract_content.sh','runs/fictional',input=candidates)
    assert fallback.returncode == 0, fallback.stderr
    asr = json.loads(fallback.stdout)
    assert asr['transcript_method'] == 'faster_whisper' and asr['transcript_model'] == 'base'
    assert command('data/store.sh','upsert','runs/fictional',input=fallback.stdout).returncode == 0
    second_asr = command('processing/extract_content.sh','runs/fictional',input=candidates)
    assert json.loads(second_asr.stdout)['extraction_reused']
    assert any(r['models'] and r['items'][0]['transcription']['device']=='cpu' for r in receipts('extract_content'))
    for invalid_native in ('xml','oversize'):
        state['untimed'] = invalid_native
        repaired = command('processing/extract_content.sh','runs/fictional',input=candidates)
        assert repaired.returncode == 0, repaired.stderr
        assert json.loads(repaired.stdout)['transcript_method'] == 'faster_whisper'
        assert json.loads(repaired.stdout)['warnings']


def test_duration_limit_and_malformed_input(harness):
    repo, run, env, state, command, configure, receipts = harness
    configure('podcast')
    discovery = command('collectors/fetch_podcasts.sh','runs/fictional','--max-duration-minutes','0.01')
    assert discovery.returncode == 1 and discovery.stdout == ''
    candidates = command('collectors/fetch_podcasts.sh','runs/fictional').stdout
    skipped = command('processing/extract_content.sh','runs/fictional','--max-duration-minutes','0.01', input=candidates)
    assert skipped.returncode == 1 and skipped.stdout == ''
    assert 'duration_limit' in skipped.stderr
    malformed = command('processing/extract_content.sh','runs/fictional',input=candidates+'{bad}\n')
    assert malformed.returncode == 2 and malformed.stdout == ''
    assert command('collectors/fetch_feeds.sh','runs/fictional','--max-items','-1').returncode == 2


def test_recording_deduplication_and_auto_caption_cleanup(harness):
    repo, run, env, state, command, configure, receipts = harness
    state['mirror'] = True
    state['auto'] = True
    configure('youtube')
    youtube = command('collectors/fetch_youtube.sh','runs/fictional').stdout
    configure('podcast')
    podcast = command('collectors/fetch_podcasts.sh','runs/fictional').stdout
    result = command('processing/extract_content.sh','runs/fictional', input=youtube+podcast)
    assert result.returncode == 0, result.stderr
    assert len(result.stdout.splitlines()) == 1
    item = json.loads(result.stdout)
    assert item['aliases'] and item['transcription']['origin']=='automatic'
    assert 'Reciprocal' in item['deduplication_basis']
    segments = json.loads((repo/item['segments_path']).read_text())
    assert [s['text'] for s in segments] == ['FICTIONAL rolling captions','are deduplicated']
    assert command('data/store.sh','upsert','runs/fictional',input=result.stdout).returncode == 0
    alias = item['aliases'][0]['item_id']
    assert json.loads(command('data/store.sh','get',alias).stdout)['item_id']==item['item_id']


def test_timeless_transcript_is_not_fabricated():
    with pytest.raises(ValueError):
        parse(b'FICTIONAL text without timestamps')


def test_later_confirmed_recording_match_preserves_historical_get(harness):
    repo, run, env, state, command, configure, receipts = harness
    configure('youtube')
    youtube = command('collectors/fetch_youtube.sh','runs/fictional').stdout
    first = command('processing/extract_content.sh','runs/fictional',input=youtube)
    assert command('data/store.sh','upsert','runs/fictional',input=first.stdout).returncode==0
    configure('podcast')
    podcast = command('collectors/fetch_podcasts.sh','runs/fictional').stdout
    second = command('processing/extract_content.sh','runs/fictional',input=podcast)
    assert second.returncode==0, second.stderr
    historical = json.loads(second.stdout)
    assert command('data/store.sh','upsert','runs/fictional',input=second.stdout).returncode==0
    assert len(command('data/store.sh','list').stdout.splitlines())==2
    state['mirror'] = True
    podcast = command('collectors/fetch_podcasts.sh','runs/fictional').stdout
    joined = command('processing/extract_content.sh','runs/fictional',input=youtube+podcast)
    assert joined.returncode==0, joined.stderr
    saved = command('data/store.sh','upsert','runs/fictional',input=joined.stdout)
    assert saved.returncode==0, saved.stderr
    assert len(command('data/store.sh','list').stdout.splitlines())==1
    old = command('data/store.sh','get',historical['item_id'],historical['version_id'])
    assert json.loads(old.stdout)['version_id']==historical['version_id']


def test_extraction_partial_failure_and_max_items(harness):
    repo, run, env, state, command, configure, receipts = harness
    configure('feed')
    good = command('collectors/fetch_feeds.sh','runs/fictional').stdout
    bad = json.loads(good)
    bad['item_id'] = 'fixture:inaccessible'
    bad['url'] = bad['url'].replace('/article.html','/failed')
    limited = command('processing/extract_content.sh','runs/fictional','--max-items','1',input=good+json.dumps(bad)+'\n')
    assert limited.returncode == 0 and len(limited.stdout.splitlines())==1
    failed = command('processing/extract_content.sh','runs/fictional',input=good+json.dumps(bad)+'\n')
    assert failed.returncode == 1 and len(failed.stdout.splitlines())==1
    assert any(r['output_count']==1 and r['errors'] and r['exit_code']==1 for r in receipts('extract_content'))


def test_identical_recording_repost_does_not_add_independent_item(harness):
    repo, run, env, state, command, configure, receipts = harness
    configure('podcast')
    original = json.loads((run/'config/sources.json').read_text())[0]
    repost = dict(original,source_id='FICTIONAL-reposting-route',publisher_id='FICTIONAL-different-reposter')
    (run/'config/sources.json').write_text(json.dumps([original,repost]))
    found = command('collectors/fetch_podcasts.sh','runs/fictional')
    assert found.returncode == 0 and len(found.stdout.splitlines())==2
    extracted = command('processing/extract_content.sh','runs/fictional',input=found.stdout)
    assert extracted.returncode == 0 and len(extracted.stdout.splitlines())==1, extracted.stderr
    item = json.loads(extracted.stdout)
    assert item['aliases'] and 'Exact original recording bytes' in item['deduplication_basis']


def test_refreshed_date_does_not_make_unchanged_written_content_new(harness):
    repo, run, env, state, command, configure, receipts = harness
    configure('feed')
    found = command('collectors/fetch_feeds.sh','runs/fictional')
    initial = command('processing/extract_content.sh','runs/fictional',input=found.stdout)
    original = json.loads(initial.stdout)
    assert command('data/store.sh','upsert','runs/fictional',input=initial.stdout).returncode==0
    refreshed = json.loads(found.stdout); refreshed['published_at']='2026-10-14T13:00:00Z'
    result = command('processing/extract_content.sh','runs/fictional',input=json.dumps(refreshed)+'\n')
    assert result.returncode==0, result.stderr
    item = json.loads(result.stdout)
    assert item['published_at']==original['published_at'] and item['version_id']==original['version_id']
    assert 'earliest verified' in item['publication_date_basis']


def test_podcast_episode_allowlist_standalone_and_partial_failure(harness):
    repo, run, env, state, command, configure, receipts = harness
    configure('podcast')
    path = run/'config/sources.json'
    definitions = json.loads(path.read_text())
    definitions[0]['episode_ids'] = ['fictional-episode']
    path.write_text(json.dumps(definitions))
    result = command('collectors/fetch_podcasts.sh','runs/fictional')
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['native_id'] == 'fictional-episode'
    definitions[0]['episode_ids'].append('FICTIONAL-missing')
    path.write_text(json.dumps(definitions))
    result = command('collectors/fetch_podcasts.sh','runs/fictional')
    assert result.returncode == 1 and len(result.stdout.splitlines()) == 1
    assert any(r['exit_code'] == 1 and r['errors'] for r in receipts('fetch_podcasts'))


def test_unchanged_native_captions_reuse_verified_download(harness):
    repo, run, env, state, command, configure, receipts = harness
    configure('youtube')
    found = command('collectors/fetch_youtube.sh','runs/fictional')
    first = command('processing/extract_content.sh','runs/fictional',input=found.stdout)
    assert first.returncode == 0, first.stderr
    assert command('data/store.sh','upsert','runs/fictional',input=first.stdout).returncode == 0
    state['media_unavailable'] = True
    same = command('processing/extract_content.sh','runs/fictional',input=found.stdout)
    assert same.returncode == 0, same.stderr
    item = json.loads(same.stdout)
    assert item['extraction_reused'] and item['version_id'] == json.loads(first.stdout)['version_id']
    assert 'native transcript' in item['reuse_basis']
    state['changed'] = True
    changed = command('processing/extract_content.sh','runs/fictional',input=found.stdout)
    assert changed.returncode == 1 and changed.stdout == ''
