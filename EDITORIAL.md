# Editorial and content stages

These four components own separate model requests and validations. The series
workflow only sequences them and the mechanical content checker. `run.sh` runs
collection and the series, then saves the summary even on failure. Successful
checks stop at awaiting_review. See PUBLISHING.md for the human approval and
production handoff. `--collection-only` is an optional diagnostic shortcut.

## Environment configuration

Current default: local Ollama / Qwen3 8B. Use `bash run_local.sh`; no credentials
or `.env` are needed. Selection is per item with explicitly labelled literal
excerpts; synthesis and writing are per piece. `editorial/passages.py` retrieves
bounded passages, `editorial/local_briefs.py` owns compact brief requests, and
`content/local_documents.py` owns per-document generation. Full evidence is
retained, and omitted context is a human-review limitation. Short passage handles
expand to validated source versions and locators. Document generation preserves
the brief claim objects mechanically, avoiding unnecessary regeneration of IDs.
Each model call has unique prompt/output files; stage receipts aggregate calls.

The cloud adapter described below is an explicit legacy alternative, not the
default and not used by `run_local.sh`. There is no automatic cloud fallback.

Activate the project venv and update dependencies:

```bash
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

For a live provider:

```bash
export MODEL_PROVIDER=openai_compatible
export MODEL_BASE_URL=https://api.openai.com/v1
export MODEL_NAME=your-provider-model-id
# Supply MODEL_API_KEY through your environment/secret manager.
# OPENAI_API_KEY is also accepted when MODEL_API_KEY is absent.
export MODEL_RESPONSE_FORMAT=json_schema
```

`MODEL_BASE_URL` can point to another compatible service; HTTPS is required except
for localhost HTTP. Embedded credentials/query strings are rejected. Local servers
may omit the key. No key or authorization header is saved or logged. Unknown
providers/missing model names are configuration errors (exit 2), not silent defaults
to a different model. Per-stage overrides are `SELECT_ITEMS_MODEL`,
`CREATE_BRIEFS_MODEL`, `WRITE_ARTICLES_MODEL`, `WRITE_VIDEO_SCRIPTS_MODEL`.

The HTTP adapter uses `/chat/completions` and strict `json_schema` output by
default. If a compatible provider lacks that feature, explicitly set
`MODEL_RESPONSE_FORMAT=json_object`. Both modes include the schema in the request
instructions and always enforce local JSON Schema plus reference validation.
There is no automatic downgrade, retry, JSON repair or prose-to-JSON conversion.
The adapter follows the
[official OpenAI structured-output contract](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=chat).

Optional limits: `MODEL_TIMEOUT_SECONDS=120`, `MODEL_MAX_OUTPUT_TOKENS=8000`.
`MODEL_TOKEN_LIMIT_FIELD` defaults to `max_completion_tokens`; choose `max_tokens`
explicitly for a compatible endpoint that requires it. A refused/network/provider
request fails with exit 1; malformed/incomplete structured output fails with exit 2.

Set `MODEL_INPUT_USD_PER_MILLION` and `MODEL_OUTPUT_USD_PER_MILLION` to your
provider's applicable prices to get token-based estimates. No prices are guessed.
Receipts record requested/returned model names, model-call duration, stage duration,
provider-reported input/output token counts, configured rates, and estimate:

```text
estimated USD = (input_tokens * input_rate + output_tokens * output_rate) / 1,000,000
```

If usage or either price is missing, cost is null. Estimates do not account for
discount tiers or invoice adjustments; they are explicitly flagged estimates.
Token usage/accounting is retained even when a returned response later fails
validation. Call status/request-attempt flags distinguish configuration/transport
failures from completed responses. No paid API calls are made by fixture tests.

## Standalone commands and workflow

The run must have its config/prompt snapshots, eligible.jsonl and stored exact
evidence versions/assets. You supply the real editorial policy and all four
prompts; this implementation has not changed those files.

```bash
R=runs/RUN_ID
bash editorial/select_items.sh "$R" < "$R/eligible.jsonl" > "$R/decisions.jsonl"
bash editorial/create_briefs.sh "$R" < "$R/decisions.jsonl" > "$R/briefs.jsonl"
bash content/write_articles.sh "$R" < "$R/briefs.jsonl" > "$R/articles.jsonl"
bash content/write_video_scripts.sh "$R" < "$R/briefs.jsonl" > "$R/video_scripts.jsonl"
bash review/check_content.sh "$R" > "$R/review.json"
```

Or coordinate the complete series attempt:

```bash
bash workflows/create_series.sh "$R"
```

The workflow saves each named artifact before continuing, stops on failed stages,
records statuses in series_stages.jsonl, and only reaches awaiting_review after a
completed passing mechanical assessment. Assessment exit 0 does not imply passed;
the workflow inspects review.passed. It never creates approval.json. Reruns move
previous outputs/review/approval to unique attempts/ directories and preserve old
receipts. Valid direct generator reruns archive existing drafts; rejected output
does not replace them.

## Structured outputs and evidence integrity

Schemas live in lib/schemas.py. Each provider returns one JSON object containing
an array; each component emits its prescribed JSONL after all records validate:

- Selection envelope: `{"decisions":[Decision,...]}`. Exactly one accept/reject/defer
  per eligible item/version. Accepted items name intended pieces; reject/defer
  arrays are empty. Output order matches input order.
- Brief envelope: `{"briefs":[Brief,Brief,Brief]}`. Exactly 01/02/03, distinct arguments,
  explicit claims/synthesis/limitations, and actual citations from each assigned
  accepted set. Insufficient valid accepted evidence fails **before model access**
  with exit 1: each piece needs at least three declared independent publishers,
  and the selected sets together must cover feed/YouTube/podcast. A model that
  fails to use those available sources or invents references is malformed (exit 2).
  The owning brief component additionally builds a request schema from the actual
  per-piece accepted set: each item/version pair is an allowed literal pair,
  written/media locator types match the source, and media segment IDs must match
  the retained list. This constrains generation without replacing post-response
  validation; exact written quotes and all semantic limitations remain checked.
  Written quote values are constrained to a small menu of literal retained
  excerpts, ranked by workflow-related terms. Full articles remain in the model
  context and retained assets; the menu is a locator aid, not a source summary.
  This can bias passage choice, so human review must still check whether each
  excerpt supports its claim and whether important context was missed.
- Content envelope: `{"documents":[Document,Document,Document]}`. Each Document
  has piece_id, markdown, claim_ids, claims. Claims must exactly preserve the brief
  claims/references, and all supported IDs must appear as Markdown markers. This
  internal shape allows structured validation while stdout emits the required
  Content manifests (piece_id/path/claim_ids).

The schemas follow the required fields/types in ARCHITECTURE.md; local validation
permits extra fields as that contract allows. Strict HTTP schemas close objects
to their defined properties. No component routes the entire pipeline through a
shared application: the shared helpers perform only transport, schema checks,
evidence verification, receipt bookkeeping or content-file publication.

Eligible metadata must match `store.sh get ITEM_ID VERSION_ID`. Asset hashes are
recomputed and the inclusive 30-day window rechecked. Only store.sh opens the
evidence index. Every claim needs evidence from eligible accepted exact versions.
Written locators contain a nonblank quote that is an exact case/whitespace-sensitive
substring of retained text; media locators identify a segment that exists in the
version's transcript. Missing versions, invented passages/segments, unselected
sources and mismatched metadata are rejected. Corrupt/missing retained assets fail
operationally. No invented sources are inserted to make a brief pass.

Model Markdown direct quotes (straight/curly double quotes and blockquotes) must
also be exact excerpts of the cited supporting passages. Rhetorical/scare quotes
without source support are therefore rejected; use unquoted wording for those.
Article/script claims must stay identical to their brief at the structured level;
their audience phrasing and narration can differ. Reference existence does not
prove entailment or factual correctness: human review must assess actual reasoning
and prose. Declared publisher_id supplies independence grouping, which the student
must verify; the code does not infer independence from reputation or popularity.

The components write articles/01–03.md and video_scripts/01–03.md with as-of dates,
inspectable claim markers, versioned source notes and media timestamps. Raw provider
content is retained under model_outputs/ with unique filenames; exact rendered
messages (including the snapshotted policy/prompt) are retained under
prompts/rendered/. Original snapshot files and earlier receipts are not overwritten.

## Mechanical review and limits

The supporting check_content component validates three briefs/manifests/files,
claim/reference/date consistency, direct quotes, source notes, and collection
coverage (12 distinct items, six publishers, two per input kind). Length targets
are warnings. It fingerprints assessed files, source assets and run date; changed
inputs change review_id. It returns one review object and exits 0 after a completed
assessment even when passed is false. It explicitly warns that semantic consistency,
original synthesis, credibility and counterarguments require human judgment.

## Fixture mode and tests

```bash
python3 -m pytest -q tests/test_editorial.py
python3 tests/dry_run_editorial.py --stage select_items
python3 tests/dry_run_editorial.py --stage create_briefs
python3 tests/dry_run_editorial.py --stage write_articles
python3 tests/dry_run_editorial.py --stage write_video_scripts
python3 tests/dry_run_editorial.py
```

The driver builds a retained isolated example run and prints each actual stage
command and sample output. It sets MODEL_PROVIDER=fixture and MODEL_FIXTURE_DIR to
its canned response directory. Static responses require `fixture:true`; usage
counts are explicitly synthetic. Fixture mode is forbidden for live runs, and
fixture-tagged evidence cannot be used in live editorial requests. Generated
example/replay drafts have an explicit non-publication label.

Fixture receipts record actual API cost 0, and keep the token/rate calculation
separately as simulated_cost_usd. It is never reported as a real bill. Tests also
mock HTTP transport in process to check structured-output requests and real-provider
accounting without network or API calls. Fictional sources/prompts are isolated
from the student's topic configuration. See docs/history/TEST_RESULTS.md for actual output.
