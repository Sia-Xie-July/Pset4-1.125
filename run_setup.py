"""Entry-point metadata, configuration validation and exact snapshots only."""
import argparse
import json
import re
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

from lib.records import canonical, load_json, reject_credentials

CONFIG_FILES = ("project.json", "sources.json", "editorial_policy.md")
PROMPT_FILES = ("select_items.md", "create_briefs.md", "write_articles.md", "write_video_scripts.md")
SECRET_KEY = re.compile(r"(?:^|_)(?:api_key|apikey|access_token|password|secret|client_secret|authorization|credentials|hf_token)$", re.I)


def no_credentials(value):
    reject_credentials(value)
    if isinstance(value, dict):
        for key, child in value.items():
            if SECRET_KEY.search(key) and child not in (None, ""):
                raise ValueError("Credentials must come from environment variables")
            no_credentials(child)
    elif isinstance(value, list):
        for child in value:
            no_credentials(child)
    elif isinstance(value, str):
        if re.search(r"\bsk-[A-Za-z0-9_-]{20,}", value):
            raise ValueError("Credential-like value in configuration")


def allocate():
    now = datetime.now(timezone.utc)
    run_id = now.strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:12]
    run_dir = Path("runs") / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    # This metadata also gives invalid-argument/config invocations a receipt home.
    metadata = {"run_id": run_id, "started_at": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
                "as_of_date": now.date().isoformat(), "mode": "live", "previous_run_id": None,
                "scope": "pipeline"}
    (run_dir / "run.json").write_text(canonical(metadata) + "\n", encoding="utf-8")
    print(run_dir.as_posix())


def configure(run_dir, arguments):
    parser = argparse.ArgumentParser(prog="bash run.sh", description="Intelligence pipeline entry point")
    parser.add_argument('--collection-only', action='store_true', help='Stop after collection (diagnostic use)')
    parser.add_argument("--mode", choices=("live", "example", "replay"), default="live")
    parser.add_argument("--config-dir", default="config")
    parser.add_argument("--prompts-dir", default="prompts")
    args = parser.parse_args(arguments)
    metadata = load_json((run_dir / "run.json").read_text(encoding="utf-8"))
    metadata["mode"] = args.mode
    metadata['scope'] = 'collection_only' if args.collection_only else 'pipeline'
    previous = []
    for path in Path("runs").glob("*/run.json"):
        if path.parent == run_dir:
            continue
        try:
            record = load_json(path.read_text(encoding="utf-8"))
            if record.get("mode") == args.mode and (path.parent / "config/project.json").is_file():
                previous.append((record["started_at"], record["run_id"]))
        except (ValueError, KeyError, OSError):
            continue
    metadata["previous_run_id"] = max(previous)[1] if previous else None
    (run_dir / "run.json").write_text(canonical(metadata) + "\n", encoding="utf-8")

    config, prompts = Path(args.config_dir), Path(args.prompts_dir)
    files = [(config / name, run_dir / "config" / name) for name in CONFIG_FILES]
    files += [(prompts / name, run_dir / "prompts" / name) for name in PROMPT_FILES]
    content = {}
    for source, target in files:
        if source.is_symlink() or not source.is_file():
            raise ValueError("Missing configuration/prompt file or unsupported symlink")
        value = source.read_bytes()
        text = value.decode("utf-8")
        if not text.strip():
            raise ValueError("Configuration and prompts must not be empty")
        content[target] = value
        no_credentials(text)
    project = load_json(content[run_dir / "config/project.json"].decode())
    if not isinstance(project, dict) or any(not isinstance(project.get(k), str) or not project[k].strip()
        for k in ("publication_name", "topic", "audience", "central_question")):
        raise ValueError("project.json requires four nonempty project strings")
    sources = load_json(content[run_dir / "config/sources.json"].decode())
    if not isinstance(sources, list) or not sources:
        raise ValueError("sources.json requires a nonempty source array")
    seen = set()
    for source in sources:
        if not isinstance(source, dict) or any(not isinstance(source.get(k), str) or not source[k].strip()
            for k in ("source_id", "publisher_id", "kind", "url")):
            raise ValueError("Invalid source definition")
        if source["kind"] not in ("feed", "youtube", "podcast") or source["source_id"] in seen:
            raise ValueError("Invalid source kind or duplicate source_id")
        seen.add(source["source_id"])
        if 'max_entries' in source and (type(source['max_entries']) is not int or source['max_entries']<1):
            raise ValueError('Source max_entries must be a positive integer')
        if 'episode_ids' in source:
            ids = source['episode_ids']
            if source['kind'] != 'podcast' or not isinstance(ids, list) or not ids or any(not isinstance(i, str) or not i.strip() for i in ids) or len(set(ids)) != len(ids):
                raise ValueError('episode_ids must be unique nonempty podcast native IDs')
        url = urlsplit(source["url"])
        if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password:
            raise ValueError("Source URLs must be HTTP(S) without embedded credentials")
        if any(SECRET_KEY.search(key) or key.lower().startswith("x-amz-") for key, _ in parse_qsl(url.query)):
            raise ValueError("Credential-bearing source URL cannot be snapshotted")
    no_credentials(project)
    no_credentials(sources)
    # Validation completes before any user file is copied. Preserve exact bytes.
    for target, value in content.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as output:
            output.write(value)


if __name__ == "__main__":
    try:
        if sys.argv[1] == "allocate":
            allocate()
        else:
            configure(Path(sys.argv[2]), sys.argv[3:])
    except (ValueError, TypeError, UnicodeError) as exc:
        print("Invalid run configuration: " + str(exc), file=sys.stderr)
        sys.exit(2)
    except OSError:
        print("Run metadata/snapshot filesystem operation failed", file=sys.stderr)
        sys.exit(1)
