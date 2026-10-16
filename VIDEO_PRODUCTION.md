# Audience video production (Google Vids)

Manual handoff after human review. Inputs for each episode NN (run `runs/20261015T052758Z-daba50c83a0b`):

| File | Use |
|---|---|
| `production/VIDEO_PLAN.md` | Scene-by-scene plan: background, on-screen text, narration paragraph |
| `production/NN.txt` | Exact narration (one paragraph = one scene). Same text as `video_scripts/NN.md` |
| `production/captions_NN.txt` | English caption transcript for YouTube (upload "without timing"; YouTube syncs it) |
| `production/youtube_description_NN.txt` | YouTube description: article link, sources with timestamps, AI disclosure |
| `publishing/check_video.py` | QA check of the exported MP4 |

## Requirements each video must meet

From the course README/policy:
- 3–5 minutes; made in Google Vids (or HeyGen); presents the article's central argument for viewing/listening.
- Generated from the same reviewed brief as the article; **same factual claims** (narration must not add or strengthen claims).
- Evidence references understandable to viewers: source cards on screen (publisher, title, date, timestamp) and full references in the description.
- Article ↔ video linked both ways; description includes the article link and source references.
- AI-generated presentation identified (presenter, voice, AI-assisted script).
- Public or unlisted on YouTube; staff can open it.

Production standards for this series:
1. An **AI avatar presents at least the opening scene** (scene 1). Optional: avatar again in the last scene.
2. **No empty pages**: every scene has a background image (stock or Vids-generated), never a plain colour.
3. **English captions for the whole video**, including the avatar scene.
4. **At least 6 scenes with different backgrounds**; no background held longer than ~45 s. (Plans have 9, 10 and 11 scenes.)
5. No logos or recognisable real people in backgrounds; source names appear only as text.

## Steps in Google Vids (per episode)

1. New video → blank (or "Help me create" with the scene list pasted, then edit every scene to match the plan exactly).
2. Create one scene per paragraph of `production/NN.txt`, in order.
3. Scene 1: insert an **AI avatar**, paste paragraph 1 as its script. Add the lower-third text from the plan.
4. Scenes 2…N: set the background image from the plan (Vids stock search term given), add the on-screen text block, and set the voiceover to the paragraph text using the **same AI voice** as the avatar. Source scenes get the "SOURCE · …" card.
5. Turn **captions on** for the video and confirm they appear on every scene, including the avatar scene.
6. Play through once: check pronunciation of names (Cukjati, Sanfilippo, antirez, METR), pacing, and that no scene is blank.
7. Download as MP4 into `videos/` named `Before the Merge NN.mp4`.

## QA before upload

```bash
python3 publishing/check_video.py "videos/Before the Merge 01.mp4"
```
All lines must be PASS. Then open the `*.contact.png` it writes and check that captions are visible and every frame has a picture.
If the MP4 has no caption track (burned-in only), the caption check fails by design — confirm captions visually and upload `captions_NN.txt` to YouTube.

Result on v2 exports (2026-10-15 18:31 UTC): 01 207.5 s, 02 237.6 s, 03 268.5 s — all checks PASS (11/10/11 shots, longest 22–31 s, no blank frames, captions from 0 s to end). An earlier v2 export failed QA (1–1.5 s white flash after the avatar in 01 and 03; no intro captions in 02); both were fixed in Vids and re-exported. The failed files were not retained.

Result on the first draft of 01, *Illustrated Edition — Draft* (2026-10-15; file not retained): duration PASS (209 s); **4 scenes (FAIL)**, one background held 91 s (FAIL); captions only 18–118 s, missing on the avatar intro and the last 91 s (FAIL). It must be rebuilt to the plan.

## YouTube upload

1. Upload the MP4; title `Before the Merge NN — <episode title>`; visibility Unlisted or Public.
2. Paste `production/youtube_description_NN.txt`; replace `[SUBSTACK ARTICLE URL]` and episode URLs.
3. Subtitles → English → Upload file → *Without timing* → `production/captions_NN.txt` → check sync → Publish.
4. Mark "altered or synthetic content" if YouTube asks (AI avatar/voice).
5. Put the YouTube link in the Substack article; record both URLs in `package/publication_links.json` and `production/videos.jsonl`; open both links in a private window to verify access.

## Published (2026-10-15)

| Episode | YouTube (unlisted) | Subtitles uploaded | Description |
|---|---|---|---|
| 01 | https://youtu.be/2mOpLgQUm2Y | `production/subtitles/captions_01_timed.srt` | `production/youtube_description_01_upload.txt` |
| 02 | https://youtu.be/nKaQr6ya9cY | `production/subtitles/captions_02_timed.srt` | `production/youtube_description_02_upload.txt` |
| 03 | https://youtu.be/cexb5hJ__Ss | `production/subtitles/captions_03_timed.srt` | `production/youtube_description_03_upload.txt` |

Paths are under `runs/20261015T052758Z-daba50c83a0b/`. Exported from Google Vids with
"Export to YouTube", then edited in YouTube Studio: title, description (sources with
timestamps, AI disclosure, series links), not made for kids, no paid promotion, **AI use = Yes**
(adds YouTube's altered/synthetic label), language English, visibility Unlisted.
The subtitle files are the timed English track from each Vids export with speech-recognition
errors corrected (names such as Cukjati, Sanfilippo, Cloudflare, METR; repeated words).
Access was checked with YouTube's public oEmbed lookup without signing in.
Each description now links its Substack article (updated 2026-10-15).

## Technical demonstration (separate from the audience videos)

See [demo/README.md](demo/README.md): `demo/Before_the_Merge_technical_demo.mp4` (4:48), built from real run outputs by `demo/source/`.
