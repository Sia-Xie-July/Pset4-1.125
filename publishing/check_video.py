"""Manual production QA for an exported audience video (not a pipeline stage).

Usage: python3 publishing/check_video.py VIDEO.mp4 [--min-scenes 6] [--max-shot 45]

Checks with ffmpeg/ffprobe only:
  - duration is 3-5 minutes
  - at least N distinct visual scenes, and no single background held too long
  - no blank/flat (empty) frames
  - an English caption track covers the whole narration (start, end, gaps)
Writes VIDEO.contact.png (one frame every 10 s) for a visual spot-check.
Exit 0 = all checks pass, 1 = at least one FAIL. Burned-in captions cannot be
verified automatically; inspect the contact sheet.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def run(*args):
    return subprocess.run(args, capture_output=True, text=True)


def seconds(stamp):
    h, m, s = stamp.replace(',', '.').split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video')
    ap.add_argument('--min-scenes', type=int, default=6)
    ap.add_argument('--max-shot', type=float, default=45.0)
    ap.add_argument('--scene-threshold', type=float, default=0.3)
    a = ap.parse_args()
    video = Path(a.video)
    results = []

    def report(ok, name, detail):
        results.append(ok)
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}")

    probe = json.loads(run('ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(video)).stdout)
    duration = float(probe['format']['duration'])
    report(180 <= duration <= 300, 'duration', f'{duration:.1f}s (target 180-300s)')

    # Scene changes -> shots
    out = run('ffmpeg', '-hide_banner', '-i', str(video), '-vf',
              f"select='gt(scene,{a.scene_threshold})',showinfo", '-f', 'null', '-').stderr
    cuts = [float(x) for x in re.findall(r'pts_time:([0-9.]+)', out)]
    bounds = [0.0] + cuts + [duration]
    shots = [round(b - s, 1) for s, b in zip(bounds, bounds[1:])]
    report(len(shots) >= a.min_scenes, 'scene count', f'{len(shots)} shots (need >= {a.min_scenes}); cuts at {[round(c, 1) for c in cuts]}')
    longest = max(shots)
    report(longest <= a.max_shot, 'longest single background', f'{longest}s (limit {a.max_shot}s); shot lengths {shots}')

    # Blank / flat frames: sample a 32x18 grey frame every 2 s and measure contrast.
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(video), '-vf', 'fps=1/2,scale=32:18,format=gray',
                          '-f', 'rawvideo', '-'], capture_output=True).stdout
    flat = []
    for i in range(len(raw) // 576):
        px = raw[i * 576:(i + 1) * 576]
        mean = sum(px) / 576
        std = (sum((p - mean) ** 2 for p in px) / 576) ** 0.5
        if std < 8:
            flat.append(i * 2)
    report(not flat, 'no empty/flat frames', f'flat frames at {flat}s' if flat else 'none found')

    # Captions
    subs = [s for s in probe['streams'] if s['codec_type'] == 'subtitle']
    if not subs:
        report(False, 'caption track', 'no subtitle stream in the file; if captions are burned in, '
               'check the contact sheet, and upload captions_NN.txt to YouTube as English subtitles')
    else:
        srt = run('ffmpeg', '-v', 'error', '-i', str(video), '-map', '0:s:0', '-f', 'srt', '-').stdout
        cues = [(seconds(x), seconds(y)) for x, y in re.findall(r'(\d+:\d+:\d+,\d+) --> (\d+:\d+:\d+,\d+)', srt)]
        lang = subs[0].get('tags', {}).get('language', 'und')
        gaps = [(round(e, 1), round(s2 - e, 1)) for (_, e), (s2, _) in zip(cues, cues[1:]) if s2 - e > 8]
        ok = bool(cues) and cues[0][0] <= 8 and cues[-1][1] >= duration - 15 and not gaps
        report(ok, 'caption coverage', f'language={lang}, {len(cues)} cues, first {cues[0][0] if cues else None}s, '
               f'last ends {cues[-1][1] if cues else None}s of {duration:.0f}s, gaps>8s at {gaps}')

    sheet = video.with_suffix('.contact.png')
    run('ffmpeg', '-v', 'error', '-y', '-i', str(video), '-vf', 'fps=1/10,scale=480:-1,tile=4x8', '-frames:v', '1', str(sheet))
    print(f'INFO  contact sheet: {sheet}')
    sys.exit(0 if all(results) else 1)


if __name__ == '__main__':
    main()
