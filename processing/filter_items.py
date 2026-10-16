"""Mechanical UTC date eligibility only; no editorial judgment or index access."""
import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.records import canonical, load_json, read_items, save_metrics, utc_timestamp


def main(metrics):
    run_dir = Path(os.environ["RUN_DIR"])
    run = load_json((run_dir / "run.json").read_text(encoding="utf-8"))
    if not isinstance(run, dict) or not isinstance(run.get("as_of_date"), str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}", run["as_of_date"]
    ):
        raise ValueError("run.json requires as_of_date in YYYY-MM-DD format")
    upper = date.fromisoformat(run["as_of_date"])
    lower = upper - timedelta(days=29)
    items = read_items(sys.stdin, metrics)
    eligible, exclusions = [], []
    for item in items:
        value = item["published_at"]
        reason = None
        if value is None:
            reason, detail = "unknown_date", "Publication date is unknown"
        else:
            try:
                published = utc_timestamp(value).date()
            except ValueError:
                reason, detail = "invalid_date", "Publication date must be a valid ISO 8601 UTC timestamp"
            else:
                if published < lower:
                    reason, detail = "outside_window", f"Publication precedes inclusive window {lower} through {upper}"
                elif published > upper:
                    reason, detail = "future_date", f"Publication is after as-of date {upper}"
        if reason:
            exclusions.append({"item_id": item["item_id"], "version_id": item["version_id"],
                               "reason": reason, "detail": detail})
        else:
            eligible.append(item)

    # Validate the entire stream before replacing the previous exclusion artifact.
    temporary = run_dir / (".exclusions-" + os.environ["INVOCATION_ID"] + ".tmp")
    try:
        temporary.write_text("".join(canonical(row) + "\n" for row in exclusions), encoding="utf-8")
        temporary.replace(run_dir / "exclusions.jsonl")
    finally:
        temporary.unlink(missing_ok=True)
    metrics["excluded_count"] = len(exclusions)
    for item in eligible:
        print(canonical(item))
        metrics["output_count"] += 1


if __name__ == "__main__":
    metrics = {"input_count": 0, "output_count": 0, "errors": []}
    try:
        main(metrics)
    except (ValueError, TypeError, UnicodeError, OverflowError):
        metrics["errors"].append("Invalid run configuration or Item JSONL input")
        print(metrics["errors"][-1], file=sys.stderr)
        sys.exit(2)
    except OSError:
        metrics["errors"].append("Cannot read run metadata or write filter artifacts")
        print(metrics["errors"][-1], file=sys.stderr)
        sys.exit(1)
    finally:
        save_metrics(metrics)
