#!/usr/bin/env bash
set -euo pipefail

# FICTIONAL fixtures only. Tests never inspect or manipulate an evidence index;
# all index access (including counts in receipts) goes through data/store.sh.
SOURCE_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
TEST_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/ps04-components.XXXXXX")
for directory in lib data processing tests/fixtures runs/fixture; do
    mkdir -p "$TEST_ROOT/$directory"
done
cp "$SOURCE_ROOT/lib/common.sh" "$SOURCE_ROOT/lib/records.py" "$TEST_ROOT/lib/"
cp "$SOURCE_ROOT/data/store.sh" "$SOURCE_ROOT/data/versioning.py" "$TEST_ROOT/data/"
cp "$SOURCE_ROOT/processing/filter_items.sh" "$SOURCE_ROOT/processing/filter_items.py" "$TEST_ROOT/processing/"
cp "$SOURCE_ROOT/tests/fixtures/"{README.md,run.json,text.txt,items.jsonl,filter_items.jsonl} "$TEST_ROOT/tests/fixtures/"
cp "$TEST_ROOT/tests/fixtures/run.json" "$TEST_ROOT/runs/fixture/run.json"
cd "$TEST_ROOT"
export RUN_DIR=runs/fixture PYTHONDONTWRITEBYTECODE=1
passed=0

die() { printf 'FAIL: %s\nFixture repository retained: %s\n' "$*" "$TEST_ROOT" >&2; exit 1; }
pass() { passed=$((passed + 1)); printf 'PASS: %s\n' "$*"; }
expect_exit() {
    local wanted=$1 actual=0
    shift
    "$@" > "$TEST_ROOT/stdout" 2> "$TEST_ROOT/stderr" || actual=$?
    [[ "$actual" == "$wanted" ]] || die "expected exit $wanted, got $actual: $*"
}
assert_json() { jq -e "$1" "${2:-$TEST_ROOT/stdout}" >/dev/null || die "$1"; }
latest_receipt() {
    python3 - <<'PY'
from pathlib import Path
files = list(Path('runs/fixture/logs').glob('*-completed.json'))
files += list(Path('runs/fixture/logs').glob('*-failed.json'))
print(max(files, key=lambda p: p.stat().st_mtime_ns))
PY
}
assert_counts() {
    assert_json ".store_counts.items == $1 and .store_counts.versions == $2" "$(latest_receipt)"
}

expect_exit 0 bash data/store.sh init
[[ ! -s "$TEST_ROOT/stdout" ]] || die 'init wrote record output'
expect_exit 0 bash data/store.sh init
assert_counts 0 0
pass 'init is idempotent and emits no records'

expect_exit 0 bash data/store.sh upsert "$RUN_DIR" < tests/fixtures/items.jsonl
assert_json '.change == "new"'
assert_counts 1 1
expect_exit 0 bash data/store.sh upsert "$RUN_DIR" < tests/fixtures/items.jsonl
assert_json '.change == "unchanged"'
assert_counts 1 1
expect_exit 0 bash data/store.sh list
[[ $(wc -l < "$TEST_ROOT/stdout" | tr -d ' ') == 1 ]] || die 'list duplicated item'
pass 'identical replay keeps exactly 1 item and 1 version'

jq -c '.retrieved_at = "2026-10-15T13:00:00Z"' tests/fixtures/items.jsonl > runs/fixture/retrieved.jsonl
expect_exit 0 bash data/store.sh upsert "$RUN_DIR" < runs/fixture/retrieved.jsonl
assert_json '.change == "unchanged"'
assert_counts 1 1
assert_json '.store_counts.observations == 3' "$(latest_receipt)"
pass 'retrieval timestamp change adds an observation, not a version'

# Generate modified metadata using the public pure hash utility, never SQLite.
python3 - <<'PY'
import json
from pathlib import Path
from data.versioning import version_id
item = json.loads(Path('tests/fixtures/items.jsonl').read_text())
item['item_id'] = 'fixture:second'
item['version_id'] = version_id(item, Path.cwd())
Path('runs/fixture/duplicate.jsonl').write_text((json.dumps(item) + '\n') * 2)
item['item_id'] = 'fixture:written-1'
item['title'] = 'FICTIONAL corrected title'
item['version_id'] = version_id(item, Path.cwd())
Path('runs/fixture/changed.jsonl').write_text(json.dumps(item) + '\n')
PY
expect_exit 0 bash data/store.sh upsert "$RUN_DIR" < runs/fixture/duplicate.jsonl
jq -se 'map(.change) == ["new", "unchanged"]' "$TEST_ROOT/stdout" >/dev/null || die 'batch duplicate order'
assert_counts 2 2
pass 'duplicate records in one ingestion produce new then unchanged'

original_version=$(jq -r '.version_id' tests/fixtures/items.jsonl)
expect_exit 0 bash data/store.sh upsert "$RUN_DIR" < runs/fixture/changed.jsonl
assert_json '.change == "changed"'
assert_counts 2 3
expect_exit 0 bash data/store.sh get fixture:written-1 "$original_version"
assert_json '.title == "FICTIONAL fixture article"'
expect_exit 0 bash data/store.sh get fixture:written-1
assert_json '.title == "FICTIONAL corrected title"'
pass 'substantive metadata creates a version and historical get remains available'

expect_exit 1 bash data/store.sh get fixture:missing
[[ ! -s "$TEST_ROOT/stdout" && -s "$TEST_ROOT/stderr" ]] || die 'missing get output contract'
assert_json '.exit_code == 1 and .status == "failed" and (.errors | length > 0)' "$(latest_receipt)"
expect_exit 1 bash data/store.sh get fixture:written-1 nonexistent-version
pass 'missing item and missing version return exit 1 with diagnostics and receipts'

cat tests/fixtures/items.jsonl > runs/fixture/bad.jsonl
printf '%s\n' '{"bad":' >> runs/fixture/bad.jsonl
expect_exit 2 bash data/store.sh upsert "$RUN_DIR" < runs/fixture/bad.jsonl
[[ ! -s "$TEST_ROOT/stdout" ]] || die 'malformed batch emitted changes'
expect_exit 0 bash data/store.sh get fixture:written-1
assert_json '.title == "FICTIONAL corrected title"'
assert_counts 2 3
jq -c '.version_id = "forged"' tests/fixtures/items.jsonl > runs/fixture/forged.jsonl
expect_exit 2 bash data/store.sh upsert "$RUN_DIR" < runs/fixture/forged.jsonl
pass 'malformed batches and forged version IDs fail without changing latest evidence'

jq -c '.aliases = [{item_id:"fixture:mirror",basis:"FICTIONAL explicit producer cross-link"}]' \
    runs/fixture/changed.jsonl > runs/fixture/alias.jsonl
expect_exit 0 bash data/store.sh upsert "$RUN_DIR" < runs/fixture/alias.jsonl
assert_counts 2 3
expect_exit 0 bash data/store.sh get fixture:mirror
assert_json '.item_id == "fixture:written-1"'
pass 'explicit alias resolves to one canonical item without a new version'

expect_exit 0 bash processing/filter_items.sh "$RUN_DIR" < tests/fixtures/filter_items.jsonl
jq -se 'map(.item_id) == ["fixture:lower", "fixture:upper"]' "$TEST_ROOT/stdout" >/dev/null || die 'inclusive date boundaries'
assert_json '.input_count == 6 and .output_count == 2 and .excluded_count == 4' "$(latest_receipt)"
pass '30-day window includes D-29 at 00:00:00Z and D at 23:59:59Z'
jq -se 'map({key:.item_id,value:.reason}) | from_entries == {
    "fixture:old":"outside_window", "fixture:unknown":"unknown_date",
    "fixture:future":"future_date", "fixture:invalid":"invalid_date"
}' runs/fixture/exclusions.jsonl >/dev/null || die 'exclusion reasons'
pass 'outside_window, unknown_date, future_date, invalid_date are recorded'

cp runs/fixture/exclusions.jsonl runs/fixture/exclusions.before
expect_exit 2 bash processing/filter_items.sh "$RUN_DIR" < runs/fixture/bad.jsonl
cmp runs/fixture/exclusions.before runs/fixture/exclusions.jsonl || die 'bad input replaced exclusion artifact'
[[ ! -s "$TEST_ROOT/stdout" ]] || die 'bad filter input emitted records'
expect_exit 0 bash processing/filter_items.sh "$RUN_DIR" < /dev/null
assert_json '.input_count == 0 and .output_count == 0' "$(latest_receipt)"
[[ ! -s runs/fixture/exclusions.jsonl ]] || die 'empty input did not clear exclusions'
pass 'filter preserves prior output on malformed input; empty input is a measured success'

expect_exit 2 bash data/store.sh list extra
assert_json '.exit_code == 2' "$(latest_receipt)"
expect_exit 2 bash processing/filter_items.sh "$RUN_DIR" extra
assert_json '.exit_code == 2' "$(latest_receipt)"
python3 - <<'PY'
import json
from pathlib import Path
receipts = [json.loads(p.read_text()) for p in Path('runs/fixture/logs').glob('*.json')]
running = [r for r in receipts if r['status'] == 'running']
final = [r for r in receipts if r['status'] != 'running']
assert len({r['invocation_id'] for r in final}) == len(final)
assert {r['invocation_id'] for r in final} == {r['invocation_id'] for r in running}
for r in final:
    assert r['started_at'].endswith('Z') and r['finished_at'].endswith('Z')
    assert r['tools'] and r['cost_usd'] is None
    assert r['exit_code'] in (0, 1, 2)
    assert {'stage', 'input_count', 'output_count', 'models', 'errors'} <= r.keys()
PY
pass 'argument failures return 2; every invocation retains unique complete receipts'

printf '\n%s tests passed. FICTIONAL fixture repository retained at:\n%s\n' "$passed" "$TEST_ROOT"
