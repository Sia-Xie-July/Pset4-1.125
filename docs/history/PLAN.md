# Historical intelligence pipeline implementation plan

Status: proposed; awaiting student approval. No implementation is authorized by this document. Read in full: `README.md`, `ARCHITECTURE.md`, and `SUBMISSION.md`. `ARCHITECTURE.md` governs interfaces and behavior. This plan preserves all 16 entry points and their boundaries. No editorial configuration, prompts, or course documents are changed.

## 1. Component contracts and helper choices

Every Bash file will have a Bash shebang and `set -euo pipefail`. Every invocation will source the small receipt helper described below. Python helpers belong to individual components; there will be no central pipeline application. The table's helper column excludes the common receipt utility. `R` means the repository-relative run directory. All stage commands take `R` first, except the entry point and documented store subcommands.

Exit convention **E**: `0` completed; `1` operational failure or incomplete collection; `2` invalid arguments/configuration/malformed input. A successful empty search returns `0`. Data goes to stdout; diagnostics go to stderr. File outputs below are relative to `R` unless explicitly stated.

| Bash file | Responsibility | Inputs | Stdout and saved outputs | Exit codes | Helper language/tools |
| --- | --- | --- | --- | --- | --- |
| `run.sh` | Establish run, snapshots, store initialization; coordinate workflows and final reporting; package existing run when requested | No args for live run; `--package R`; user config and prompts | Summary JSON; `run.json`, `config/`, `prompts/`, `summary.json`; downstream artifacts via components | E; blocking review/requirements return 1; successful normal run awaits review | Bash with jq for metadata/config validation; no substantive helper |
| `workflows/collect_sources.sh` | Sequence collectors, extraction, upsert, export, filtering; preserve partial failure | `R`, snapshotted config | Saved `candidates/{feeds,youtube,podcasts}.jsonl`, `candidates.jsonl`, `items.jsonl`, `changes.jsonl`, `corpus.jsonl`, `eligible.jsonl`, `exclusions.jsonl`; no extra stdout stream required | E; any unresolved collection failure remains 1 | Bash only; jq for stream validation |
| `workflows/create_series.sh` | Sequence selection, briefs, both generators, review | `R`, saved eligible evidence and snapshots | `decisions.jsonl`, `briefs.jsonl`, `articles.jsonl`, `video_scripts.jsonl`, `review.json`; no extra stdout stream required | E; inspect review.passed, return 1 on blocking result | Bash only |
| `collectors/fetch_feeds.sh` | Discover substantive written articles and stable source metadata | `R`; configured feed sources | Candidate JSONL | E; retain valid partial records on failure | Python: HTTP and feed parsing |
| `collectors/fetch_youtube.sh` | Discover video metadata/native IDs | `R`; configured channels, playlists, videos | Candidate JSONL | E; retain valid partial records on failure | Python adapter around yt-dlp |
| `collectors/fetch_podcasts.sh` | Discover episodes, GUIDs, audio enclosures | `R`; configured podcast feeds | Candidate JSONL | E; retain valid partial records on failure | Python: HTTP and feed parsing |
| `processing/extract_content.sh` | Fetch substantive text/media; obtain timestamped transcripts; reuse verified unchanged extraction | `R`; Candidate JSONL stdin; store queries | Item JSONL; immutable downloads in `data/media/`, text and segment assets in `data/assets/` | E; inaccessible/unprocessable items reported and stage incomplete | Python; article extraction, yt-dlp, ffmpeg, transcription adapter |
| `processing/filter_items.sh` | Mechanical date eligibility | `R`; Item JSONL stdin; run as-of date | Eligible Item JSONL; `exclusions.jsonl` | E; date exclusions are completed assessments, not failures | Python standard library |
| `data/store.sh` | Exclusive evidence-index access, identity, deduplication, version history | `init`; `upsert R` + Item JSONL stdin; `list`; `get ITEM_ID [VERSION_ID]` | init: no records; upsert: ordered Change JSONL; list: latest Item per identity; get: matching Item | E; absent get returns 1 | Embedded Python with sqlite3, hashlib, json inside store.sh; no other file opens `data/evidence/` |
| `editorial/select_items.sh` | AI policy decisions, one per eligible item | `R`; eligible Item JSONL stdin; policy/prompt snapshots | Decision JSONL | E; invalid model output cannot become successful decisions | Component-local Python model adapter and validation |
| `editorial/create_briefs.sh` | Three distinct arguments with supported claims, synthesis, limitations | `R`; Decision JSONL stdin; eligible evidence/project/policy/prompt snapshots | Exactly three Brief records (`01`, `02`, `03`) | E; insufficient evidence returns 1 | Component-local Python model adapter and validation |
| `content/write_articles.sh` | Articles grounded in briefs and exact evidence versions | `R`; Brief JSONL stdin; referenced evidence and snapshots | Manifest JSONL; `articles/01.md`, `02.md`, `03.md` | E | Component-local Python model adapter and validation |
| `content/write_video_scripts.sh` | Narration, visual directions, references from same briefs | `R`; Brief JSONL stdin; referenced evidence and snapshots | Manifest JSONL; `video_scripts/01.md`, `02.md`, `03.md` | E | Component-local Python model adapter and validation |
| `review/check_content.sh` | Assess artifacts, references, freshness, coverage, consistency; fingerprint assessed inputs | `R`; briefs, manifests, drafts/scripts, exact evidence versions | One review JSON object for `review.json` | 0 when assessment completes even if passed=false; 1 cannot assess; 2 invalid input/config | Python; deterministic checks, explicit human-judgment warnings |
| `publishing/prepare_package.sh` | Verify current passing review and student approval; assemble production handoff | `R`; current artifacts, `review.json`, `approval.json` | Package manifest JSON; `package/` articles, scripts, source notes, `manifest.json`, `publication_links.json` | E; absent/stale approval or changed reviewed inputs returns 1 | Python for verified copying, source notes, manifest |
| `reporting/summarize_run.sh` | Summarize completed and incomplete runs without inventing results | `R`; saved artifacts and receipts | Summary JSON for `summary.json` | E; an incomplete run can be successfully summarized with exit 0 and status failed | Python standard library |

Coordination will use at least one real pipe, such as an input reader piping saved candidates into extraction. Each producer's artifacts are saved before the dependent stage runs. Pipeline statuses are explicitly captured with `pipefail`/`PIPESTATUS`; expected child failures are handled without losing the final summary to `set -e`. Workflows never implement collection, persistence, reasoning, or rendering.

## 2. Exact shared record schemas

The following is schema notation, not executable code or example evidence. Each named record is an object; all listed fields are required; additional fields are permitted by the architecture. `string[]` means an array of strings; `T[]` means an array of records of type T. Union alternatives are separated with `|`. Prose fields, including `limitations` and `synthesis`, are strings, not arrays. Timestamps are ISO 8601 UTC. Paths are repository-relative.

### Candidate

```text
{
  item_id: string,
  source_id: string,
  publisher_id: string,
  kind: "feed" | "youtube" | "podcast",
  title: string,
  url: string,
  published_at: string | null,
  retrieved_at: string,
  media_url: string | null
}
```

`published_at` is source publication time, separate from retrieval time; unknown publication dates are null. `media_url` is null when no direct media URL is available.

### Item

```text
{
  item_id: string,
  source_id: string,
  publisher_id: string,
  kind: "feed" | "youtube" | "podcast",
  title: string,
  url: string,
  published_at: string | null,
  retrieved_at: string,
  media_url: string | null,
  version_id: string,
  text_path: string | null,
  segments_path: string | null
}
```

Absent optional asset paths may be null. Written material has `segments_path: null`; audio/video must have a segment file. Proposed extraction always retains substantive text at `text_path` as well, so a missing text path cannot masquerade as usable written evidence. Every referenced asset must resolve from the repository root.

### Segment (Transcript segment)

```text
{
  segment_id: string,
  start_seconds: number,
  end_seconds: number,
  text: string
}
```

Segments are saved as a **JSON array**, not JSONL, at `segments_path`. Evidence points to a segment within an exact item version. Proposed validation checks nonnegative, ordered time intervals and unique IDs within a segment file.

### Exclusion

```text
{
  item_id: string,
  version_id: string,
  reason: string,
  detail: string
}
```

Required reasons include `outside_window`, `unknown_date`, `future_date`, `invalid_date`; the architecture does not declare this an exhaustive enum. A malformed timestamp string yields `invalid_date`; a structurally malformed record yields exit 2.

### Change

```text
{
  item_id: string,
  version_id: string,
  change: "new" | "changed" | "unchanged"
}
```

### Decision

```text
{
  item_id: string,
  version_id: string,
  decision: "accept" | "reject" | "defer",
  reason: string,
  piece_ids: string[]
}
```

Rejected/deferred decisions have `piece_ids: []`. Intended pieces use `01`, `02`, `03`. Exactly one decision is produced per eligible item; mechanically excluded items are recorded separately.

### Brief

```text
{
  piece_id: string,
  title: string,
  question: string,
  argument: string,
  synthesis: string,
  limitations: string,
  claims: Claim[]
}
```

Brief generation produces exactly the three IDs `01`, `02`, `03`. Inference reasoning belongs in `synthesis`.

### Claim

```text
{
  claim_id: string,
  statement: string,
  type: "reported_fact" | "source_claim" | "inference",
  evidence: EvidenceRef[]
}
```

Every claim has at least one evidence reference. Inspectable claim IDs such as `01-c1` appear in both drafts and scripts.

### Evidence ref (Evidence reference)

```text
{
  item_id: string,
  version_id: string,
  locator: { type: "text", quote: string }
           | { type: "segment", segment_id: string }
}
```

A written quote must match an exact retained passage. A media locator must resolve to a timestamped segment, not a title or general homepage. Citations pin versions rather than following “latest.”

### Manifest (Content manifest)

```text
{
  piece_id: string,
  path: string,
  claim_ids: string[]
}
```

Article and script manifests use this schema in separate JSONL files. The publication package's `manifest.json` is a separate JSON document listing assets and piece IDs; it is not this JSONL content manifest.

Candidate, Item, Exclusion, Change, Decision, Brief, and Manifest streams use one object per JSONL line. Claims and evidence refs are nested objects, not additional required standalone streams. Run metadata, review, approval, summary, package manifests, and transcript arrays retain their documented JSON formats.

## 3. Storage, stable identities, and replay

Use SQLite at `data/evidence/evidence.sqlite3`. Only `data/store.sh` opens, reads, writes, or inspects this directory. Its embedded Python is part of that component; other Python files never access the database. Retained assets remain outside it in `data/assets/` and `data/media/`.

Proposed tables:

- **items**: canonical `item_id` primary key, latest-version pointer, first-seen run. Native IDs or canonical URLs anchor identity; titles and retrieval dates never do.
- **versions**: composite primary key `(item_id, version_id)`, immutable normalized Item JSON, canonical hash payload, content digests, first-seen run. Foreign keys prevent dangling current-version pointers.
- **observations**: unique invocation ID and input ordinal, run ID, canonical item/version, original route/source metadata, actual retrieved time, change classification. Replays add observation history, not duplicate evidence versions.
- **aliases**: unique native/canonical route identity to canonical item ID, provenance and matching basis. Explicit identity redirects preserve resolution of previously cited IDs if a later reconciliation joins two known items.
- **runs**: observed run metadata sufficient to associate versions and observations with runs, without credentials.

`init` is idempotent and never clears existing records. Use transactions and uniqueness constraints, a bounded busy timeout, and deterministic input ordering. Validate input and referenced assets before committing an ingestion; emit changes only after successful commit. Malformed batches return 2 without partially committed versions. Upsert emits one Change per input in input order, including duplicate inputs.

### Proposed version_id computation (v1)

Document the exact algorithm in the `store.sh` header before implementing dependent extraction. Compute lowercase hexadecimal SHA-256 of UTF-8 canonical JSON with sorted keys, compact separators, Unicode preserved, finite numbers only. The hash payload contains:

- A fixed versioning-algorithm tag, `evidence-v1`.
- Canonical `item_id`, `source_id`, `publisher_id`, `kind`, `title`, canonical public `url`, and verified `published_at`.
- `text_sha256`: digest of retained normalized UTF-8 text, or null when absent.
- `segments_sha256`: digest of canonical JSON for the ordered segment array, including IDs, start/end times, and exact text, or null when absent.

Text normalization is limited to UTF-8 decoding, Unicode NFC, and CRLF/CR to LF; do not collapse substantive whitespace or paraphrase content. Segment numeric serialization must be consistent between extraction and storage. Canonical public URLs remove only recognized tracking parameters; do not remove identity-bearing query parameters.

Exclude `retrieved_at`, run/invocation IDs, filesystem paths, costs, cache validators, download expiry tokens, and transient `media_url` transport locations. A media URL change alone does not establish changed evidence. Canonical source attribution changes, corrected dates/titles, transcript corrections, or passage changes do change the hash. Newly learned discovery routes are observations/aliases rather than changes to the canonical attribution.

Extraction computes the proposed digest using a focused pure hashing utility owned under `data/`; the utility never accesses `data/evidence/`. Store recomputes and validates incoming IDs from assets rather than trusting callers. This helper is not shared pipeline logic. Content-addressed asset filenames are independent of run timestamps, and referenced files are never overwritten.

Upsert classification: first identity is `new`; a different substantive version is `changed`; identical content and metadata are `unchanged`. Repeated identical records in one batch are unchanged after their first occurrence. Returning to an already stored historical version reuses its version row; if it differs from the current latest pointer, classify the transition as changed and retain the observation. Retrieval-only updates create observations without new versions. `list` exports exactly one latest canonical item; `get` can retrieve every retained version. Last retrieval information may be exposed from observations without mutating the version's substantive payload.

Extraction queries `get`/`list`, never the database. Use cached immutable native-media results or verified HTTP validators/content digests to avoid repeated transcription; record the basis for reuse. When change status cannot be established, refetch and compare rather than assuming unchanged. Freshness filtering always reruns against the new run date, even for cached evidence.

## 4. Reconciling YouTube and podcast copies

1. Collectors emit stable discovery identities: YouTube native video ID; podcast GUID scoped by its feed/source; written canonical URL. Preserve publisher and route metadata. Feed entries pointing to an episode are discovery routes, not additional substantive written evidence.
2. Extraction inspects explicit cross-links, producer episode IDs, canonical episode pages, and available media metadata. Same publisher, similar titles, or similar dates alone are insufficient proof. Transcript overlap/duration can flag a possible match; edits, inserted ads, and introductions make timestamps noninterchangeable.
3. Store owns durable reconciliation. Proposed optional record extensions carry route aliases and an auditable reconciliation basis; `get` accepts a known alias and `list` returns canonical identities plus these extensions. Required commands and record fields remain unchanged. Unresolved suspected copies are flagged for human reconciliation and block claims that minimum distinct-item coverage is satisfied.
4. For a confirmed recording, retain one canonical `item_id` and representative evidence route. Prefer an explicit producer episode identity when known initially; otherwise keep the first established stable ID rather than renaming it when another upload appears. Preserve all alternative URLs/native IDs in alias observations. Extraction uses store exports to reuse the representative transcript instead of creating a second item for a transport copy.
5. Keep timestamps tied to the exact retained recording/version. Never attach a podcast segment's offsets to a YouTube upload without verified alignment. Alternate recordings needing different offsets retain their own assets/provenance; citations use the representative route or an explicitly verified mapping.
6. If two existing identities are later confirmed duplicates, store records an alias/redirect and retains historical version resolution. Latest corpus and coverage contain one underlying item; old claim references remain resolvable. This merge requires explicit matching evidence, not an automatic title heuristic.
7. Use the verified original publication date of the underlying substantive material. A later upload of an old recording does not refresh eligibility. Unknown original dates remain null and are excluded; document date provenance without inventing an exact time when only date precision is available.

Coverage uses each underlying item once. A dual-platform recording cannot satisfy both a distinct YouTube item and a distinct podcast item. Keep one canonical kind for coverage and report alternative routes separately. Aim for at least two distinct written items, two distinct YouTube recordings, and two other distinct podcast recordings, within at least 12 items from six independent originating sources. Publisher identities also collapse syndicated/reposted routes; shared announcements do not become independent corroboration merely through repetition.

## 5. Shared receipts and failure handling

Propose `lib/receipt.sh`, sourced by all 16 scripts. It performs only invocation bookkeeping and JSON receipt writing (using jq), not domain work. It establishes invocation UUID, stage, UTC start time, counters, tools/models, cost metadata, and sanitized errors; registers EXIT and signal handling once; preserves the component's intended exit status; writes an atomic, uniquely named JSON receipt under `R/logs/`. Earlier receipts are never replaced.

Proposed receipt fields: `invocation_id`, `parent_invocation_id`, `stage`, `status`, `exit_code`, `input_count`, `output_count`, `started_at`, `finished_at`, `tools`, `models`, `cost_usd`, `cost_is_estimate`, `errors`. Counts are measured or null when not known; `cost_usd` is numeric or null. Known free/local execution must be distinguished from unavailable provider pricing. Review completion and its passed/failed assessment are recorded separately. Parent receipts do not duplicate children's billable cost.

The shell traps handle success, ordinary failure, and catchable interruption; SIGKILL/power loss cannot guarantee a final receipt. An initial receipt marked running may be created under a separate unique filename and linked to the terminal receipt, allowing reporting to recognize unfinished invocations without overwriting history. Summary counts terminal invocations once, not both lifecycle records.

**Store receipt context proposal:** preserve literal command forms `store.sh init`, `store.sh list`, and `store.sh get ITEM_ID [VERSION_ID]`; supply `RUN_DIR=...` in their environment. `upsert R` obtains it positionally. Workflows export this context; standalone documentation shows it explicitly. Missing context returns 2 with stderr. An invalid/missing/unwritable run directory cannot host a receipt; report that logging failure honestly. The entry point creates a diagnostic run context before validating live configuration where possible. This resolves an ambiguity in the architecture without adding required store positional arguments; approval is requested below.

Credentials are read only from environment variables. Never dump environments, secret-bearing headers, signed credential URLs, or provider request authorization into diagnostics, prompts, snapshots, or receipts. Save exact nonsecret configuration/prompt snapshots and actual rendered model instructions separately under the run's prompt artifacts. Reject secret-bearing configuration instead of silently claiming a redacted copy is exact.

Reporting reads saved records and receipts, not the evidence database. Null means unmeasured/not run; zero means measured empty. Report distinct evidence counts, raw observations/duplicates, incomplete coverage, failed stages, elapsed time, tools/models, known/estimated/unknown costs, and remaining manual work. Finalize workflow receipts before the summary; the entry-point receipt can finalize after summary emission, with entry elapsed/status taken from active run metadata so no circular summary dependency is required.

## 6. Dependencies, implementation sequence, and validation

Proposed dependency choices (installation and exact version locking occur only after approval): Bash, jq, Python 3 with sqlite3/JSON/hash/date/path standard libraries, yt-dlp for YouTube discovery/downloads, and ffmpeg/ffprobe for audio preparation and inspection. Python packages: requests for HTTP, feedparser for RSS/podcast discovery, trafilatura for substantive article text, and jsonschema for boundary validation. Use native timed captions when available and appropriate; proposed fallback is local faster-whisper with its model identity and settings recorded. A hosted transcription alternative and the text-model provider remain student decisions. Provider SDKs are added only once that choice is made. No current version, hardware performance, price, or compatibility is assumed verified by this plan.

Keep the dependency set small, pin tested versions, record actual tool/model versions in receipts, and document setup in `SUBMISSION.md` when implementation reaches documentation. Test models' timestamp output and transcription quality before using their passages as evidence. Local transcription may require a substantial model download and runtime; measure on the student's machine before selecting a model size.

Implement and demonstrate **one component or phase at a time**:

1. Approve contracts, technical choices, and unresolved questions. Prepare only clearly labeled example/replay test settings; student supplies real editorial configuration and prompts.
2. Add the small receipt helper and record validation/hash utilities. Demonstrate unique receipts and exit-code preservation without implementing pipeline domain logic in them.
3. Implement `data/store.sh`: init, upsert, list, get, version validation, aliases, transactions, replay behavior. Test new/changed/unchanged, retrieval-only replay, repeated input in one ingestion, absent get, and historical version retrieval.
4. Implement `processing/filter_items.sh`. Test D−29 and D inclusion, D−30 exclusion, future, unknown, invalid dates, and retained evidence aging out on a later run.
5. Implement collectors individually: feeds, YouTube, podcasts. For each, test success, genuine empty results, invalid configuration, and labeled simulated partial failure. Keep source discovery separate from substantive extraction.
6. Implement `processing/extract_content.sh`, one input type at a time. Verify full written content, real media retrieval, timestamped transcripts, unchanged cache reuse, immutable assets, cross-platform copies, and unresolved-match reporting.
7. Implement `workflows/collect_sources.sh` using those independently verified interfaces, a real pipe, preserved outputs, and explicit incomplete coverage.
8. Implement `editorial/select_items.sh`, then `editorial/create_briefs.sh`. Validate one decision per eligible item, rejection/defer arrays, exact evidence versions, three distinct pieces, supported claims, and loud failure when evidence is insufficient.
9. Implement article generation, then video-script generation from the same briefs. Preserve claim markers and audience-usable source notes; target 600–900 article words and 3–5 minute scripts.
10. Implement `review/check_content.sh`: required files and three pieces, exact quotes/segments, date window, source independence counts, at least three independent sources per piece, 12-item/six-source collection coverage, two distinct items per required input kind, and all three kinds contributing to the series. Check claim-ID consistency, warn about lengths and matters requiring human judgment, and fingerprint assessed drafts, scripts, briefs, manifests, exact referenced evidence/assets, and as-of date. Completed blocking assessment exits 0 with passed=false.
11. Implement `publishing/prepare_package.sh`: invoke/verify a current assessment even standalone, require matching student approval, reject stale evidence/drafts, assemble source notes and manual production instructions, and preserve entered publication links on identical repackaging.
12. Implement `workflows/create_series.sh`, then reporting, then `run.sh`. Verify final summaries on failures, successful `awaiting_review`, and approved `ready_for_production`. Packaging must leave evidence snapshots/drafts unchanged and never recollect or regenerate them.
13. Conduct two live runs on different actual UTC dates during the assignment week. Capture as-of once per run. Demonstrate replay without duplicate versions, new/changed material (or a labeled withheld-item replay), freshness, and failure/recovery. Review at least three accepted and three rejected/deferred items; student revises policy at least once, rerun with preserved before/after outputs, and record factual corrections.
14. Student supplies final human approval, renders videos with Google Vids or HeyGen, publishes three article/video pairs, verifies accessible links, and records the separate 4–6 minute technical demonstration. Complete `SUBMISSION.md` with setup, evidence locations, traceable claim example, both runs, review/policy changes, manual handoffs, and reflection.

After each implemented component, provide its standalone command, run it on explicitly labeled test input, show actual sample output and receipt, and explain its code before moving on. Tests will exercise contract behavior rather than mirror implementation. Fixtures never count as real collected evidence.

Planned standalone command patterns (not executable until implementation):

- Store: `RUN_DIR=runs/EXAMPLE bash data/store.sh init`; `bash data/store.sh upsert runs/EXAMPLE < runs/EXAMPLE/items.jsonl`; `RUN_DIR=runs/EXAMPLE bash data/store.sh list`; `RUN_DIR=runs/EXAMPLE bash data/store.sh get ITEM_ID VERSION_ID`.
- Collectors: `bash collectors/fetch_feeds.sh runs/EXAMPLE` (equivalently the other collectors).
- Stream stages: `bash processing/extract_content.sh runs/EXAMPLE < runs/EXAMPLE/candidates.jsonl`; the table defines equivalent inputs for filtering, selection, briefs, and content generators.
- Artifact stages: `bash review/check_content.sh runs/EXAMPLE`, `bash publishing/prepare_package.sh runs/EXAMPLE`, and `bash reporting/summarize_run.sh runs/EXAMPLE`.
- Workflows: `bash workflows/collect_sources.sh runs/EXAMPLE` and `bash workflows/create_series.sh runs/EXAMPLE` using prepared, labeled snapshots.
- Live entry: `bash run.sh`; approved production handoff: `bash run.sh --package runs/RUN_ID`.

## 7. Decisions needed from the student

Before real collection/editorial generation:

1. What are the publication name, narrow topic, audience/assumed knowledge, central recurring question, scope/exclusions, voice, and reason to return? You own `config/project.json`, `config/editorial_policy.md`, and all four prompt files; this plan does not authorize writing them.
2. Which real feeds, YouTube sources, and podcasts should be used, and which share an originating publisher? Please identify known episode/video mirrors. `config/sources.json` is currently empty. Source independence and missing perspectives require your judgment.
3. Which text-model provider/model and maximum run budget should be used? Which environment variable names will supply credentials? Should transcription use local faster-whisper or a hosted provider, and in which languages?
4. Do you approve the proposed SQLite/version-hash design, embedded store implementation, optional alias/provenance extensions, and `RUN_DIR` environment context for store init/list/get? These are implementation proposals, not additional architecture requirements.
5. For publication dates supplied only as a calendar date, approve retaining date precision/provenance in an extension and a documented UTC boundary representation, or require exclusion until a real timestamp can be verified. We must not present an invented source publication time as observed. Missing dates remain null regardless.

Before production/submission:

6. Google Vids or HeyGen? What narration/presentation preferences and access are available? Platform work remains a manual handoff unless separately requested.
7. What are the assignment-week dates and planned dates for the two live runs? Where should large media be retained, and are there repository size constraints? Source text/transcript assets needed to inspect citations must remain accessible.
8. Who should be named as reviewer, and what are the repository/publication account details for the final submission? Only you create the approve/revise decision after reviewing actual outputs; technical plan approval does not approve future publication content.

Approval gate: wait for explicit approval of this plan before implementing any component or installing dependencies. Editorial decisions can be supplied later as their dependent phases approach.
