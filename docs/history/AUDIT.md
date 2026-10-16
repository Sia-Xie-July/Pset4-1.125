# Historical architecture contract audit — 2026-10-14

Authority: [ARCHITECTURE.md](../../ARCHITECTURE.md), read in full, with assignment
requirements from [README.md](../../README.md). This audit covers the owned repository,
including untracked implementation files and hidden settings. It does not certify
installed third-party packages, external accounts, or the quality of an unwritten
publication. README.md and ARCHITECTURE.md were not edited.

**Subsequent topic-configuration update:** After the audit, the user explicitly
authorized filling the recommended topic, root configuration, policy and prompts,
and chose English articles/scripts with Chinese planning notes (later translated into English). Those fields are
now populated for Before the Merge. The configuration findings below are updated;
the earlier test results remain historical. Model API setup, real runs, human
review and publication were pending at that point. See PROJECT_BRIEF.md and NEXT_STEPS.md.

**2026-10-15 UTC follow-up:** Real collection retained 22 eligible items from
seven publisher groups. A GitHub RSS/CDATА parsing false positive was repaired
with four regression cases; its standalone retry produced 18 RSS candidates.
A 22-item saved-input replay produced zero new/changed items. OpenAI structured
connection testing subsequently passed (HTTP 200; 42 input/12 output tokens),
and a full run started at runs/20261015T035002Z-e05bbed2241b/. Historical pending
statements below describe the earlier audit, not proof this live run completed.
The user explicitly supplied a local .env file after the audit; it is not tracked,
is ignored by Git and has mode 0600. Its credential is loaded into process
environment without printing it. Therefore the earlier clean working-tree scan
does not assert that the current working directory contains no local secret.

**PASS** means the implementation requirement was verified by source inspection
and the cited check. **PARTIAL** means mechanics exist but a real-world
demonstration, editorial decision, or human judgment remains. **FAIL** means an
observed implementation defect. The defects listed below were fixed; no confirmed
implementation FAIL remains. Pending student work is listed explicitly, not
represented as fictional completion.

The original execution tests use isolated, labeled fictional fixtures. Simulated
approvals are not the student's approval. No paid requests were made during the
original audit; later live checks are recorded separately in TEST_RESULTS.md.

## Verification commands

Run from the repository root after setup. Each requirement below cites one or
more of these exact commands; prerequisites and outputs are described here.

- **V01 — static ownership, secret scan and Bash checks:**
  `.venv/bin/python tests/audit_repo.py`.
  Scans owned files, hidden settings, Git blobs/history and Git config without
  printing credential matches. Checks the 16 paths, shebangs, strict mode,
  `/bin/bash -n`, Bash 3.2 compatibility patterns and unauthorized SQLite imports.
- **V02 — full offline suite:** `.venv/bin/python -m pytest -q`.
  Local HTTP fixture servers require permission to bind localhost in the Codex
  sandbox. They do not access real sources or paid APIs.
- **V03 — store and filter standalone:** `/bin/bash tests/test_components.sh`.
  Tests init/upsert/list/get, replay, version history, UTC window, reasons,
  malformed input, argument errors and receipt uniqueness without reading SQLite.
- **V04 — collectors/extraction standalone and real pipes:**
  `.venv/bin/python -m pytest tests/test_collection.py -q`.
- **V05 — collection coordinator, metadata and failure summaries:**
  `.venv/bin/python -m pytest tests/test_orchestration.py -q`.
- **V06 — model stages, schemas and references:**
  `.venv/bin/python -m pytest tests/test_editorial.py -q`.
- **V07 — review, package and all summary statuses:**
  `.venv/bin/python -m pytest tests/test_publishing.py -q`.
- **V08 — audit regression checks, all 16 argument interfaces:**
  `.venv/bin/python -m pytest tests/test_audit_contracts.py -q`.
- **V09 — retained standalone demo:**
  `.venv/bin/python tests/dry_run_publishing.py`.
  Prints real component commands/results using fictional evidence and simulated
  approval, including stale rejection and preserved links.
- **V10 — inspect index-access sites:**
  `rg -n 'data/evidence|sqlite3|\.sqlite' lib collectors processing editorial content review publishing reporting run.sh run_setup.py workflows data/store.sh`.
  The matches in common.sh and records.py are exclusion guards; only store.sh
  opens the index. Tests query its interface and receipt counts.
- **V11 — editorial configuration completeness:**
  `wc -c config/* prompts/*.md` and
  `jq -e 'all(.publication_name,.topic,.audience,.central_question; type == "string" and length > 0)' config/project.json`, then
  `jq -e 'type == "array" and length > 0' config/sources.json`.
  These currently expose pending student configuration, not a successful live run.
- **V12 — actual submission specimens:**
  `rg --files runs data/assets` and `rg -n 'To complete|Add link|Add path|Add your' SUBMISSION.md`.
  Absent runtime directories are an honest missing-specimen result. External
  publication access must additionally be opened and checked by the student.
- **V13 — independent stage examples:**
  `.venv/bin/python tests/dry_run_editorial.py --stage select_items`, repeat with
  `create_briefs`, `write_articles`, `write_video_scripts`; and
  `.venv/bin/python tests/dry_run_collection.py`.
  Drivers retain isolated fictional run directories and print stdout specimens.
- **V14 — current real topic configuration and bounded discovery:**
  `.venv/bin/python -m pytest tests/test_topic_config.py -q`.
  Checks populated fields, three source kinds, declared publisher grouping,
  byte-exact config/prompt snapshots and positive per-source discovery limits.
  Discovery behavior tests use explicitly fictional inputs, not real evidence.

## Defects found and repaired

Each finding was **FAIL before repair / PASS after repair**:

- Persisted collector/enclosure/transcript URLs could contain credential query
  parameters; direct component snapshots did not consistently reject credential
  values. Fixed in [lib/records.py](../../lib/records.py),
  [collectors/support.py](../../collectors/support.py),
  [processing/extract_content.py](../../processing/extract_content.py), and
  [run_setup.py](../../run_setup.py). Active credential values and recognizable private
  keys/tokens are rejected before persistence, without printing values. **Verify V08**.
- Model payload/output and returned model metadata needed the same persistence
  guard. Fixed in [lib/model_provider.py](../../lib/model_provider.py); retained text and
  segments are checked in [data/versioning.py](../../data/versioning.py) and extraction.
  **Verify V06 and V08**. Transport headers remain environment-only.
- Missing retained assets were classified as exit 2 by extraction's outer handler.
  They now produce operational exit 1. File:
  [processing/extract_content.py](../../processing/extract_content.py). **Verify V08**.
- Absolute RUN_DIR could leak into the summary's run_dir field. It is normalized to
  a repository-relative path in [reporting/summarize_run.py](../../reporting/summarize_run.py).
  **Verify V08**.
- A caller could direct another component's receipt writes into data/evidence/.
  [lib/common.sh](../../lib/common.sh) now validates the receipt directory before writing,
  rejects directories outside the repo or inside the index, and rejects symlinks
  resolving there. Asset/media publishing uses the equivalent boundary guard in
  [processing/media.py](../../processing/media.py). **Verify V08 and V10**.
- An RSS link directly to YouTube could be mistaken for substantive written
  evidence. Extraction now rejects that discovery route with exit 1, rather than
  inflating written coverage. **Verify V08**.
- Exact recording bytes were only reconciled when publisher IDs matched, allowing
  a reposting endpoint to inflate independent evidence. Exact byte matches now
  reconcile even across declared publishers; reciprocal-link matching still
  requires the shared producer. File: extraction. **Verify V04**.
- A later advertised date could refresh unchanged previously retained content.
  Extraction retains the earlier verified publication date when normalized written
  content or original recording bytes are unchanged; invalid/unknown metadata is
  not invented. **Verify V04**.
- Publication-link validation allowed credential-bearing URLs. Packaging now uses
  the public-URL guard. Its receipt reports one output manifest and separately nine
  assets. File: [publishing/prepare_package.py](../../publishing/prepare_package.py).
  **Verify V07**.

## Architecture and running the completed project

- **PASS — all 16 exact required Bash paths remain implemented**, with separate
  responsibilities. Entry paths are listed in [tests/audit_repo.py](../../tests/audit_repo.py).
  **Verify V01 and V02**.
- **PASS — Bash entry points and coordination; focused owning helpers**.
  [run.sh](../../run.sh) and [workflows/](../../workflows/) delegate; collectors, extraction,
  store, editorial, content, review, publishing and reporting own their work.
  Shared lib modules cover boundaries, receipts, transport and reference checks;
  no shared application runs the complete pipeline. **Verify V01, V04–V08 and inspect those files**.
- **PASS — normal run collects, generates, checks, and stops awaiting_review**.
  [run.sh](../../run.sh), [workflows/create_series.sh](../../workflows/create_series.sh).
  **Verify V07**, especially `test_normal_entry_calls_collection_and_real_series`.
  That entry test isolates collection using a labeled handoff stub; real collection
  is tested separately with V04/V05, not claimed as a real 12-source live run.
- **PASS — --package reruns checks, packages matching approval and summarizes**,
  with no recollection or model regeneration. Files: run.sh and publishing helper.
  **Verify V07/V09**; the stale test compares drafts and snapshots byte for byte.
- **PARTIAL — provider and editorial choices remain the student's**.
  [EDITORIAL.md](../../EDITORIAL.md) describes configurable providers; the user has
  authorized the configured topic/audience/policy but has yet to configure the
  actual model service. **Verify V11/V12/V14**.

## Configuration and prompts

- **PASS — project.json contains four nonempty editorial strings**.
  Before the Merge now specifies its audience, question, scope, exclusions, language
  and reader-return rationale. **Verify V11/V14**.
- **PASS — actual sources array with source_id/publisher_id/kind/url**.
  Nine real entries across three kinds and eight declared producer groups are
  configured, with conservative affiliation notes and explicit discovery bounds.
  Actual eligible/relevant coverage remains a separate pending result. **Verify V11/V14/V05**.
- **PASS — editorial_policy.md addresses relevance/freshness/credibility/
  novelty/perspective/uncertainty/exclusions**. The populated v1 also covers
  incentives, causality, source identity, exact references and human review.
  **Verify V11/V14/V06**. It is not a completed human policy-revision demonstration.
- **PASS — select_items.md expresses the authorized selection instructions**.
  It supplies scoped piece purposes and evidence-specific acceptance rules.
  **Verify V11/V14/V06**.
- **PASS — create_briefs.md specifies three distinct supported arguments**.
  Working titles are conditional on evidence; exact claims/references are required.
  **Verify V11/V14/V06**.
- **PASS — write_articles.md specifies audience, voice and English length targets**.
  No invented scenes, experiments or unsupported benefits are allowed.
  **Verify V11/V14/V06**.
- **PASS — write_video_scripts.md specifies English narration, useful visuals,
  audience-facing sources and production timing checks**. **Verify V11/V14/V06**.
- **PASS — configured endpoint shapes, shared publisher grouping, extra fields**.
  collectors/support.py and the three discovery helpers preserve source/publisher
  IDs and accept additional metadata. **Verify V04/V05**.
- **PARTIAL — explain and verify publisher independence**. Grouping mechanics
  use publisher_id; actual producer/ownership judgments need student verification.
  Files: lib/evidence.py, SUBMISSION.md. **Verify V06/V12; inspect actual sources**.
- **PASS — credentials environment-only, tools/provider setup documented**.
  lib/model_provider.py, SETUP.md, EDITORIAL.md, requirements.txt and the technical
  links added to SUBMISSION.md. **Verify V01/V06/V08**.

## Common interfaces

- **PASS — RUN_DIR first argument, store subcommands as specified**. All wrappers
  source common.sh and validate arguments; store uses init/upsert/list/get. Its
  init/list/get require RUN_DIR in the environment for the mandatory receipt home.
  **Verify V03/V08**. A valid existing run directory is the standalone prerequisite.
- **PASS — all components independently runnable**. Collectors and extraction:
  V04; store/filter: V03; four model stages: V06/V13; review/package/reporting:
  V07/V09; coordinators: V05/V07. **Verify V02/V03**. A prerequisite failure is not
  counted as proof of successful standalone operation.
- **PASS — JSONL record streams; JSON documents/arrays and Markdown exceptions**.
  lib/records.py, lib/schemas.py, component helpers. **Verify V03–V07**.
- **PASS — stdout data, stderr diagnostics**, including partial collector and
  extractor failures. Wrapper/tool log suppression and captured subprocess outputs
  prevent diagnostic contamination. **Verify V03/V04/V06/V08**.
- **PASS — repository-relative paths, UTC timestamps and nullable unknowns**.
  records.py, collector publication parser, run_setup.py, content/files.py and
  reporting helper. Date-only discovery metadata is retained separately rather
  than inventing midnight timestamps. **Verify V03/V04/V05/V08**.
- **PASS — exits 0/1/2**, including successful empty searches versus failed
  sources; malformed inputs/configuration are 2, operational failures 1.
  Completed negative review assessments are the specified exit-0 exception.
  **Verify V03–V08**.
- **PASS — unique receipts with counts/times/tools/models/cost/errors**, unknown
  cost null and estimates explicit; reruns preserve receipts. common.sh and
  component metrics. Running/final lifecycle records share an invocation ID but
  have distinct names; summary deduplicates them. **Verify V03/V05–V08**.
  Invalid RUN_DIR is rejected before any write; without an authorized receipt home
  a receipt cannot be created. For argument failures with a valid run, V08 checks it.
- **PASS — partial results retained and failed source status propagated**.
  collectors/support.py, extract_content.py, collect_sources.sh. **Verify V04/V05**.
- **PASS — exact config/prompt snapshots and preserved comparison attempts**.
  run_setup.py, both workflows, content/files.py and model_provider.py.
  **Verify V05/V06/V07**. Semantic policy revision remains student work below.

## Run artifacts

- **PASS — metadata fields, unique IDs, UTC date captured once, previous_run_id**.
  run_setup.py. Live is default; explicit example/replay modes retain their label.
  **Verify V05/V07**.
- **PASS — config/, prompts/, logs/, separate candidates/* and merged stream**.
  run_setup.py and collect_sources.sh. **Verify V05**.
- **PASS — items/changes/corpus/eligible/exclusions JSONL**.
  collect_sources.sh saves each before continuing and records actual pipe statuses.
  **Verify V03/V05**.
- **PASS — decisions/briefs/articles/video_scripts manifests and three files each**.
  create_series.sh and content/files.py. **Verify V06/V07/V13**.
- **PASS — review.json and summary.json, including failure summaries**.
  create_series.sh, run.sh and reporting helper. **Verify V05/V07/V08**.
- **PASS — approval.json remains student-supplied; package exists only after approval**.
  prepare_package.py; test approvals are explicitly simulated. **Verify V07/V09**.
- **PASS — original media under data/media, retained text/segments under data/assets**,
  content-addressed immutable files; earlier referenced bytes remain accessible.
  media.py, extract_content.py, store.sh. **Verify V03/V04**.
- **PASS — only store.sh directly opens canonical data/evidence**. Embedded
  Python is part of this owning Bash component. records.py/common.sh only forbid
  index paths; media publishing rejects paths/symlinks resolving there.
  **Verify V01/V08/V10**. No test directly inspects or changes SQLite.
- **PARTIAL — two actual live runs and retained specimens in the submitted repo**.
  Tests create example-mode specimens in disposable directories, not live-run
  evidence. No actual submitted run specimens are present. **Verify V12**.

## Component contracts: entry point and workflows

- **PASS — entry validates/snapshots/initializes/calls both workflows**, then
  summarizes last even on failure and prints summary JSON. run.sh/run_setup.py.
  **Verify V05/V07/V08**.
- **PASS — collection calls all three collectors, preserves separate outputs,
  merges valid records, extracts, upserts, lists and filters**. collect_sources.sh
  and lib/candidate_stream.py. **Verify V04/V05**.
- **PASS — at least one actual compatible pipe with statuses preserved**.
  `store.sh list | tee corpus.jsonl | filter_items.sh`, plus validated candidate
  merging; PIPESTATUS is captured immediately with Bash 3.2 indexed arrays.
  **Verify V05**, including failed filter pipe test.
- **PASS — series saves each artifact, runs checks and refuses insufficient evidence**.
  create_series.sh and create_briefs.py. **Verify V06/V07**. No workflow supplies a
  fabricated source or approval to satisfy missing requirements.

## Component contracts: collection and preparation

- **PASS — written RSS/Atom collector resolves URL/date/stable identity**.
  fetch_feeds.py/support.py, excluding unavailable entries honestly. **Verify V04**.
- **PASS — YouTube collector uses native IDs and actual publication metadata**.
  fetch_youtube.py; unavailable/timestamp-free sources are failure or null, not
  invented dates. **Verify V04**; historical live smoke details are in TEST_RESULTS.md.
- **PASS — podcast collector includes audio enclosure and available transcript links**.
  fetch_podcasts.py/support.py. **Verify V04**.
- **PASS — extraction fetches substantive text or downloads recordings and emits Items**.
  extract_content.py/media.py. **Verify V04**.
- **PASS — timed segments, manual captions before auto, podcast-native before ASR**.
  media.py/transcripts.py; no usable timestamps triggers CPU faster-whisper
  fallback (default base/int8), with method/model provenance. **Verify V04**.
- **PASS — malformed/empty caption artifacts normalized and inaccessible items reported**.
  transcripts.py, extractor per-item errors/receipts. **Verify V04**.
- **PASS — saved extraction reused only after content verification and store queries**.
  extract_content.py uses store list/get interface, fresh substantive/recording
  hashes and native transcripts; retrieval time alone does not mean change.
  **Verify V03/V04**.
- **PASS — confirmed recording copies reconciled to one underlying item**, keeping
  representative transcript offsets and historical exact versions. Reciprocal
  producer links or identical original bytes are recorded as the explicit basis.
  Unconfirmed producer-link leads fail rather than adding a duplicate. **Verify V04/V07**.
- **PARTIAL — unrelated/transcoded copies with no confirming links or byte match**
  require human reconciliation and producer-independence review. No title-based or
  speculative acoustic matching is claimed. Files: extraction and SETUP.md.
  **Verify V04, then inspect real recording pairs before counting coverage**.
- **PASS — mechanical UTC window D−29 through D inclusive**, including previously
  stored unchanged material, unknown/invalid/future/outside reasons and exclusion
  side effects. filter_items.py. **Verify V03/V05**.
- **PASS — item/duration safeguards explicit in receipts**, not silently interpreted
  as complete coverage. support.py/extraction and summary coverage_limits.
  **Verify V04/V05**.

## Component contracts: evidence storage

- **PASS — init is nondestructive, idempotent, with no record stdout**.
  store.sh initialize(). **Verify V03**.
- **PASS — upsert is transactional, ordered, and replay-safe**, including duplicate
  records in one batch (new/changed only first), observations and retained history.
  store.sh upsert(). **Verify V03**.
- **PASS — list exports one latest version per canonical item**, including older
  material for filtering; aliases don't inflate item count. **Verify V03/V04/V05**.
- **PASS — get latest or exact version; missing item/version exits 1**, even after
  a later confirmed identity merge historical exact IDs remain retrievable.
  store.sh get/export_item(). **Verify V03/V04**.
- **PASS — deterministic content/metadata version ID excludes retrieval time**.
  data/versioning.py and documented evidence-v1 SHA-256 in data/README.md/store
  header; retained-path changes cannot overwrite old evidence. **Verify V03/V04**.

## Component contracts: editorial decisions and content

- **PASS — exactly one eligible-item Decision**, accept/reject/defer with reasons
  and intended pieces; excluded items retain separate mechanical reasons.
  select_items.py and Evidence.decisions(). **Verify V06**.
- **PASS — exact snapshotted policy/prompt supplied to each model**, with rendered
  messages, structured schema enforcement and configurable model/provider.
  model_provider.py and four owning components. **Verify V06**.
- **PASS — exactly three distinct supported Briefs, IDs 01/02/03**, with explicit
  question/argument/synthesis/limitations/claims and insufficiency refusal.
  create_briefs.py and Evidence.briefs(). **Verify V06**.
- **PASS — every claim has accepted exact-version evidence**, verified literal
  written quote or existing media segment, date-checked and store-resolved.
  lib/evidence.py and content/validation.py. **Verify V06/V07**.
- **PASS — article/script manifests and inspectable markers preserved**, with
  as-of dates, audience links, quoted passage or timestamp source notes.
  content/files.py and validation.py. **Verify V06/V07**.
- **PASS — script request includes narration, useful visuals and references**;
  structured claims match the article's brief. write_video_scripts.py.
  **Verify V06**, then inspect rendered request and generated scripts.
- **PARTIAL — actual audience-facing quality, original contribution, credibility,
  narration usefulness and semantic consistency** require the student's policy,
  real outputs and human review. Mechanical markers and matching references do not
  establish sound reasoning. **Verify V12 and review actual prose**.

## Component contracts: review and publication handoff

- **PASS — review reads required artifacts/evidence and emits review_id/passed/issues**.
  check_content.py; issues identify piece/artifact, severity and explanation.
  **Verify V06/V07/V09**.
- **PASS — required files, three distinct pieces, exact references, dates, source
  counts and all media kinds checked**; altered source-note passages also fail.
  Evidence.briefs(), check_content.py. **Verify V06/V07**.
- **PASS — length and human-judgment limitations are warnings**, blocking errors
  set passed false; completed negative assessment exits 0. **Verify V06/V07**.
- **PASS — review fingerprint changes with drafts, briefs, references, assets or
  as-of date**, and excludes logs/approval/package outputs. review/fingerprint.py.
  **Verify V07**, including all fingerprint-input variants.
- **PASS — only student supplies approval fields/approve-or-revise decision**.
  Approval shape/timestamp validation and exact fingerprint matching are enforced
  by prepare_package.py. No production code writes approval.json. **Verify V07/V10**.
- **PASS — direct packaging independently reassesses current inputs**, refuses
  failed/missing/stale review or nonmatching approval with exit 1. **Verify V07/V09**.
- **PASS — package has three articles, three scripts and per-piece source notes**,
  manifest asset/piece listings and manual steps for Google Vids/HeyGen, Substack
  and YouTube. prepare_package.py. **Verify V07/V09**.
- **PASS — publication links initially null and preserved on unchanged repackaging**;
  malformed links return 2 without replacing the existing package. **Verify V07/V09**.
- **PASS — package readiness does not claim rendering or publication**.
  Manifest marks videos_rendered/publication_verified false; handoff docs describe
  human production/publishing/access verification. **Verify V07 and PUBLISHING.md**.
- **PARTIAL — actual student approval and three rendered/published pairs**, including
  cross-links, source descriptions and staff access, are not supplied. **Verify V12**.

## Component contracts: reporting

- **PASS — incomplete saved runs are summarized**, with failed/incomplete stage
  details and run_id/status rather than invented successful stages.
  reporting/summarize_run.py. **Verify V05/V07/V08**.
- **PASS — all required counts**, discovered/extracted/new/changed/unchanged/
  eligible/excluded/accepted/rejected/deferred/articles/video_scripts.
  Null means unmeasured; measured empty artifacts give 0; failed invalid-output
  stages don't get fabricated zero counts. **Verify V05/V07/V08**.
- **PASS — distinct underlying-item coverage by kind and publisher**, duplicate
  observations separately, collector/extraction limits and coverage failures kept
  explicit even when usable evidence continues. **Verify V05/V07**.
- **PASS — elapsed time, tool/model use, known/estimated/unknown costs**.
  Invocation receipts are deduplicated; cost_usd is explicitly a known subtotal
  across retained attempts, not an assumed complete bill. Unknowns remain listed.
  **Verify V06/V07**.
- **PASS — exactly failed / awaiting_review / ready_for_production**, stale approval
  and damaged package fail; renewed passing review can resolve prior check failures.
  **Verify V07/V09**.
- **PASS — remaining manual actions and published links separate from readiness**;
  no inferred publication from a missing URL/file. **Verify V07/V09**.

## Shared record definitions

- **PASS — Candidate:** all nine required fields, nullable published_at/media_url,
  configured kind, native/canonical stable identity. support.py, extraction's
  validate_candidate and candidate_stream.py. **Verify V04/V05/V08**.
- **PASS — Item:** Candidate fields plus version_id/text_path/segments_path;
  written segments null, media segments required. records.validate_item().
  **Verify V03/V04**.
- **PASS — Segment:** array of objects with segment_id/start_seconds/end_seconds/text;
  numeric finite ordered times and usable text. transcripts.py/versioning.py.
  **Verify V03/V04**.
- **PASS — Exclusion:** item_id/version_id/reason/detail with required reasons.
  filter_items.py. **Verify V03**.
- **PASS — Change:** item_id/version_id/change, values new/changed/unchanged.
  store.sh. **Verify V03**.
- **PASS — Decision:** item_id/version_id/decision/reason/piece_ids; reject/defer
  arrays empty and accept assignments checked. schemas.py/evidence.py. **Verify V06**.
- **PASS — Brief:** piece_id/title/question/argument/synthesis/limitations/claims.
  schemas.py/evidence.py. **Verify V06**.
- **PASS — Claim:** claim_id/statement/type/evidence with reported_fact/source_claim/
  inference types and nonempty evidence. schemas.py. **Verify V06**.
- **PASS — Evidence ref:** item_id/version_id/locator with text exact quote or
  segment existing segment_id, never a title/homepage substitute. evidence.py.
  **Verify V06/V07**.
- **PASS — Content manifest:** piece_id/path/claim_ids with three actual outputs.
  schemas.py/content/files.py. **Verify V06/V07**.
- **PASS — required strings, objects and arrays; extra fields allowed**.
  Local schemas preserve ARCHITECTURE's extensibility; strict provider requests
  close their transport schemas without changing the local record contract.
  **Verify V06**, including extra-claim-metadata test.
- **PASS — evidence paths resolve outside the index**, versions and assets retained
  exactly, inferences carry source references and brief synthesis. records.py,
  versioning.py/evidence.py/store.sh. **Verify V03/V04/V06/V08**.

## Additional requested checks

- **PASS — no unauthorized index access found**. Only store.sh imports/opens
  SQLite; other mentions are guards. Runtime attempts to route receipts into the
  index are rejected, and all successful evidence queries use store.sh.
  **Verify V01/V08/V10**. Static checks are supported by manual source review;
  substring absence alone would not prove access isolation.
- **PARTIAL — earlier scan found no credential matches; local secret now present**.
  V01's scan initially checked 162 working files/history blobs, including 38
  historical blobs, with zero findings. Active credentials, key formats and private
  key blocks are checked without printing values. Persistence canary tests pass.
  The later user-supplied .env intentionally contains the local credential and
  is outside that earlier result. `git ls-files -- .env` returns no path;
  `git check-ignore .env` confirms exclusion. Environment-only transport and
  persistence canaries remain tested. Do not run a diagnostic that prints .env.
  **Verify V06/V08 and those filename-only Git commands**.
- **PARTIAL — universal 'no secrets anywhere' cannot be certified by a pattern scan**.
  Unrecognized formats, third-party installations, external environment/accounts
  and inaccessible history are outside that claim. The scanner never directly
  reads canonical SQLite to satisfy index ownership; store validates incoming
  metadata/text/segments and only its get/list interface may inspect saved records.
  No secret contents are included in this audit. **Verify V01/V03/V08**.
- **PASS — macOS Bash 3.2/BSD compatibility**. Tests invoke /bin/bash and the static
  verifier rejects associative arrays/mapfile/readarray/lowercase expansion/GNU
  hashing. Shell date uses portable UTC formatting; date/hash work is otherwise
  Python. **Verify V01/V02/V03**.

## Evaluation checkpoints and student submission

- **PASS — fixture source of every required kind, traced claim, replay without
  duplicate versions, window checks and honest simulated failure/recovery**.
  Test fixtures and TEST_RESULTS.md document these bounded technical demonstrations.
  **Verify V03–V09**.
- **PARTIAL — corresponding live evidence, inspected real editorial decisions and
  two live runs on different days**. Fixtures and a historical transport smoke test
  do not meet the assignment quantity/freshness/live-run requirements. **Verify V12**.
- **PARTIAL — actual editorial-policy revision/comparison and factual corrections**.
  Preservation mechanics exist, but the student's judgments and before/after
  policy specimens are missing. **Verify V12 and SUBMISSION.md Editorial Review**.
- **PARTIAL — submitted specimens remain accessible in the repository**. Temporary
  fictional test repositories are retained locally but are not submitted live-run
  specimens. Keep real source text/transcripts and run artifacts once collected.
  **Verify V12**.
- **PASS — technical setup/provider/handoff documentation** is linked into
  SUBMISSION.md; requirements.txt, SETUP.md, EDITORIAL.md and PUBLISHING.md contain
  concrete commands and environment-variable names without secret values.
  **Verify V01 and inspect those files**.
- **PASS — draft implemented architecture diagram** now exists in
  SUBMISSION.md, including model-call locations, sole index ownership, assets,
  manual approval/production/publication, and summary. **Verify**
  `rg -n 'flowchart|model call|SQLite|Manual' SUBMISSION.md`.
- **PARTIAL — actual student identity/repository URL/model choice**.
  Topic and audience are now populated, but the student elected to supply identity
  and repository URL later; live model service is not yet configured. **Verify V12/V14**.
- **PARTIAL — actual three article/video publication URLs and technical demo link**.
  These remain placeholders, not fabricated links. **Verify V12 and open submitted links**.
- **PARTIAL — real evidence locations, review sample, policy revision and reflection**.
  SUBMISSION.md still requests these student-authored accounts. **Verify V12**.

## Recorded execution results

Actual outputs during this audit (overlapping targeted reruns are not added as
independent test totals):

```text
$ .venv/bin/python tests/audit_repo.py
required_bash_files: 16
files_or_blobs_scanned: 162
historical_blobs_scanned: 38
findings: []
$ /bin/bash tests/test_components.sh
12 tests passed.
$ .venv/bin/python -m pytest tests/test_audit_contracts.py -q
21 passed in 7.99s
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

The full suite ran after the initial fixes; the two new freshness/repost tests and
the newly added receipt-home guard were then verified separately. Final changed
extraction/package paths receive the targeted regression check recorded in
TEST_RESULTS.md. All fixtures remain explicitly fictional. These results establish
technical behavior, not completion of the student's publication assignment.
