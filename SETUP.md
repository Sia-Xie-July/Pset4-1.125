# macOS setup and collection/extraction

## Local LLM (current default, no API key)

Install with `brew install ollama` and `ollama pull qwen3:8b`.
In a separate terminal run `OLLAMA_NO_CLOUD=1 ollama serve` if the server is not
already running. Then use `bash run_local.sh` from this repository.
The launcher ignores legacy `.env` settings and clears cloud model credentials
and stage overrides. Local transport uses loopback only, bypasses HTTP proxies,
and never sends an Authorization header. There is no automatic cloud fallback.
`LOCAL_MODEL_NAME` overrides the model; the default is Qwen3 8B.
The context is 32768 tokens with an 8192 output budget. Oversized requests fail
before inference, rather than silently truncating evidence. Local selection runs
per item, and briefs/content run per piece using explicit literal excerpts.
Full source assets remain available for human review of omitted context.
Local inference reports zero API charges; electricity and hardware are excluded.
Standalone components default to local unless MODEL_PROVIDER is explicitly set.
Earlier cloud configuration examples below/elsewhere are legacy alternatives.

Editorial/content components and the standalone series workflow are also now
available. See [EDITORIAL.md](EDITORIAL.md) for model environment variables,
schemas, evidence checks, fixture tests and invocation commands. The root entry
point runs collection, editorial generation and checks, stopping for human review.

Tested on Apple Silicon with macOS `/bin/bash` 3.2.57, Python 3.13.7, ffmpeg
9.0.2, and the versions in `requirements.txt`. No newer Bash is required. Python
3.13 is recommended explicitly because installing Homebrew yt-dlp can also
change the globally linked Python; activate the project venv before running scripts.

## Install

```bash
brew install ffmpeg yt-dlp jq python@3.13
"$(brew --prefix python@3.13)/bin/python3.13" -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m pip check
```

The Python yt-dlp package includes its JavaScript support (`[default]`). Homebrew
yt-dlp installs the Deno runtime used for current YouTube challenges. Use the
venv's Python package for this project. Faster-whisper 1.2.1 is paired with
PyAV 16.1.0: the live test exposed an incompatible `metadata_errors` API in
PyAV 19, so requirements pin the tested pair. Native captions need no model
download. The first fallback downloads the base model from Hugging Face.

```bash
export WHISPER_MODEL=base
export WHISPER_DEVICE=cpu
export WHISPER_COMPUTE_TYPE=int8
export TRANSCRIPT_LANGUAGES=en,en-US,en-GB
```

These Whisper settings are defaults, so exporting them is optional. Model size
or a local model directory, device, and compute type are configurable. For this
Mac use CPU/int8; the implementation does not select NVIDIA or Metal. Optional
`HF_HOME` sets the model cache directory. Authentication, if needed, comes from
environment variables such as `HF_TOKEN`; never put tokens in config, source URLs,
or run snapshots. This phase makes no paid transcription API calls; receipts
leave unmeasured cost null.

## Prepare an existing run

The entry point and both workflows are implemented. Populate
your own root config and all four prompts, then run `bash run.sh`. It validates
them, captures UTC start/as-of once, creates a unique run directory, copies exact
config/prompt snapshots, initializes the store, runs collection and freshness
filtering, then generates and checks the series. Alternate inputs use `--config-dir DIR --prompts-dir DIR`;
fixture/replay runs must explicitly use `--mode example` or `--mode replay`.
Source files are not edited. Missing/blank settings return 2 with receipts and a
summary. Credentials are never copied from environment variables into snapshots.

Successful checks stop at awaiting_review. Supply your own human approval after
reviewing the actual material, then use `bash run.sh --package runs/RUN_ID` for the
production handoff without recollection or draft regeneration. See EDITORIAL.md
for model settings and PUBLISHING.md for approval, packaging and summary details.
Operational failures return 1, invalid config/input returns 2, and usable partial
results are retained. `--collection-only` is available for collection diagnostics;
its summary reports the unfinished pipeline honestly as failed.

For standalone workflow use, prepare run.json and config/prompts snapshots, run
`RUN_DIR=runs/RUN_ID bash data/store.sh init`, then invoke
`bash workflows/collect_sources.sh runs/RUN_ID`. Its stdout is collection status
JSON. It saves every collector exit code in collection_status.json and every
downstream/pipe status in collection_stages.jsonl. The real Item pipe is
store list → tee corpus.jsonl → filter. Earlier workflow outputs move into a
unique attempts/ directory on resume, and earlier receipts remain untouched.
Components never substitute root configuration for a missing snapshot.

You supply `RUN_DIR/config/sources.json`, an array with `source_id`, `publisher_id`,
`kind`, and `url`. Written RSS/Atom uses feed; a YouTube video/channel/playlist uses
youtube; a podcast feed uses podcast. Endpoints from one producer share
publisher_id. Do not use signed/credential-bearing URLs in saved configuration.
Collectors derive podcast IDs from source_id and episode GUID (falling back to
episode URL/enclosure), YouTube IDs from native video IDs, and written IDs from
canonical article URLs. Date-only metadata is retained separately when available;
published_at stays null if an actual time is not known. No midnight is invented.

## Standalone and pipes

Commands below assume the venv is activated and R names a prepared run.

```bash
R=runs/RUN_ID
RUN_DIR="$R" bash data/store.sh init
bash collectors/fetch_feeds.sh "$R" --max-items 2 > "$R/feeds-candidates.jsonl"
bash collectors/fetch_youtube.sh "$R" --max-items 1 --max-duration-minutes 6 > "$R/youtube-candidates.jsonl"
bash collectors/fetch_podcasts.sh "$R" --max-items 1 --max-duration-minutes 6 > "$R/podcast-candidates.jsonl"
bash processing/extract_content.sh "$R" --max-items 2 < "$R/feeds-candidates.jsonl" > "$R/feed-items.jsonl"
bash processing/extract_content.sh "$R" --max-items 1 --max-duration-minutes 6 < "$R/youtube-candidates.jsonl" > "$R/youtube-items.jsonl"
bash processing/extract_content.sh "$R" --max-items 1 --max-duration-minutes 6 < "$R/podcast-candidates.jsonl" > "$R/podcast-items.jsonl"
```

For a pipe, preserve the collector's status as well as extraction's:

```bash
set -o pipefail
bash collectors/fetch_feeds.sh "$R" --max-items 1 | bash processing/extract_content.sh "$R" --max-items 1
bash collectors/fetch_youtube.sh "$R" --max-items 1 | bash processing/extract_content.sh "$R" --max-items 1
bash collectors/fetch_podcasts.sh "$R" --max-items 1 | bash processing/extract_content.sh "$R" --max-items 1
```

Each invocation saves unique receipts, including partial failures. Valid records
remain on stdout when one source/item fails; the final exit is 1. Argument/config
and structural JSONL errors return 2. Extraction validates the entire input stream
before downloading, so malformed batches do not publish partial Item records.
Successful empty feed searches are measured successes, distinct from request failures.

`--max-items N` applies globally to each invocation (0 means unlimited); its env
default is `MAX_ITEMS=0`. Intentional item limits are recorded in receipts. Media
duration defaults to 20 minutes (`MAX_DURATION_MINUTES`), overridable by
`--max-duration-minutes`. Collectors check discovered duration when available;
extraction checks metadata before download and actual ffprobe duration before
transcription. If a feed omits duration, the original must be downloaded to measure
it. A duration skip is an error/exit 1, with an explicit reason in the receipt.

## Transcript and asset behavior

YouTube retrieves caption track metadata through yt-dlp, tries manually supplied
subtitles first, then generated captions. Podcast discovery preserves audio
enclosures and namespace transcript links. Supported native formats include
WebVTT, SRT, YouTube json3, segment JSON, and common timed XML. Untimed HTML/plain
text never gets invented offsets; failed or untimed native tracks fall back to
faster-whisper. Native attempts and fallback warnings remain inspectable in Item
records. Actual native/transcription failure is recorded rather than an empty success.

All transcripts are arrays of segment_id/start_seconds/end_seconds/text. Times
are numbers, empty cues are removed, and adjacent rolling captions lose exact
repeats/overlapping words. Ordinary later repetitions and manual caption prose
remain. Items and receipts record native_captions (model null) or faster_whisper
(model name, device, compute type). Reused ASR records mark executed false.

Original downloads go to content-addressed files in data/media; extracted text
and normalized segments go to data/assets. Complete files are published by
hard-linking, without replacing existing files. Hash collisions/corrupt saved
files fail explicitly. Referenced assets are never overwritten. Original media
is ignored by Git; retain it locally or document retrieval for submission.

Extraction uses store.sh list to discover prior items/aliases, then checks their
asset hashes. Full written content is fetched anew and compared after normalization.
Native captions are retrieved/normalized anew. Media bytes are downloaded and
hashed; unchanged recordings with verified saved ASR skip another transcription.
Retrieval time, paths, media transport URLs, method/model bookkeeping and run IDs
are excluded from the version hash. Evidence-relevant metadata and substantive
text/segment changes do affect it. See data/README.md for the exact algorithm.
When unchanged normalized text or original recording bytes have a later advertised
publication date, extraction keeps the earlier verified date. A refreshed date
therefore does not make previously retained unchanged material newly eligible.
Persist extracted output via `bash data/store.sh upsert "$R" < items.jsonl` before
the next run to enable reuse. Extraction itself never reads the evidence index.

## Recording reconciliation

Exact original recording bytes are a confirmed match, including a reposting
endpoint with a different declared publisher_id. This prevents copies from adding
independent evidence. For
different transport encodings, the podcast episode metadata must link to that
YouTube ID and the YouTube description must reciprocally link to the exact episode
URL, with matching publisher_id. This is an explicit producer linkage, not a
title/date similarity guess. Episode links with only one direction are reported
as unresolved when the corresponding route is in the corpus; verify them before
counting distinct coverage. Copies lacking any linkage or identical bytes need
human identity review; this implementation does not infer equivalence acoustically.

One representative item ID/transcript is retained, with alternate routes as
aliases and discovery_routes. Its offsets always link to its own recording.
An earlier verified publication time found during reconciliation is retained;
uploading a copy later does not refresh freshness. The pipeline emits one Item
per reconciled recording in an extraction invocation. Store upsert persists aliases.
If both identities already existed, a confirmed merge retires only the duplicate
current pointer; all old versions, run observations and version-pinned get calls
remain available. Coverage must count this recording once and use its canonical
kind, not count a dual-platform copy as two distinct media items.

## Configured publication topic

The project now uses Before the Merge: evidence-based coding-agent adoption for
technical leads of 3–10-person software teams. Articles/scripts are English;
PROJECT_BRIEF.md, SOURCE_NOTES.md and NEXT_STEPS.md explain the editorial choices
and execution plan (all in English). The root policy is v2 after human review (v1 is kept in
docs/policy/); the four prompts are populated.

Sources may set positive integer `max_entries` to bound discovery within that
source. Receipts report `discovery_limit` and `limited:true`; summary coverage
limitations remain explicit. This is separate from the collector-wide MAX_ITEMS
limit and lets several publishers contribute without processing entire archives.
The configured source set contains recordings longer than 20 minutes. Only if
prepared to process them, use the explicit MAX_DURATION_MINUTES=40 override in
NEXT_STEPS.md; the default safeguard itself remains unchanged.

## Test commands

```bash
bash tests/test_components.sh
python3 -m pytest -q tests/test_collection.py
python3 -m pytest -q tests/test_orchestration.py
python3 tests/dry_run_collection.py
python3 tests/dry_run_collection.py --simulate-failure
python3 tests/run_live_smoke.py
```

Offline tests use a localhost fixture server, invented text/captions, sine-wave
media, and explicitly labeled fake yt-dlp/ASR adapters. Each collector/extractor
entry point is exercised standalone and in a real Bash pipe. No production fixture
switch exists. Tests copy only implementation files to isolated temporary
repositories; store.sh alone opens their indexes.

The live smoke script uses real network adapters and audio: a 19-second YouTube
upload and a short NPR News Now episode, then repeats each through a pipe. It
prints actual command results and retains all artifacts, receipts and media in a
temporary repository. It uses mode example and labels the real transport test as
non-publication evidence; the old YouTube upload cannot satisfy 30-day freshness.
No user editorial config is altered. See docs/history/TEST_RESULTS.md for observed results.

The collection dry-run driver creates an isolated temporary repository, supplies
minimal labeled fictional project/policy/prompt placeholders, and runs the actual
run.sh/workflow against the offline fixture server. It prints the run directory
tree and retains all artifacts. The simulated failure adds a labeled inaccessible
feed; the entry point must exit 1 while extraction/upsert/filter continue with
valid records. This test driver requires the pytest development dependency.

Reference APIs: [yt-dlp](https://github.com/yt-dlp/yt-dlp),
[faster-whisper](https://github.com/SYSTRAN/faster-whisper),
[podcast transcript namespace](https://github.com/Podcastindex-org/podcast-namespace/blob/main/docs/tags/transcript.md).
