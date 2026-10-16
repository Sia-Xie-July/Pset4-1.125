# Historical collection and extraction verification — 2026-10-14

These are development tests, not a submitted publication run. Offline fixtures
are explicitly fictional. The live transport test uses real media but mode example;
its historical YouTube upload is ineligible for assignment evidence.

## Before the Merge topic configuration

The user authorized populating the recommended topic and chose English articles
and scripts with Chinese planning notes (later translated into English). Project, real source entry points,
policy v1, and all four prompts are now populated. This is configuration work,
not a completed live publication run or human approval.

Metadata-only network checks returned parseable HTTP 200 feeds for Simon
Willison Entries, GitHub's Copilot changelog, Cloudflare's AI tag, METR and NLW's
AI Daily Brief. Native yt-dlp metadata was retrieved for all four configured video
IDs. No media was downloaded/transcribed and no paid model request was made by
these checks. Source limitations and original links are in SOURCE_NOTES.md.

The configured set has 9 entry points, 8 declared producer groups, all 3 kinds,
and at most 25 discovered entries under per-source max_entries. These are
configuration counts, not verified independent evidence or accepted-source totals.
The per-source discovery bound was added to the owning collector helper to avoid
processing the entire 1,100+ episode podcast archive. Bounds remain explicit in receipts.

Actual outputs:

```text
$ .venv/bin/python -m pytest tests/test_topic_config.py tests/test_audit_contracts.py -q
30 passed in 9.67s
$ .venv/bin/python -m pytest tests/test_topic_config.py tests/test_collection.py tests/test_orchestration.py -q
23 passed in 31.93s
$ .venv/bin/python tests/audit_repo.py
required_bash_files: 16
files_or_blobs_scanned: 169
historical_blobs_scanned: 38
findings: []
```

The second invocation includes the real topic snapshot-validation test added
after the first invocation. Discovery behavior and transport tests are explicitly
fictional offline fixtures; they do not consume the real sources as evidence.
No model provider/name/key was configured in the execution environment when
checked. Formal source-versioned briefs/articles/scripts, two actual dated runs,
student review and real publication links therefore remain pending rather than
being filled with fabricated results. The student will provide their identity
and repository URL later. See NEXT_STEPS.md for actual execution instructions.

## Whole-repository architecture audit

See AUDIT.md for section-by-section statuses, repaired defects, boundaries and
reproducible verification commands. Student configuration and real publication/
live-run requirements remain pending; no fictional completion was supplied.

Actual outputs after fixes to credential persistence, operational exit codes,
relative run paths, receipt/asset index boundaries, recording repost reconciliation
and refreshed-date handling:

```text
$ .venv/bin/python tests/audit_repo.py
required_bash_files: 16
files_or_blobs_scanned: 163
historical_blobs_scanned: 38
findings: []
$ /bin/bash tests/test_components.sh
12 tests passed.
$ .venv/bin/python -m pytest -q
78 passed in 213.73s (0:03:33)
$ .venv/bin/python -m pytest tests/test_collection.py::test_identical_recording_repost_does_not_add_independent_item tests/test_collection.py::test_refreshed_date_does_not_make_unchanged_written_content_new -q
2 passed in 2.67s
$ .venv/bin/python -m pytest tests/test_audit_contracts.py -q
22 passed in 9.39s
$ .venv/bin/python -m pytest tests/test_collection.py tests/test_publishing.py::test_package_standalone_and_preserved_links tests/test_publishing.py::test_normal_entry_calls_collection_and_real_series -q
13 passed in 41.23s
$ .venv/bin/python -m pytest tests/test_audit_contracts.py::test_model_response_metadata_cannot_persist_active_credential tests/test_audit_contracts.py::test_publication_link_cannot_contain_credential -q
2 passed in 0.44s
```

These are overlapping regression runs, not additive independent test counts.
The whole suite ran before the final small safeguards; targeted tests verified
those changed paths afterwards. Test subprocesses use macOS /bin/bash. The secret
scan does not print matched values or read the canonical index outside store.sh;
unknown credential formats and installed dependencies remain outside its claim.

## Review, packaging and reporting phase

All approvals in these tests are explicitly SIMULATED, isolated example-mode
fixtures. No student approval, paid model request, video rendering or publication
was performed. Actual commands and output:

```text
$ .venv/bin/python -m pytest tests/test_publishing.py tests/test_editorial.py tests/test_orchestration.py -q
44 passed in 214.20s (0:03:34)
$ .venv/bin/python -m pytest tests/test_publishing.py -q
14 passed in 159.30s (0:02:39)
$ .venv/bin/python -m pytest tests/test_publishing.py::test_normal_entry_calls_collection_and_real_series -q
1 passed in 14.53s
$ .venv/bin/python -m pytest tests/test_publishing.py::test_review_rejects_altered_source_note_passage -q
1 passed in 10.99s
$ /bin/bash -n run.sh review/check_content.sh publishing/prepare_package.sh reporting/summarize_run.sh
[exit 0, no output]
```

The second invocation added tests for malformed/incomplete summaries and recovery
from a preceding failed review. The normal-entry test uses an explicitly fictional
collection handoff stub and the real series workflow; real collector/pipe behavior
is covered separately by the localhost integration tests. The localhost test server
required sandbox permission; the initial sandboxed attempt failed to bind, then all
five collection orchestration regression tests passed after permission.

```text
$ .venv/bin/python tests/dry_run_publishing.py
FICTIONAL evidence and SIMULATED approvals; no API calls or publication.
$ bash review/check_content.sh runs/fictional-series
{"review_id":"8b4f5ba18f709d3a2d02fd07ba49a68d8d0bd4b58a125ae52c6acb6a1796770f","passed":true}
$ bash reporting/summarize_run.sh runs/fictional-series
{"status":"awaiting_review","counts":{"accepted":3,"articles":3,"changed":null,"deferred":3,"discovered":null,"eligible":12,"excluded":null,"extracted":12,"new":null,"rejected":6,"unchanged":null,"video_scripts":3}}
$ bash publishing/prepare_package.sh runs/fictional-series
exit=0; package assets=9
$ bash run.sh --package runs/fictional-series
exit=0; status=ready_for_production; publication links preserved=True
$ [modify articles/01.md] then bash publishing/prepare_package.sh runs/fictional-series
exit=1; Stale review: reviewed inputs changed; rerun checks and obtain matching approval
$ bash run.sh --package runs/fictional-series (stale approval)
exit=1; status=failed
Run directory: runs/fictional-series
Stale approval: review_id differs from current reviewed inputs
Production package requires current passing checks and matching human approval
```

Retained fictional demonstration:
`/private/var/folders/j3/n_3mwdz5715fhtn16419kl0m0000gn/T/ps04-publication-fixture-b0asn6or/repo/runs/fictional-series`.
It contains package/MANUAL_STEPS.md, manifest.json, publication_links.json and three
files each under articles/, video_scripts/, source_notes/. Its current summary is
failed after the deliberate stale-approval test; the preceding approved fixture
package and simulated entered link are retained. Production snapshots/drafts stay
byte-identical during --package, and no collector or model-generation calls run.

Tests also verify missing/revise/invalid-timestamp approval rejection, malformed
publication links exiting 2 without replacing the package, source/brief/script/date
fingerprint changes, distinct coverage after recording-copy reconciliation, null
unmeasured counts versus measured zero, known-cost subtotals with unknown costs,
and published links reported separately from production readiness.

## Editorial/content phase

Actual commands executed with the fixture provider (no model API calls):

```bash
.venv/bin/python tests/dry_run_editorial.py --stage select_items
.venv/bin/python tests/dry_run_editorial.py --stage create_briefs
.venv/bin/python tests/dry_run_editorial.py --stage write_articles
.venv/bin/python tests/dry_run_editorial.py --stage write_video_scripts
.venv/bin/python tests/dry_run_editorial.py
.venv/bin/python -m pytest -q tests/test_editorial.py
```

The stage driver printed these independently runnable commands against its own
prepared example run:

```bash
bash editorial/select_items.sh runs/fictional-series < eligible.jsonl
bash editorial/create_briefs.sh runs/fictional-series < decisions.jsonl
bash content/write_articles.sh runs/fictional-series < briefs.jsonl
bash content/write_video_scripts.sh runs/fictional-series < briefs.jsonl
bash workflows/create_series.sh runs/fictional-series
```

The driver's displayed input basenames refer to files in runs/fictional-series;
the subprocess actually supplies those saved files on stdin. All four stages
exited 0: 12 decisions, exactly three briefs (01/02/03), three article manifests,
and three script manifests/files. A representative Decision output was:

```json
{"decision":"accept","item_id":"fixture:00","piece_ids":["01","02","03"],"reason":"FICTIONAL canned decision for contract testing","version_id":"f52fee482d80f949f6a538c382b68a2b42d1ffb60047a78ce52c0339418dd178"}
```

Representative article/script manifests were:

```json
{"claim_ids":["01-c1"],"path":"runs/fictional-series/articles/01.md","piece_id":"01"}
{"claim_ids":["01-c1"],"path":"runs/fictional-series/video_scripts/01.md","piece_id":"01"}
```

Actual final workflow output:

```text
exit=0
{
  "status": "awaiting_review",
  "exit_code": 0,
  "human_review_required": true
}
```

The mechanical review passed with human-review and approximate length warnings;
the deliberately short mock drafts are not publication-ready. No approval file
was generated. Exact retained run, including rendered messages, raw model outputs,
receipts, briefs, drafts/scripts, source notes and review:

`/private/var/folders/j3/n_3mwdz5715fhtn16419kl0m0000gn/T/ps04-editorial-fixture-buf8ndk1/repo/runs/fictional-series/`

Each model receipt reports FICTIONAL-model, measured stage/model duration,
100 synthetic input tokens, 50 synthetic output tokens, tokens_are_fixture=true,
actual API cost_usd=0 and simulated_cost_usd=0.000125 (fixture rates 0.5/1.5 per
million tokens). Those rates/counts are not claims about a real provider's bill.
The in-process HTTP mock separately verified 120/80 reported usage and a flat-rate
estimate of 0.00018, and verified no key/header value was persisted.

Actual test output:

```text
...........................                                              [100%]
27 passed in 55.96s
```

Tests cover schema/JSON failures, missing Decisions, wrong versions, invented
sources/quotes/segments, wrong brief count/IDs, insufficient accepted evidence
before model access (exit 1), unsupported content claims/quotes/markers, unchanged
older drafts after rejection, fixture/live safeguards, workflow stop/resume,
review fingerprints, unknown price handling, strict/JSON HTTP formats, and safe
token-cost accounting. Additional metadata permitted by the architecture remains
valid without changing required claim/reference semantics. No real model API was
contacted and no user topic settings, policy or prompts were rewritten.

## Collection orchestration phase

Actual commands:

```bash
.venv/bin/python -m pytest -q tests/test_orchestration.py tests/test_collection.py
.venv/bin/python tests/dry_run_collection.py
.venv/bin/python tests/dry_run_collection.py --simulate-failure
/bin/bash -n run.sh workflows/collect_sources.sh reporting/summarize_run.sh
git diff --check
```

Actual combined test output: `14 passed in 25.99s`. The five orchestration tests
prove standalone/resumed workflow behavior, exact snapshots and prior-run linkage,
partial source failures, invalid config receipts/summary, and actual pipe failure
status preservation without stale exclusion outputs. Bash syntax and diff checks
passed.

The dry driver executed this command in its isolated fixture repository:

```bash
bash run.sh --mode example --config-dir runs/fictional/config --prompts-dir fixture-prompts
```

Successful fixture run: exit 0; collector codes fetch_feeds=0, fetch_youtube=0,
fetch_podcasts=0; discovered=3, extracted=3, new=3, eligible=3, excluded=0.
Editorial counts remain null. `collection_status` is completed; pipeline_complete
is false. coverage_incomplete is true because three fictional items do not meet
the assignment quantity/independence minimums. This is not a publication run.

Retained successful run:

`/private/var/folders/j3/n_3mwdz5715fhtn16419kl0m0000gn/T/ps04-collection-dry-run-lavgdka6/repo/runs/20261014T181117Z-826fb92e54d2/`

Actual tree (receipt names collapsed for readability):

```text
runs/20261014T181117Z-826fb92e54d2/
├── candidates/
│   ├── feeds.jsonl
│   ├── podcasts.jsonl
│   └── youtube.jsonl
├── config/
│   ├── editorial_policy.md
│   ├── project.json
│   └── sources.json
├── logs/ (24 unique receipt files)
├── prompts/
│   ├── create_briefs.md
│   ├── select_items.md
│   ├── write_articles.md
│   └── write_video_scripts.md
├── candidates.jsonl
├── changes.jsonl
├── collection_stages.jsonl
├── collection_status.json
├── corpus.jsonl
├── eligible.jsonl
├── exclusions.jsonl
├── items.jsonl
├── run.json
└── summary.json
```

The simulated failure run exited 1 and reported collection_status=incomplete,
collector codes fetch_feeds=1, fetch_youtube=0, fetch_podcasts=0. It still retained
three valid Candidates, three Items/Changes, and three eligible items. The failed
feed's receipt contains the actual retrieval error and its valid partial output
count. Retained failure run:

`/private/var/folders/j3/n_3mwdz5715fhtn16419kl0m0000gn/T/ps04-collection-dry-run-kxhvljqm/repo/runs/20261014T181322Z-64ccbfb24152/`

No actual topic config, policy or prompts were edited; test placeholders are under
tests/fixtures/orchestration. Only isolated copies of store.sh accessed indexes.
The reporting scaffold keeps summary logic out of run.sh and explicitly reports
the editorial/review stages as not run.

## Commands actually run

```bash
PATH="$PWD/.venv/bin:$PATH" /bin/bash tests/test_components.sh
.venv/bin/python -m pytest -q tests/test_collection.py
HF_HOME=/private/tmp/ps04-whisper-diagnostic .venv/bin/python tests/run_live_smoke.py
/bin/bash -n lib/common.sh collectors/fetch_feeds.sh collectors/fetch_youtube.sh collectors/fetch_podcasts.sh processing/extract_content.sh data/store.sh tests/test_components.sh
.venv/bin/python -m pip check
git diff --check
```

Offline tests required permission to bind their localhost HTTP fixture server in
this sandbox. Live tests ran with network access and downloaded original media
and the base model into temporary locations. No fixtures were put in a live store.

## Offline output

```text
12 tests passed.
.........                                                                [100%]
9 passed in 15.53s
No broken requirements found.
```

Bash syntax and diff checks exited 0. The 12 prior tests cover store replay,
retrieval-only updates, deterministic versions, historical/missing get, date
endpoints/reasons, malformed input, empty successes, and unique receipts.
The nine collection tests cover:

- Each of feed, YouTube and podcast collectors/extraction standalone and through
  a real pipe; a failed source retains one valid Candidate and returns 1.
- Full article retrieval beyond feed summaries and podcast audio enclosure URLs.
- Native timed transcripts, ASR fallback with base/CPU/int8, content reuse,
  changed transcript versions and immutable earlier assets.
- Duration guards, invalid arguments/malformed streams, bounded extraction and
  valid partial Item output despite an inaccessible item.
- Rolling caption cleanup and refusal to invent timestamps for untimed text;
  fallback also succeeds for malformed XML and captions exceeding media duration.
- Reciprocal producer-link reconciliation, plus later reconciliation of two
  previously stored identities with original version-pinned get still available.

## Live standalone and piped commands

The live script printed and executed these inside its isolated repository:

```bash
RUN_DIR=runs/live-smoke /bin/bash data/store.sh init
/bin/bash collectors/fetch_youtube.sh runs/live-smoke --max-items 1 --max-duration-minutes 6
/bin/bash processing/extract_content.sh runs/live-smoke --max-items 1 --max-duration-minutes 6
/bin/bash data/store.sh upsert runs/live-smoke
set -o pipefail
bash collectors/fetch_youtube.sh runs/live-smoke --max-items 1 --max-duration-minutes 6 | bash processing/extract_content.sh runs/live-smoke --max-items 1 --max-duration-minutes 6
/bin/bash collectors/fetch_podcasts.sh runs/live-smoke --max-items 1 --max-duration-minutes 6
/bin/bash processing/extract_content.sh runs/live-smoke --max-items 1 --max-duration-minutes 6
/bin/bash data/store.sh upsert runs/live-smoke
bash collectors/fetch_podcasts.sh runs/live-smoke --max-items 1 --max-duration-minutes 6 | bash processing/extract_content.sh runs/live-smoke --max-items 1 --max-duration-minutes 6
```

Standalone extraction/upsert received the saved preceding stage stdout on stdin.
All of these commands exited 0 in the successful smoke run. Source snapshot:
YouTube `https://www.youtube.com/watch?v=jNQXAC9IVRw`; podcast RSS
`https://feeds.npr.org/500005/podcast.xml`. The latter discovered the episode
“1pm ET, October 14 | The latest headlines from NPR.”

Actual compact Item output from standalone extraction:

```json
{"item_id":"youtube:jNQXAC9IVRw","kind":"youtube","title":"Me at the zoo","duration_seconds":19.021,"transcript_method":"native_captions","transcript_model":null,"version_id":"2cc98129651d51191e4333e71b12fb91969457ea48953a3a54ade811bbb8729c"}
{"item_id":"podcast:203de4a1ca55e57b8886550b9b1d8c6273203e9e73e26c6e4e114eca71cc100d","kind":"podcast","title":"1pm ET, October 14 | The latest headlines from NPR","duration_seconds":286.6155,"transcript_method":"faster_whisper","transcript_model":"base","version_id":"6b0a96ef74f74d2fde6877947daac52a7f09a6e281a8824d71618088b5fc6063"}
```

Each piped replay produced the same version ID as its standalone extraction.
NPR's feed duration was 280 seconds; ffprobe measured the downloaded enclosure at
286.6155 seconds. The safeguard used the measured duration before transcription.
The difference is retained honestly rather than replacing measured duration with
feed metadata. ASR provenance records cpu and int8, and native provenance has a
null model. Both original media and timestamped segments were retained.

Full records, exact commands/stdout/stderr (`smoke_results.json`), receipts,
content-addressed assets and original media remain in:

`/private/var/folders/j3/n_3mwdz5715fhtn16419kl0m0000gn/T/ps04-live-smoke-n5rbbwv0/`

The script prints a fresh retained path when rerun. It never writes a database
into the project repository. Only each isolated copy of store.sh opens its index.

## Failures found and repaired during development

An initial asset-path handling bug made extraction return 1 after discovery;
using absolute target paths before generating repository-relative records fixed
it. The real podcast fallback then exposed PyAV 19 incompatibility with
faster-whisper's `metadata_errors` argument. Requirements now pin tested PyAV
16.1.0/faster-whisper 1.2.1, and the subsequent real podcast test passed. ASR tool
failures are now reported as operational exit 1. The older fixture-copy test was
updated to name its five files explicitly after nested fixture directories were
added. Earlier failed smoke runs/receipts were preserved in separate temporary
repositories; they were not rewritten as successful tests.

## Live collection follow-up: 2026-10-15 UTC

No paid model request was made during these checks. The Codex process did not
have MODEL_API_KEY or OPENAI_API_KEY; credentials exported in an external terminal
are not inherited by an already running application.

The first sandboxed fixture run could not bind its local HTTP server (8 passed,
15 setup errors). Repeating with permission for local sockets produced:

```text
.venv/bin/python -m pytest tests/test_topic_config.py tests/test_collection.py tests/test_orchestration.py -q
23 passed in 32.74s
```

A real GitHub RSS feed exposed an overly broad byte search: HTML document
declaration examples inside CDATA were mistaken for XML DTD declarations.
collectors/support.py now rejects actual DTDs through the XML parser's doctype
callback. Four explicitly fictional regression cases cover CDATA/escaped text
and real external/internal DTDs. After this repair:

```text
.venv/bin/python -m pytest tests/test_feed_xml.py tests/test_topic_config.py -q
11 passed in 0.17s
.venv/bin/python -m pytest tests/test_feed_xml.py tests/test_collection.py tests/test_orchestration.py -q
20 passed in 31.78s
```

Standalone real RSS retry against the run snapshot:

```text
bash collectors/fetch_feeds.sh runs/20261015T033503Z-f6539b3bc938
exit_code: 0
candidates: 18
publishers: ['cloudflare', 'metr', 'microsoft-github', 'simon-willison']
```

The retry used MAX_DURATION_MINUTES=40 and the activated project virtualenv;
stdout is retained separately as diagnostics/feeds-after-xml-fix.jsonl in that
run. It does not rewrite the earlier failed collector receipt or, by itself,
establish a repaired end-to-end collection workflow.

The read-only repository audit reported 16 required Bash entry points, 310
files/blobs scanned, 38 historical blobs scanned and findings: []. This is a
pattern-based scan with the limitations printed by tests/audit_repo.py, not proof
that every possible credential format is absent.

Complete collection attempt (virtualenv active, CPU/int8/base fallback):

```text
MAX_DURATION_MINUTES=40 bash run.sh --collection-only
RUN_DIR=runs/20261015T033503Z-f6539b3bc938
exit_code: 1
elapsed_seconds: 472.851913
discovered: 22
extracted: 22
eligible: 22
excluded: 0
new: 20
unchanged: 2
source_coverage: feed=15, youtube=4, podcast=3, publishers=7
collector_exit_codes: fetch_feeds=1, fetch_youtube=0, fetch_podcasts=0
```

The GitHub failure occurred before the parser fix. The independent retry above
then succeeded. This run remains a failed collection attempt, not an end-to-end
publication run. Two earlier written items from the bounded smoke run explain
the two unchanged records. Seven media transcripts and original downloads are
retained. No editorial model call was attempted.

An additional store-interface replay of the saved items returned:

```json
{"input_count":22,"new":0,"changed":0,"unchanged":22,"latest_item_version_pairs_unchanged":true}
```

The replay queried list before/after and used upsert; no audit helper opened the
canonical index. Full output is in diagnostics/replay-result.json and
diagnostics/replay-changes.jsonl in that run. This is a labeled saved-input replay,
not a second live run or proof of new source discovery.

After the user supplied a local .env file, a temporary launcher parsed only its
credential assignments (no shell evaluation), loaded the key into process
environment and ran an actual structured OpenAI connection test:

```text
Connection test HTTP status: 200
Structured JSON connection test: passed
Connection test tokens: {"prompt_tokens": 42, "completion_tokens": 12}
Run directory: runs/20261015T035002Z-e05bbed2241b
```

The connection probe used gpt-5.4-mini and a strict boolean-object JSON schema.
At configured standard prices its estimated cost is $0.0000855; this separate
probe is not included in pipeline invocation receipts. The full run was launched
with MAX_DURATION_MINUTES=40 and the same CPU/int8/base transcription defaults.
.env was confirmed untracked, added to .gitignore and restricted to mode 0600.
Its contents are never included in these records; the earlier clean-workspace
secret scan predates this explicitly user-supplied local file.

Additional offline generation/review/package regressions:

```text
.venv/bin/python -m pytest tests/test_editorial.py tests/test_publishing.py -q
43 passed in 264.26s (0:04:24)
```

The first real brief response was rejected with exit 2 for using unassigned or
unknown exact source versions; further inspection also found out-of-range media
segment IDs and one inexact written quote. No drafts were emitted from it. The
response, rendered request and $0.336339 running model-cost subtotal were retained.
The owning brief component now constrains the request schema to per-piece literal
item/version pairs and actual source segment IDs; post-response validation remains
in force. This is a technical generation constraint, not a claimed human policy
revision or approval. Targeted verification after the final repair:

```text
.venv/bin/python -m pytest tests/test_brief_constraints.py tests/test_editorial.py::test_briefs_reject_invented_evidence_and_bad_shapes tests/test_editorial.py::test_all_stages_and_workflow_with_verified_refs -q
9 passed in 19.49s
```

The formal run's collection workflow was then resumed independently. All three
collectors, extraction, upsert, list and filter returned exit 0. Its earlier
artifacts remain in attempts/ and earlier failure receipts remain in logs/.
This demonstrates real failure recovery; it is not another calendar-day run.

Further live execution rejected a mistyped Cloudflare item ID during selection,
and a long podcast's ASR tail exceeded the measured recording endpoint. Both
failures were retained without publishing outputs. Selection now constrains the
literal item/version pairs and response count; the usual completeness/duplicate
checks still run. ASR uses the measured endpoint to bound a crossing final segment
and removes segments starting beyond the recording, recording both counts in
transcription.timestamp_bounds and receipt warnings. Native-caption fallback
behavior is unchanged. YouTube format selection now requests audio at metadata
resolution too, avoiding unnecessary full-video downloads during extraction.

Verified fixture checks after these changes:

```text
.venv/bin/python -m pytest tests/test_selection_constraints.py tests/test_editorial.py::test_selection_rejects_malformed_output_and_preserves_usage tests/test_editorial.py::test_all_stages_and_workflow_with_verified_refs -q
6 passed in 15.34s
.venv/bin/python -m pytest tests/test_asr_bounds.py tests/test_collection.py::test_reuse_changed_assets_and_cpu_fallback tests/test_collection.py::test_duration_limit_and_malformed_input -q
4 passed in 5.30s
.venv/bin/python -m pytest tests/test_asr_bounds.py tests/test_collection.py::test_reuse_changed_assets_and_cpu_fallback tests/test_collection.py::test_collectors_standalone_partial_failure_and_pipe -q
7 passed in 9.11s
.venv/bin/python -m pytest tests/test_podcast_selection.py tests/test_topic_config.py tests/test_collection.py::test_podcast_episode_allowlist_standalone_and_partial_failure -q
14 passed in 1.23s
```

The episode allowlist selects only the configured native GUIDs; a missing GUID
produces an operational failure while keeping valid partial candidates. Invalid
allowlists are configuration errors. Root source configuration now selects two
specific HTML All The Things episodes, with provenance and limitations recorded
in SOURCE_NOTES.md; the new run snapshot is runs/20261015T040201Z-6f8029259331/.
