"""Invocation bookkeeping and snapshots, not editorial or rendering logic."""
import os
import sys
import time
from pathlib import Path

from lib.records import load_json, save_metrics


class OperationalFailure(Exception):
    pass


class InvalidInput(ValueError):
    pass


def records(stream):
    try:
        return [load_json(line) for line in stream]
    except (ValueError, TypeError) as exc:
        raise InvalidInput("Malformed JSONL input") from exc


def run_directory():
    directory = Path(os.environ["RUN_DIR"]).resolve()
    try:
        directory.relative_to(Path.cwd())
    except ValueError:
        raise InvalidInput("RUN_DIR must be within the repository") from None
    return directory


def snapshots(run, stage):
    try:
        metadata = load_json((run / "run.json").read_text(encoding="utf-8"))
        project = load_json((run / "config/project.json").read_text(encoding="utf-8"))
        policy = (run / "config/editorial_policy.md").read_text(encoding="utf-8")
        prompt = (run / "prompts" / (stage + ".md")).read_text(encoding="utf-8")
    except (OSError, ValueError):
        raise InvalidInput("Missing or malformed run configuration/prompt snapshots") from None
    if not isinstance(project, dict) or any(not isinstance(project.get(k), str) or not project[k].strip()
        for k in ("publication_name", "topic", "audience", "central_question")) or not policy.strip() or not prompt.strip():
        raise InvalidInput("Project, policy and stage prompt snapshots must be populated")
    return metadata, project, policy, prompt


def run_stage(main):
    metrics = {"input_count": 0, "output_count": 0, "errors": [], "models": [], "cost_usd": None,
               "cost_is_estimate": False, "model_calls": []}
    started = time.monotonic()
    code = 0
    try:
        main(metrics)
    except InvalidInput as exc:
        metrics["errors"].append(str(exc))
        print(str(exc), file=sys.stderr)
        code = 2
    except (ValueError, TypeError, KeyError):
        metrics["errors"].append("Invalid configuration/input or malformed model output; inspect saved model output and schemas")
        print(metrics["errors"][-1], file=sys.stderr)
        code = 2
    except OperationalFailure as exc:
        metrics["errors"].append(str(exc))
        print(str(exc), file=sys.stderr)
        code = 1
    except OSError:
        metrics["errors"].append("Stage filesystem or source-asset operation failed")
        print(metrics["errors"][-1], file=sys.stderr)
        code = 1
    finally:
        metrics["duration_seconds"] = time.monotonic() - started
        metrics["model_duration_seconds"] = sum(call["duration_seconds"] for call in metrics["model_calls"])
        save_metrics(metrics)
    return code
