#!/usr/bin/env bash
set -euo pipefail

# Evidence-v1: SHA-256 of sorted compact UTF-8 JSON containing algorithm tag,
# item_id/source_id/publisher_id/kind/title/url/published_at plus normalized text
# and ordered segment digests. See data/README.md and data/versioning.py.
# Retrieval times, paths, transport media URLs, and run IDs are excluded.
# This file alone opens data/evidence/. Python below is part of this component.
REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$REPO_ROOT"
source "$REPO_ROOT/lib/common.sh"
command_name=${1:-}
if [[ "$command_name" == upsert ]]; then
    common_init store.upsert "${2:-${RUN_DIR:-}}"
else
    common_init "store.${command_name:-invalid}" "${RUN_DIR:-}"
fi
case "$command_name" in
    init|list) require_arg_count "$#" 1 1 'Usage: store.sh init|list (set RUN_DIR)' ;;
    upsert) require_arg_count "$#" 2 2 'Usage: store.sh upsert RUN_DIR' ;;
    get) require_arg_count "$#" 2 3 'Usage: store.sh get ITEM_ID [VERSION_ID] (set RUN_DIR)' ;;
    *) fail 2 'Usage: store.sh init|upsert|list|get' ;;
esac

# fd 3 preserves the JSONL input while stdin carries this component's program.
python3 - "$@" 3<&0 <<'PY'
import os
import sqlite3
import sys
from pathlib import Path

from data.versioning import digest, version_payload
from lib.records import canonical, load_json, read_items, save_metrics

root = Path.cwd()
metrics = {"input_count": 0, "output_count": 0, "errors": []}
db = None


def connect(create=False):
    directory = root / "data/evidence"
    if create:
        directory.mkdir(parents=True, exist_ok=True)
    path = directory / "evidence.sqlite3"
    if not create and not path.is_file():
        raise OSError("Store is not initialized; run store.sh init")
    connection = sqlite3.connect(str(path), timeout=10)
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def initialize():
    db.executescript("""
    CREATE TABLE IF NOT EXISTS versions (
        item_id TEXT NOT NULL, version_id TEXT NOT NULL, item_json TEXT NOT NULL,
        hash_payload TEXT NOT NULL, first_run TEXT NOT NULL,
        PRIMARY KEY(item_id, version_id)
    );
    CREATE TABLE IF NOT EXISTS items (
        item_id TEXT PRIMARY KEY, latest_version TEXT NOT NULL, first_run TEXT NOT NULL,
        FOREIGN KEY(item_id, latest_version) REFERENCES versions(item_id, version_id)
    );
    CREATE TABLE IF NOT EXISTS runs (run_id TEXT PRIMARY KEY, metadata TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS observations (
        invocation_id TEXT NOT NULL, ordinal INTEGER NOT NULL, run_id TEXT NOT NULL,
        item_id TEXT NOT NULL, version_id TEXT NOT NULL, item_json TEXT NOT NULL,
        change TEXT NOT NULL, PRIMARY KEY(invocation_id, ordinal),
        FOREIGN KEY(item_id, version_id) REFERENCES versions(item_id, version_id),
        FOREIGN KEY(run_id) REFERENCES runs(run_id)
    );
    CREATE TABLE IF NOT EXISTS aliases (
        alias TEXT PRIMARY KEY, item_id TEXT NOT NULL, basis TEXT NOT NULL,
        FOREIGN KEY(item_id) REFERENCES items(item_id)
    );
    """)


def upsert():
    with os.fdopen(3, encoding="utf-8") as source:
        records = read_items(source, metrics)
    run = load_json((Path(os.environ["RUN_DIR"]) / "run.json").read_text(encoding="utf-8"))
    if not isinstance(run, dict) or not isinstance(run.get("run_id"), str) or not run["run_id"]:
        raise ValueError("run.json requires run_id")
    # Save only public run metadata, never environment/provider configuration.
    metadata = {key: run.get(key) for key in
                ("run_id", "started_at", "as_of_date", "mode", "previous_run_id")}
    prepared = []
    for item in records:
        payload = version_payload(item, root)
        if item["version_id"] != digest(canonical(payload)):
            raise ValueError("version_id does not match evidence-v1 payload")
        aliases = item.get("aliases", [])
        if not isinstance(aliases, list):
            raise ValueError("aliases must be an array")
        for alias in aliases:
            if not isinstance(alias, dict) or any(
                not isinstance(alias.get(k), str) or not alias[k] for k in ("item_id", "basis")
            ):
                raise ValueError("Each alias requires item_id and an explicit matching basis")
        prepared.append((item, canonical(payload), aliases))

    changes = []
    with db:
        db.execute("BEGIN IMMEDIATE")
        existing_run = db.execute("SELECT metadata FROM runs WHERE run_id=?", (run["run_id"],)).fetchone()
        if existing_run and existing_run[0] != canonical(metadata):
            raise ValueError("Existing run metadata must not change")
        db.execute("INSERT OR IGNORE INTO runs VALUES (?, ?)", (run["run_id"], canonical(metadata)))
        for ordinal, (item, payload, aliases) in enumerate(prepared):
            iid, vid = item["item_id"], item["version_id"]
            # An existing evidence path may be reused only for identical content.
            # New content must have a new immutable asset path.
            incoming_hashes = load_json(payload)
            for stored_json, stored_payload in db.execute("SELECT item_json, hash_payload FROM versions"):
                stored, hashes = load_json(stored_json), load_json(stored_payload)
                for field, hash_field in (("text_path", "text_sha256"), ("segments_path", "segments_sha256")):
                    if item[field] is not None and item[field] == stored[field] and incoming_hashes[hash_field] != hashes[hash_field]:
                        raise ValueError("Referenced asset path changed; retain old assets and use a new path")
            mapped = db.execute("SELECT item_id FROM aliases WHERE alias=?", (iid,)).fetchone()
            if mapped and mapped[0] != iid:
                raise ValueError("Use the canonical item returned by get for alias ingestion")
            old = db.execute("SELECT latest_version FROM items WHERE item_id=?", (iid,)).fetchone()
            change = "new" if old is None else "unchanged" if old[0] == vid else "changed"
            db.execute("INSERT OR IGNORE INTO versions VALUES (?, ?, ?, ?, ?)",
                       (iid, vid, canonical(item), payload, run["run_id"]))
            db.execute("""INSERT INTO items VALUES (?, ?, ?)
                          ON CONFLICT(item_id) DO UPDATE SET latest_version=excluded.latest_version""",
                       (iid, vid, run["run_id"]))
            for alias in aliases:
                aid = alias["item_id"]
                occupied = db.execute("SELECT item_id FROM items WHERE item_id=?", (aid,)).fetchone()
                mapped = db.execute("SELECT item_id FROM aliases WHERE alias=?", (aid,)).fetchone()
                if occupied and aid != iid and alias.get("merge_existing") is True:
                    # Explicit confirmed reconciliation: retire only the current
                    # duplicate pointer, retaining all versions and observations.
                    # Version-pinned get below still resolves historical IDs.
                    db.execute("UPDATE aliases SET item_id=? WHERE item_id=?", (iid, aid))
                    db.execute("DELETE FROM items WHERE item_id=?", (aid,))
                    occupied = None
                if (occupied and aid != iid) or (mapped and mapped[0] != iid):
                    raise ValueError("Alias conflicts with an existing identity; explicit reconciliation required")
                db.execute("INSERT OR IGNORE INTO aliases VALUES (?, ?, ?)", (aid, iid, alias["basis"]))
            db.execute("INSERT INTO observations VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (os.environ["INVOCATION_ID"], ordinal, run["run_id"], iid, vid, canonical(item), change))
            changes.append({"item_id": iid, "version_id": vid, "change": change})
    return changes


def export_item(row):
    item = load_json(row[0])
    aliases = db.execute("SELECT alias, basis FROM aliases WHERE item_id=? ORDER BY alias",
                         (item["item_id"],)).fetchall()
    if aliases:
        item["aliases"] = [{"item_id": alias, "basis": basis} for alias, basis in aliases]
    return item


try:
    command = sys.argv[1]
    db = connect(create=command == "init")
    if command == "init":
        initialize()
        output = []
    elif command == "upsert":
        output = upsert()
    elif command == "list":
        output = [export_item(row) for row in db.execute("""
            SELECT v.item_json FROM items i JOIN versions v
            ON i.item_id=v.item_id AND i.latest_version=v.version_id ORDER BY i.item_id
        """).fetchall()]
    else:
        iid = sys.argv[2]
        mapped = db.execute("SELECT item_id FROM aliases WHERE alias=?", (iid,)).fetchone()
        if len(sys.argv) == 4:
            row = db.execute("SELECT item_json FROM versions WHERE item_id=? AND version_id=?",
                             (iid, sys.argv[3])).fetchone()
            if row is None and mapped:
                row = db.execute("SELECT item_json FROM versions WHERE item_id=? AND version_id=?",
                                 (mapped[0], sys.argv[3])).fetchone()
        else:
            iid = mapped[0] if mapped else iid
            row = db.execute("""SELECT v.item_json FROM items i JOIN versions v
                ON i.item_id=v.item_id AND i.latest_version=v.version_id WHERE i.item_id=?""", (iid,)).fetchone()
        if row is None:
            raise LookupError("Requested item/version not found")
        output = [export_item(row)]
    # Counts are exported in receipts so tests/reporting never inspect SQLite.
    metrics["store_counts"] = {name: db.execute(f"SELECT count(*) FROM {name}").fetchone()[0]
                               for name in ("items", "versions", "observations")}
    for record in output:
        print(canonical(record))
        metrics["output_count"] += 1
except (ValueError, TypeError, UnicodeError) as exc:
    metrics["errors"].append("Invalid input/configuration: " + str(exc))
    print(metrics["errors"][-1], file=sys.stderr)
    sys.exit(2)
except LookupError:
    metrics["errors"].append("Requested item/version not found")
    print(metrics["errors"][-1], file=sys.stderr)
    sys.exit(1)
except (OSError, sqlite3.Error):
    metrics["errors"].append("Storage/asset operation failed; check initialization, files and permissions")
    print(metrics["errors"][-1], file=sys.stderr)
    sys.exit(1)
finally:
    if db is not None:
        db.close()
    save_metrics(metrics)
PY
