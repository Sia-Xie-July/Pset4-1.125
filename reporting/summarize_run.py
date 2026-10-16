"""Saved-artifact and receipt reporting; never accesses the evidence index."""
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.records import canonical, load_json, save_metrics, utc_timestamp
from review.fingerprint import fingerprint


def read_document(path, default=None):
    if not path.is_file():
        return default
    return load_json(path.read_text(encoding="utf-8"))


def rows(run, name):
    path = run / name
    if not path.is_file():
        return None
    return [load_json(line) for line in path.read_text(encoding="utf-8").splitlines()]


def summarize(run):
    problems = []
    def document(path, default=None):
        try:
            value = read_document(path, default)
            if default is not None and not isinstance(value,type(default)):
                raise ValueError('Unexpected document shape')
            return value
        except (ValueError, OSError):
            problems.append({'stage':'reporting_inputs','artifact':str(path),'error':'Missing/unreadable or malformed artifact'})
            return default
    def stream(name):
        try:
            value = rows(run, name+'.jsonl')
            if value is not None and any(not isinstance(row,dict) for row in value):
                raise ValueError('Records must be objects')
            required = {'candidates':('item_id',),'items':('item_id',),'eligible':('item_id','kind','publisher_id'),
                        'changes':('change',),'decisions':('decision',),'series_stages':('stage','exit_code')}
            if value is not None and any(any(key not in row for key in required.get(name,())) for row in value):
                raise ValueError('Missing record field')
            return value
        except (ValueError, OSError):
            problems.append({'stage':name,'error':'Unreadable or malformed JSONL artifact'})
            return None
    metadata = document(run / "run.json", {})
    collection = document(run / "collection_status.json", {})
    artifacts = {name: stream(name) for name in
                 ("candidates", "items", "changes", "eligible", "exclusions")}
    stage_codes = {stage["stage"]: stage["exit_code"] for stage in collection.get("stages", [])}
    if stage_codes.get("filter_items") not in (None, 0):
        # A filter that could not assess input has not measured eligibility.
        # Redirection may leave an empty file, which is not a successful zero.
        artifacts["eligible"] = artifacts["exclusions"] = None
    if stage_codes.get('extract_content') == 2:
        artifacts['items'] = None
    if stage_codes.get('store.upsert') not in (None,0):
        artifacts['changes'] = None
    counts = {key: len(artifacts[name]) if artifacts[name] is not None else None for key, name in
              (("discovered", "candidates"), ("extracted", "items"), ("eligible", "eligible"), ("excluded", "exclusions"))}
    changes = Counter(row["change"] for row in artifacts["changes"] or [])
    for key in ("new", "changed", "unchanged"):
        counts[key] = changes[key] if artifacts["changes"] is not None else None
    decisions = stream('decisions')
    series = document(run/'series_status.json', {})
    series_stages = stream('series_stages') or []
    series_codes = {s['stage'].split('/')[-1]:s['exit_code'] for s in series_stages}
    if series_codes.get('select_items') not in (None, 0):
        decisions = None
    decision_counts = Counter(row['decision'] for row in decisions or [])
    for key, value in (('accepted','accept'),('rejected','reject'),('deferred','defer')):
        counts[key] = decision_counts[value] if decisions is not None else None
    for name, stage in (('articles','write_articles'),('video_scripts','write_video_scripts')):
        result = stream(name)
        counts[name] = len(result) if result is not None and series_codes.get(stage) in (None,0) else None
    terminals, running = {}, {}
    for path in (run / "logs").glob("*.json"):
        receipt = document(path)
        if not isinstance(receipt,dict) or 'invocation_id' not in receipt or 'status' not in receipt:
            continue
        (running if receipt["status"] == "running" else terminals)[receipt["invocation_id"]] = receipt
    receipts = list(terminals.values())
    latest = {}
    for path in sorted((run/'logs').glob('*.json'), key=lambda p:p.stat().st_mtime_ns):
        receipt = document(path)
        if isinstance(receipt,dict) and receipt.get('status') != 'running' and receipt.get('stage'):
            latest[receipt['stage']] = receipt
    for stage, count_keys in {'select_items':('accepted','rejected','deferred'),
                              'write_articles':('articles',),
                              'write_video_scripts':('video_scripts',)}.items():
        if latest.get(stage,{}).get('exit_code') not in (None,0):
            for key in count_keys:
                counts[key] = None
    collector_receipts = [r for r in receipts if r.get("parent_invocation_id") == collection.get("invocation_id")
                          and r["stage"].startswith("fetch_")]
    limited = [r["stage"] for r in collector_receipts if r.get("limited")]
    extraction_limit = latest.get('extract_content',{}).get('limited_count',0)
    evidence = artifacts["eligible"]
    unique = {row["item_id"]: row for row in evidence or []}
    by_kind = Counter(row["kind"] for row in unique.values())
    by_publisher = Counter(row["publisher_id"] for row in unique.values())
    sources = document(run / "config/sources.json", [])
    missing_kinds = sorted({"feed", "youtube", "podcast"} - {s["kind"] for s in sources})
    minimums_met = None if evidence is None else (len(unique) >= 12 and len(by_publisher) >= 6
                      and all(by_kind[k] >= 2 for k in ("feed", "youtube", "podcast")))
    failed = [stage for stage in collection.get("stages", [])+series_stages if stage["exit_code"] not in (None, 0)]
    if series.get('exit_code') not in (None,0) and not any(s['exit_code'] not in (None,0) for s in series_stages):
        failed.append({'stage':series.get('failed_stage','create_series'),'exit_code':series['exit_code']})
    for stage in ('select_items','create_briefs','write_articles','write_video_scripts','check_content','prepare_package'):
        receipt = latest.get(stage,{})
        if receipt.get('exit_code') not in (None,0):
            failed.append({'stage':stage,'exit_code':receipt['exit_code'],'errors':receipt.get('errors',[])})
    exit_code = int(os.environ.get("RUN_EXIT_CODE", '0'))
    incomplete = collection.get("exit_code") not in (0, None)
    if exit_code and not failed:
        failed.append({"stage": "run", "exit_code": exit_code})
    discovered = artifacts["candidates"]
    aliases = {alias['item_id']:row['item_id'] for row in artifacts['items'] or [] for alias in row.get('aliases',[])}
    duplicates = None if discovered is None else len(discovered) - len({aliases.get(r['item_id'],r['item_id']) for r in discovered})
    costs = [r["cost_usd"] for r in receipts if r.get("cost_usd") is not None]
    elapsed = None
    if metadata.get("started_at"):
        try:
            elapsed = max(0,(datetime.now(timezone.utc) - utc_timestamp(metadata["started_at"])).total_seconds())
        except ValueError:
            failed.append({'stage':'run_metadata','error':'Invalid started_at'})
    methods = []
    tools, models = [], []
    for receipt in receipts:
        tools.extend(receipt.get("tools", []))
        models.extend(receipt.get("models", []))
        for item in receipt.get("items", []):
            if item.get("transcription"):
                methods.append(item["transcription"])
    def distinct(values):
        return list({canonical(value): value for value in values}.values())
    review = document(run/'review.json', {})
    approval = document(run/'approval.json', {})
    package = document(run/'package/manifest.json', {})
    links = document(run/'package/publication_links.json', None)
    current = fingerprint(run)
    review_passed = review.get('passed') is True and review.get('review_id') == current
    stale = bool(review) and review.get('review_id') != current
    approval_valid = False
    if approval:
        from publishing.prepare_package import approval_matches
        from lib.stage_runtime import OperationalFailure
        try:
            approval_matches(approval, current)
            approval_valid = True
        except ValueError:
            failed.append({'stage':'approval','error':'Invalid human approval'})
        except OperationalFailure as exc:
            failed.append({'stage':'approval','error':str(exc)})
    package_valid = bool(package) and package.get('review_id') == current and approval_valid
    if package_valid:
        import hashlib
        from lib.records import asset_path
        try:
            from publishing.prepare_package import publication_links
            publication_links(links)
            assets = package['assets']
            package_valid = len(assets)==9 and all(hashlib.sha256(asset_path(Path.cwd(),a['path']).read_bytes()).hexdigest()==a['sha256'] for a in assets)
        except (OSError,ValueError,KeyError,TypeError):
            package_valid = False
    if stale:
        failed.append({'stage':'check_content','error':'Stale review: inputs changed'})
    if review and review.get('passed') is not True:
        failed.append({'stage':'check_content','error':'Blocking review issues','issues':review.get('issues',[])})
    if package and not package_valid:
        failed.append({'stage':'prepare_package','error':'Package is stale, damaged, or lacks matching approval'})
    # A fresh passing assessment resolves a preceding failed mechanical review.
    # Collection or generation failures remain independently visible.
    if review_passed:
        failed = [failure for failure in failed if failure.get('stage','').removesuffix('.sh').split('/')[-1] != 'check_content']
    failed.extend(problems)
    status = 'failed'
    reason = 'Pipeline incomplete or has unresolved failures'
    if review_passed and not failed and not incomplete and not exit_code:
        status = 'ready_for_production' if package_valid else 'awaiting_review'
        reason = 'Approved package prepared; rendering and publication remain manual' if package_valid else 'Mechanical checks pass; human review and packaging remain'
    pending = sorted({r['stage'] for iid,r in running.items() if iid not in terminals and r['stage'] not in ('run','run.package','run.resume','summarize_run')})
    if pending:
        status = 'failed'
        failed.extend({'stage':s,'error':'Invocation has no final receipt'} for s in pending)
    manual = package.get('manual_steps') or ['Inspect the actual drafts and evidence; record a human decision in approval.json',
        'Prepare the approved production package', 'Render videos in Google Vids or HeyGen and publish on Substack and YouTube; verify and record links']
    return {
        "run_id": metadata.get("run_id", run.name), "run_dir": run.resolve().relative_to(Path.cwd()).as_posix(), "mode": metadata.get("mode"),
        "as_of_date": metadata.get("as_of_date"), "scope": metadata.get('scope','pipeline'),
        "status": status, "pipeline_complete": review_passed,
        "status_reason": reason,
        "collection_status": "not_run" if not collection else "incomplete" if incomplete else "completed",
        "collection_exit_code": collection.get('exit_code'), "collector_exit_codes": collection.get("collector_exit_codes", {}),
        "counts": counts, "duplicate_observations": duplicates,
        "source_coverage": {"distinct_items": len(unique) if evidence is not None else None,
                            "by_kind": dict(by_kind) if evidence is not None else None,
                            "by_publisher": dict(by_publisher) if evidence is not None else None},
        "coverage_incomplete": incomplete or bool(limited) or bool(extraction_limit) or bool(missing_kinds) or minimums_met is not True,
        "coverage_limits": {"bounded_collectors": limited, "unconfigured_kinds": missing_kinds,
                            "assignment_minimums_met": minimums_met, "extraction_items_not_processed_limit":extraction_limit},
        "failed_or_incomplete_stages": failed,
        "historical_failed_invocations": [{'stage':r['stage'],'invocation_id':r['invocation_id'],
            'exit_code':r.get('exit_code'),'errors':r.get('errors',[])} for r in receipts if r.get('exit_code') not in (None,0)],
        "not_run": [name for name,path in [('collection','collection_status.json'),('create_series','series_status.json'),('editorial_selection','decisions.jsonl'),('briefs','briefs.jsonl'),('articles','articles.jsonl'),('video_scripts','video_scripts.jsonl'),('review','review.json'),('package','package/manifest.json')] if not (run/path).exists()],
        "elapsed_seconds": elapsed, "tools": distinct(tools), "models": distinct(models),
        "transcription_methods": distinct(methods),
        "cost_usd": sum(costs) if costs else None,
        "cost_scope": "Known subtotal across all retained invocation attempts; null costs remain unknown",
        "cost_is_estimate": any(r.get('cost_is_estimate',False) for r in receipts),
        "cost_total_complete": all(r.get('cost_usd') is not None for r in receipts) if receipts else False,
        "unknown_cost_stages": sorted({r["stage"] for r in receipts if r.get("cost_usd") is None}),
        "remaining_manual_actions": manual,
        "publication_links": links, "publication_verified": False,
        "unmatched_running_stages": pending,
    }


if __name__ == "__main__":
    metrics = {"input_count": None, "output_count": 0, "errors": []}
    try:
        print(canonical(summarize(Path(os.environ["RUN_DIR"]))))
        metrics["output_count"] = 1
    except (ValueError, TypeError, KeyError):
        metrics["errors"].append("Malformed run artifact or receipt prevents summary")
        print(metrics["errors"][-1], file=sys.stderr)
        sys.exit(2)
    except OSError:
        metrics["errors"].append("Run artifacts cannot be read for summary")
        print(metrics["errors"][-1], file=sys.stderr)
        sys.exit(1)
    finally:
        save_metrics(metrics)
