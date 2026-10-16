"""Small record-boundary checks; no collection, storage, or editorial logic."""
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

SECRET_FIELD = re.compile(r'(?:^|_)(?:api_?key|access_token|token|password|secret|client_secret|authorization|credentials|hf_token)$', re.I)
SECRET_VALUE = re.compile(r'\b(?:sk-[A-Za-z0-9_-]{20,}|(?:ghp|github_pat)_[A-Za-z0-9_-]{20,}|xox[baprs]-[A-Za-z0-9_-]{20,}|AKIA[A-Z0-9]{16})\b|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----')


def reject_credentials(value):
    """Reject secrets before persisting public records; never echo their values."""
    if isinstance(value, dict):
        for key, child in value.items():
            if SECRET_FIELD.search(key) and child not in (None, ''):
                raise ValueError('Credentials must come from environment variables')
            reject_credentials(child)
    elif isinstance(value, list):
        for child in value:
            reject_credentials(child)
    elif isinstance(value, str):
        active = [v for k,v in os.environ.items() if SECRET_FIELD.search(k) and len(v)>=8]
        if SECRET_VALUE.search(value) or any(secret in value for secret in active):
            raise ValueError('Credential value cannot be persisted')


def safe_public_url(value):
    parsed = urlsplit(value)
    if parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Expected public HTTP(S) URL without credentials')
    if any(SECRET_FIELD.search(k) or k.lower().startswith('x-amz-') for k,_ in parse_qsl(parsed.query)):
        raise ValueError('Credential-bearing URL cannot be persisted')
    reject_credentials(value)
    return value


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def load_json(text):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    def bad_constant(_):
        raise ValueError("Nonfinite JSON number")

    return json.loads(text, object_pairs_hook=unique, parse_constant=bad_constant)


def utc_timestamp(value):
    if not isinstance(value, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)", value
    ):
        raise ValueError("Expected ISO 8601 UTC timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.utcoffset() != timedelta(0):
        raise ValueError("Expected UTC timestamp")
    return parsed


def asset_path(root, value):
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or path.parts[:2] == ("data", "evidence"):
        raise ValueError("Asset path must stay outside the evidence index and within the repository")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root) or resolved.is_relative_to(root / "data/evidence"):
        raise ValueError("Asset path escapes its allowed location")
    return resolved


def validate_item(item):
    if not isinstance(item, dict):
        raise ValueError("Item must be an object")
    reject_credentials(item)
    for key in ("item_id", "source_id", "publisher_id", "kind", "title", "url",
                "retrieved_at", "version_id"):
        if not isinstance(item.get(key), str) or not item[key]:
            raise ValueError(f"Item requires nonempty string {key}")
    for key in ("published_at", "media_url", "text_path", "segments_path"):
        if key not in item or (item[key] is not None and not isinstance(item[key], str)):
            raise ValueError(f"Item requires string or null {key}")
    if item["kind"] not in ("feed", "youtube", "podcast"):
        raise ValueError("Invalid item kind")
    if item["kind"] == "feed" and item["segments_path"] is not None:
        raise ValueError("Written items must have null segments_path")
    if item["kind"] != "feed" and not item["segments_path"]:
        raise ValueError("Media items require segments_path")
    utc_timestamp(item["retrieved_at"])
    safe_public_url(item['url'])
    if item['media_url'] is not None:
        safe_public_url(item['media_url'])
    # Publication date strings deliberately remain unchecked here: filter emits
    # invalid_date for malformed dates rather than rejecting the entire stream.


def read_items(stream, metrics):
    items = []
    for number, line in enumerate(stream, 1):
        try:
            item = load_json(line)
            validate_item(item)
        except (ValueError, TypeError) as exc:
            # Never echo raw input, which may contain credentials.
            raise ValueError(f"Malformed Item JSONL at line {number}") from exc
        items.append(item)
        metrics["input_count"] += 1
    return items


def save_metrics(metrics):
    Path(os.environ["RECEIPT_METRICS"]).write_text(canonical(metrics) + "\n", encoding="utf-8")
