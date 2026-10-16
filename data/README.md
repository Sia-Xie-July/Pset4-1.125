# Evidence storage and date filtering

Implemented components require Bash, jq, and Python 3.10+ with its standard
library (including SQLite). There are no model/network calls in this phase.

## Standalone commands

Run from the repository root. An existing run directory is required for receipts.
For upsert it must contain `run.json` with a nonempty `run_id`; keep the complete
architecture metadata (`started_at`, `as_of_date`, `mode`, `previous_run_id`).

```bash
RUN_DIR=runs/RUN_ID bash data/store.sh init
bash data/store.sh upsert runs/RUN_ID < runs/RUN_ID/items.jsonl
RUN_DIR=runs/RUN_ID bash data/store.sh list > runs/RUN_ID/corpus.jsonl
RUN_DIR=runs/RUN_ID bash data/store.sh get ITEM_ID VERSION_ID
bash processing/filter_items.sh runs/RUN_ID < runs/RUN_ID/corpus.jsonl > runs/RUN_ID/eligible.jsonl
```

Omit VERSION_ID to get latest. `init` is idempotent and silent; other store
commands emit JSONL. Missing items/versions return 1. Invalid arguments or
malformed input return 2. The filter writes `exclusions.jsonl` atomically after
validating the full stream, and emits eligible Item records unchanged.

Test without contaminating a live index:

```bash
bash tests/test_components.sh
```

Tests build a temporary repository from explicitly fictional fixtures. They
retain it and print its path. Item/version counts are read from store receipts,
never by opening SQLite from a test. `tests/fixtures/run.json` fixes the example
date at 2026-10-14; both 2026-09-15 and 2026-10-14 are eligible. Null, malformed,
older, and future dates receive their documented exclusion reasons. Date-only
and non-UTC publication timestamps are invalid, not guessed or silently converted.

## Ownership and schema

Only `data/store.sh` opens `data/evidence/evidence.sqlite3`; its Python program is
embedded in that file. Tables hold canonical items/current-version pointers,
immutable versions, associated run metadata, every ingestion observation, and
explicit aliases. Transactions and primary/foreign keys protect identity and
version uniqueness. Entire malformed batches roll back and emit no changes.
Concurrent writes have a 10-second SQLite busy timeout and an immediate write
transaction. `list` sorts by item ID and retains old material for date filtering.

Every replay records observations, but adds no duplicate versions. Retrieval
timestamps in returned versions remain the originally retained timestamp; later
retrievals are preserved in observations. A return to a historical version moves
the latest pointer and reports changed, without creating another version row.

Optional `aliases` is an array of `{ "item_id": "...", "basis": "..." }`
objects describing confirmed alternate route identities. An alias is not a
second item; `get` resolves it. Upsert must use the canonical identity and version
hash, not an independently hashed alias identity. Conflicts with already stored
canonical items are rejected unless the alias explicitly supplies
`merge_existing: true` with its matching basis. Extraction supplies this only
after confirming exact recording bytes or reciprocal producer episode links.
That reconciliation retires the duplicate latest-item pointer but preserves all
historical versions, observations, and version-pinned get calls. The store does
not guess matches from titles. Stored versions remain intact.

## Exact evidence-v1 hash

`data/versioning.py` is the pure hashing utility used by ingestion validation and
used by extraction. It never accesses the index. `version_id` is the
lowercase hexadecimal SHA-256 digest of this payload's canonical UTF-8 JSON:

- `algorithm`: `evidence-v1`;
- `item_id`, `source_id`, `publisher_id`, `kind`, `title`, `url`, `published_at`;
- `text_sha256`, or null if absent;
- `segments_sha256`, or null if absent.

Canonical JSON uses sorted keys, comma/colon separators without spaces,
unescaped Unicode, and rejects nonfinite numbers. Text is UTF-8 with Unicode NFC
and CRLF/CR normalized to LF; other whitespace is preserved. Segment hashing
uses the ordered array of `segment_id`, `text`, `start_seconds`, `end_seconds`;
times normalize to finite floats, so 1 and 1.0 are equivalent. Segment text is
otherwise exact. Segment IDs are unique, intervals nonnegative, and starts ordered.

Canonical public URLs and verified source attribution are supplied by extraction;
the store does not guess URL equivalences or rewrite user evidence. Publication
date strings, including malformed ones for downstream exclusion, are hashed as
supplied. Retrieval time, run IDs, asset paths, transport media URLs, aliases,
and other observation-only extensions are excluded. Asset paths stay within the
repository and outside `data/evidence/`. Written evidence requires substantive
text; media requires a nonempty segment array. New content needs a new immutable
asset path; ingestion rejects changed content at a previously referenced path.

Upsert recomputes and verifies the supplied hash, and returns one ordered Change
per input. The first new identity reports new; differing current versions report
changed; repeated current versions report unchanged. Historical rows and assets
must be retained. Legacy starter example hashes are illustrative and need not
match this algorithm; use `tests/fixtures/` for executable fixtures.

## Receipt helper

Each implemented Bash component sources `lib/common.sh`, calls
`common_init STAGE RUN_DIR`, then `require_arg_count`. `log` writes stderr;
`fail CODE MESSAGE` records a safe diagnostic and exits. Components never log raw
input, environments, or command traces. Python components write measured counts
and safe errors to the invocation's `RECEIPT_METRICS` file; the EXIT trap combines
these with invocation metadata into an atomic receipt.

Each invocation retains a unique running receipt and a separate completed/failed
receipt linked by `invocation_id`. Reports must count the final receipt once;
an unmatched running receipt means interruption before finalization. Final
receipts include stage, status, exit code, counts, UTC start/finish, tools/models,
cost (null for unmeasured), estimate flag and errors. Store receipts additionally
report `store_counts` for items, versions and observations. No database inspection
by other components is needed. INT/TERM/HUP produce exit 1; SIGKILL cannot be
trapped. No valid/writable run directory or missing receipt dependencies can
prevent receipt creation; these failures are reported to stderr explicitly.
