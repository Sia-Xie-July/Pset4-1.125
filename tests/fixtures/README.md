# FICTIONAL FIXTURES — NOT COLLECTED EVIDENCE

All items, URLs, text and dates in this directory are invented test inputs.
`run.json` uses mode `example` and a fixed as-of date of 2026-10-14.

- `items.jsonl`: one fictional written Item with an evidence-v1 version hash.
- `text.txt`: the retained fictional passage used by that hash.
- `filter_items.jsonl`: six fictional Items testing 2026-09-15 and 2026-10-14
  as inclusive endpoints, and old, unknown, future, and malformed dates.

The tests copy only implementation files and these fixtures to temporary
repositories. Only the copied `data/store.sh` accesses their evidence indexes.
Tests never open SQLite directly and never ingest fixtures into the project's
live store. Temporary repositories are retained for inspection; their paths are
printed by the test suite.
