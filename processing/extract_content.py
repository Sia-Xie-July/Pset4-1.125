"""Substantive extraction, immutable assets, reuse and recording reconciliation."""
import argparse
import hashlib
import importlib.metadata
import math
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import requests
import trafilatura
from yt_dlp.utils import DownloadError
from data.versioning import version_id
from lib.records import canonical, load_json, save_metrics, utc_timestamp, asset_path, safe_public_url, reject_credentials
from processing import media
from processing.transcripts import bound_asr_segments


def options():
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir")
    parser.add_argument("--max-items", type=int, default=int(os.getenv("MAX_ITEMS", "0")))
    parser.add_argument("--max-duration-minutes", type=float, default=float(os.getenv("MAX_DURATION_MINUTES", "20")))
    args = parser.parse_args()
    if args.max_items < 0 or not math.isfinite(args.max_duration_minutes) or args.max_duration_minutes <= 0:
        parser.error("max-items must be >=0; duration must be positive and finite")
    return args


def validate_candidate(item):
    if not isinstance(item, dict):
        raise ValueError("Candidate must be an object")
    reject_credentials(item)
    for key in ("item_id", "source_id", "publisher_id", "kind", "title", "url", "retrieved_at"):
        if not isinstance(item.get(key), str) or not item[key]:
            raise ValueError("Candidate lacks required strings")
    for key in ("published_at", "media_url"):
        if key not in item or item[key] is not None and not isinstance(item[key], str):
            raise ValueError("Candidate lacks nullable metadata")
    if item["kind"] not in ("feed", "podcast", "youtube"):
        raise ValueError("Invalid Candidate kind")
    if item["kind"] == "podcast" and not item["media_url"]:
        raise ValueError("Podcast Candidate requires an audio enclosure URL")
    for url in (item["url"], item["media_url"]):
        if url is not None:
            safe_public_url(url)
            parsed = urlsplit(url)
            if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
                raise ValueError("Invalid source URL")
    utc_timestamp(item["retrieved_at"])
    duration = item.get("duration_seconds")
    if duration is not None and (type(duration) not in (int, float) or not math.isfinite(duration) or duration <= 0):
        raise ValueError("Invalid duration metadata")
    if not isinstance(item.get("transcript_urls", []), list) or not isinstance(item.get("related_youtube_ids", []), list):
        raise ValueError("Invalid transcript/reconciliation metadata")
    for record in item.get("transcript_urls", []):
        if not isinstance(record, dict) or not isinstance(record.get("url"), str):
            raise ValueError("Invalid transcript link")
        safe_public_url(record['url'])


def store(command, *args):
    result = subprocess.run(["bash", "data/store.sh", command, *args], capture_output=True, text=True)
    if result.returncode:
        raise media.ItemFailure("Evidence store query failed; initialize it with store.sh init")
    return [load_json(line) for line in result.stdout.splitlines()]


def verify_saved(item, root):
    if version_id(item, root) != item["version_id"]:
        raise media.ItemFailure("Stored evidence assets no longer match their version")
    if item.get("media_path"):
        path = asset_path(root, item["media_path"])
        if not path.is_file() or media.file_hash(path) != item.get("media_sha256"):
            raise media.ItemFailure("Stored original media is missing or corrupt")


def asset(content, directory, suffix):
    reject_credentials(content.decode('utf-8'))
    file = directory / ("asset" + suffix)
    file.write_bytes(content)
    path, _ = media.retain_file(file, Path("data/assets"), suffix)
    return path


def enforce_duration(seconds, maximum):
    if seconds is not None and seconds > maximum * 60:
        raise media.ItemFailure("duration_limit: media exceeds --max-duration-minutes")


def record_tool(metrics, name):
    if any(isinstance(tool, dict) and tool.get("name") == name for tool in metrics["tools"]):
        return
    result = subprocess.run([name, "-version"], capture_output=True, text=True, timeout=10)
    metrics["tools"].append({"name": name, "version": result.stdout.splitlines()[0] if result.stdout else None})


def link_urls(text):
    return re.findall(r'https?://[^\s<>"\']+', text or "")


def same_recording(item, other):
    if item["kind"] == "feed" or other["kind"] == "feed":
        return None
    if item.get("media_sha256") and item["media_sha256"] == other.get("media_sha256"):
        return "Exact original recording bytes, including reposted discovery routes"
    if item["publisher_id"] != other["publisher_id"]:
        return None
    if {item["kind"], other["kind"]} == {"youtube", "podcast"}:
        youtube, podcast = (item, other) if item["kind"] == "youtube" else (other, item)
        vid = youtube.get("native_id") or youtube["item_id"].removeprefix("youtube:")
        if vid in podcast.get("related_youtube_ids", []) and podcast["url"] in youtube.get("description_urls", []):
            return "Reciprocal producer episode/YouTube links with shared publisher_id"
    return None


def reconcile(item, pool, metrics):
    for other in pool:
        if item["item_id"] == other["item_id"]:
            continue
        basis = same_recording(item, other)
        if basis:
            aliases = {a["item_id"]: a for a in other.get("aliases", [])}
            aliases[item["item_id"]] = {"item_id": item["item_id"], "basis": basis,
                                        "merge_existing": any(p["item_id"] == item["item_id"] for p in pool)}
            # Preserve representative transcript and its route-specific offsets.
            result = dict(other, retrieved_at=item["retrieved_at"], aliases=list(aliases.values()))
            # A newer transport copy never refreshes the underlying recording.
            if item["published_at"] and other["published_at"]:
                try:
                    if utc_timestamp(item["published_at"]) < utc_timestamp(other["published_at"]):
                        result["published_at"] = item["published_at"]
                except ValueError:
                    result["published_at"] = None
            routes = other.get("discovery_routes", []) + [{"item_id": item["item_id"], "kind": item["kind"], "url": item["url"]}]
            result["discovery_routes"] = list({canonical(r): r for r in routes}.values())
            result["deduplication_basis"] = basis
            result["version_id"] = version_id(result, Path.cwd())
            metrics["reconciliations"].append({"route_id": item["item_id"], "item_id": other["item_id"], "basis": basis})
            return result
        if item["publisher_id"] == other["publisher_id"] and {item["kind"], other["kind"]} == {"youtube", "podcast"}:
            youtube, podcast = (item, other) if item["kind"] == "youtube" else (other, item)
            vid = youtube.get("native_id") or youtube["item_id"].removeprefix("youtube:")
            if vid in podcast.get("related_youtube_ids", []):
                raise media.ItemFailure("Unconfirmed episode/YouTube match; verify reciprocal links before counting evidence")
    return item


def preserve_publication_date(item, previous, unchanged):
    if previous and unchanged and item['published_at'] and previous['published_at']:
        try:
            if utc_timestamp(item['published_at']) > utc_timestamp(previous['published_at']):
                item['published_at'] = previous['published_at']
                item['publication_date_basis'] = 'Retained earliest verified publication date for unchanged underlying content'
        except ValueError:
            pass  # Leave malformed/unknown metadata for the mechanical filter.


def extract(candidate, previous, args, directory, metrics):
    root = Path.cwd()
    warnings = []
    if previous:
        verify_saved(previous, root)
    if candidate["kind"] == "feed":
        host = urlsplit(candidate['url']).hostname
        if host in ('youtu.be','www.youtu.be','youtube.com','www.youtube.com','m.youtube.com'):
            raise media.ItemFailure('RSS discovery route points to YouTube media, not substantive written evidence; use the YouTube collector')
        response = requests.get(candidate["url"], timeout=(10, 30))
        response.raise_for_status()
        text = trafilatura.extract(response.content, include_comments=False, include_tables=True)
        if not text or not text.strip():
            raise media.ItemFailure("Unable to retrieve substantive written content")
        text = unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))
        item = dict(candidate, text_path=asset(text.encode(), directory, ".txt"), segments_path=None,
                    extraction_method="full_text", transcript_method=None, transcript_model=None)
        preserve_publication_date(item, previous, previous is not None and item['text_path']==previous['text_path'])
        item["version_id"] = version_id(item, root)
        reused = previous is not None and item["version_id"] == previous["version_id"]
        item["extraction_reused"] = reused
        item["reuse_basis"] = "fresh substantive text and metadata hash match" if reused else None
        return item

    enforce_duration(candidate.get("duration_seconds"), args.max_duration_minutes)
    info = media.youtube_info(candidate["url"]) if candidate["kind"] == "youtube" else None
    if info is not None:
        enforce_duration(info.get("duration"), args.max_duration_minutes)
        candidate = dict(candidate, title=info.get("title") or candidate["title"])
    segments, provenance = media.timed_native(candidate, info, warnings)
    # Fresh native captions are the evidence content. When both they and the
    # evidence metadata still match, keep the already hash-verified download.
    # ASR-only recordings still require a fresh recording-byte comparison.
    if previous and info is not None and segments and info.get("duration") is not None:
        saved_segments = load_json(asset_path(root, previous["segments_path"]).read_text(encoding="utf-8"))
        if segments == saved_segments and abs(info["duration"] - previous["duration_seconds"]) <= 2:
            item = dict(previous, **candidate)
            item.update(transcription=provenance, transcript_method=provenance["method"],
                        transcript_model=provenance["model"], warnings=warnings,
                        description_urls=link_urls(info.get("description", "")),
                        duration_seconds=previous["duration_seconds"])
            preserve_publication_date(item, previous, True)
            item["version_id"] = version_id(item, root)
            if item["version_id"] == previous["version_id"]:
                item.update(extraction_reused=True,
                            reuse_basis="fresh native transcript and evidence metadata match; retained media hash verified")
                return item
    original = media.youtube_download(info, directory) if info else media.podcast_download(candidate["media_url"], directory)
    seconds = media.duration(original)
    record_tool(metrics, "ffprobe")
    enforce_duration(seconds, args.max_duration_minutes)
    media_path, media_digest = media.retain_file(original, Path("data/media"), original.suffix)
    if segments and segments[-1]["end_seconds"] > seconds + 2:
        warnings.append("Native timestamps exceed recording duration; falling back to faster-whisper")
        segments, provenance = None, None
    reused = False
    if segments is None and previous and media_digest == previous.get("media_sha256") and previous.get("transcript_method") == "faster_whisper":
        # No usable native transcript now; reuse the verified prior ASR result
        # only when freshly downloaded recording bytes still match.
        segments = load_json(asset_path(root, previous["segments_path"]).read_text(encoding="utf-8"))
        provenance = dict(previous["transcription"], executed=False)
        reused = True
    if segments is None:
        record_tool(metrics, "ffmpeg")
        segments, provenance = media.transcribe(original, directory)
    if provenance["method"] == "faster_whisper":
        segments, bounds = bound_asr_segments(segments, seconds)
        if bounds["clipped_end_count"] or bounds["discarded_after_end_count"]:
            provenance = dict(provenance, timestamp_bounds=bounds)
            warnings.append("ASR tail limited to measured audio endpoint; see timestamp_bounds")
    if segments[-1]["end_seconds"] > seconds + 2:
        raise media.ItemFailure("Transcript timestamps exceed recording duration")
    item = dict(candidate, media_path=media_path, media_sha256=media_digest, duration_seconds=seconds,
                text_path=asset(("\n".join(s["text"] for s in segments) + "\n").encode(), directory, ".txt"),
                segments_path=asset((canonical(segments) + "\n").encode(), directory, ".segments.json"),
                transcription=provenance, transcript_method=provenance["method"], transcript_model=provenance["model"],
                warnings=warnings, description_urls=link_urls(info.get("description", "")) if info else [])
    preserve_publication_date(item, previous, previous is not None and media_digest==previous.get('media_sha256'))
    item["version_id"] = version_id(item, root)
    reused = reused or previous is not None and item["version_id"] == previous["version_id"]
    item["extraction_reused"] = reused
    item["reuse_basis"] = "verified content hash match after fresh retrieval" if reused else None
    return item


def main(metrics):
    args = options()
    records = []
    for number, line in enumerate(sys.stdin, 1):
        item = load_json(line)
        validate_candidate(item)
        records.append(item)
        metrics["input_count"] += 1
    # All structural validation precedes downloads; a malformed stream is exit 2.
    if args.max_items and len(records) > args.max_items:
        metrics["limited_count"] = len(records) - args.max_items
        records = records[:args.max_items]
    pool = store("list")
    for row in pool:
        verify_saved(row, Path.cwd())
    known = {row["item_id"]: row for row in pool}
    for row in pool:
        for alias in row.get("aliases", []):
            known[alias["item_id"]] = row
    asset_path(Path.cwd(),'data/media').mkdir(parents=True, exist_ok=True)
    emitted = {}
    for candidate in records:
        try:
            old = known.get(candidate["item_id"])
            if old and old["item_id"] != candidate["item_id"]:
                # Refresh the representative route to detect changed evidence,
                # rather than assigning mirror offsets to its segments.
                candidate = dict(old, retrieved_at=candidate["retrieved_at"])
            with tempfile.TemporaryDirectory(prefix=".extract-", dir="data/media") as temp:
                item = extract(candidate, old, args, Path(temp), metrics)
                item = reconcile(item, list(emitted.values()) + pool, metrics)
            verify_saved(item, Path.cwd())
            emitted[item["item_id"]] = item
            known[item["item_id"]] = item
            provenance = item.get("transcription")
            metrics["items"].append({"item_id": item["item_id"], "status": "completed",
                                      "transcription": provenance, "reused": item.get("extraction_reused", False),
                                      "warnings": item.get("warnings", [])})
            if provenance and provenance["method"] == "faster_whisper" and provenance not in metrics["models"]:
                metrics["models"].append(provenance)
                metrics["tools"].extend({"name": name, "version": importlib.metadata.version(name)}
                                        for name in ("faster-whisper", "av"))
        except (media.ItemFailure, requests.RequestException, DownloadError, OSError, ValueError, RuntimeError,
                subprocess.SubprocessError, ImportError, TypeError, KeyError) as exc:
            reason = str(exc) if isinstance(exc, media.ItemFailure) else f"Retrieval, transcript, or tool operation failed ({type(exc).__name__})"
            error = f"Item {candidate['item_id']}: {reason}"
            metrics["errors"].append(error)
            metrics["items"].append({"item_id": candidate["item_id"], "status": "failed", "reason": reason})
            print(error, file=sys.stderr)
    for item in emitted.values():
        print(canonical(item), flush=True)
        metrics["output_count"] += 1
    return 1 if metrics["errors"] else 0


if __name__ == "__main__":
    metrics = {"input_count": 0, "output_count": 0, "errors": [], "items": [], "models": [], "reconciliations": [], "limited_count": 0,
               "tools": [{"name": p, "version": importlib.metadata.version(p)} for p in ("requests", "yt-dlp", "trafilatura")]}
    try:
        code = main(metrics)
    except (ValueError, TypeError, KeyError):
        metrics["errors"].append("Invalid extraction arguments, Candidate JSONL, or run configuration")
        print(metrics["errors"][-1], file=sys.stderr)
        code = 2
    except OSError:
        metrics['errors'].append('Extraction filesystem or retained-asset operation failed')
        print(metrics['errors'][-1], file=sys.stderr)
        code = 1
    except media.ItemFailure as exc:
        metrics["errors"].append(str(exc))
        print(str(exc), file=sys.stderr)
        code = 1
    finally:
        save_metrics(metrics)
    sys.exit(code)
