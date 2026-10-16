"""Mechanical Candidate JSONL validation. Retain valid lines; no collection."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.records import canonical, load_json, utc_timestamp


def validate(record):
    if not isinstance(record, dict):
        raise ValueError
    for key in ("item_id", "source_id", "publisher_id", "kind", "title", "url", "retrieved_at"):
        if not isinstance(record.get(key), str) or not record[key]:
            raise ValueError
    for key in ("published_at", "media_url"):
        if key not in record or record[key] is not None and not isinstance(record[key], str):
            raise ValueError
    if record["kind"] not in ("feed", "youtube", "podcast"):
        raise ValueError
    utc_timestamp(record["retrieved_at"])


if __name__ == "__main__":
    invalid = False
    for line_number, line in enumerate(sys.stdin, 1):
        try:
            record = load_json(line)
            validate(record)
            print(canonical(record))
        except (ValueError, TypeError):
            print(f"Malformed Candidate record at merged line {line_number}; omitted", file=sys.stderr)
            invalid = True
    sys.exit(2 if invalid else 0)
