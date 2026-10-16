"""Collector-only discovery helpers. No extraction or evidence-index access."""
import argparse
import calendar
import hashlib
import os
import re
import math
from itertools import islice
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit, parse_qsl, urlencode
import xml.etree.ElementTree as ET

import feedparser
import requests
from lib.records import canonical, load_json, save_metrics, safe_public_url, reject_credentials


class SourceFailure(Exception):
    pass


class FeedTreeBuilder(ET.TreeBuilder):
    def doctype(self, name, pubid, system):
        # Reject actual XML declarations, not HTML examples inside CDATA/text.
        raise SourceFailure("Feed contains unsupported XML declarations")


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def public_url(url):
    safe_public_url(url)
    parsed = urlsplit(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("URLs must be public HTTP(S) URLs without embedded credentials")
    query = [(k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
             if not k.lower().startswith("utm_") and k.lower() not in ("fbclid", "gclid")]
    return urlunsplit((parsed.scheme, parsed.netloc.lower(), parsed.path, urlencode(query), ""))


def options():
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir")
    parser.add_argument("--max-items", type=int, default=int(os.getenv("MAX_ITEMS", "0")))
    parser.add_argument("--max-duration-minutes", type=float, default=float(os.getenv("MAX_DURATION_MINUTES", "20")))
    args = parser.parse_args()
    if args.max_items < 0 or not math.isfinite(args.max_duration_minutes) or args.max_duration_minutes <= 0:
        parser.error("max-items must be >= 0 (0 means unlimited); duration must be > 0")
    return args


def sources(run_dir, kind):
    definitions = load_json((Path(run_dir) / "config/sources.json").read_text(encoding="utf-8"))
    if not isinstance(definitions, list):
        raise ValueError("sources.json must be an array")
    seen = set()
    for source in definitions:
        reject_credentials(source)
        if not isinstance(source, dict) or any(not isinstance(source.get(k), str) or not source[k]
                                             for k in ("source_id", "publisher_id", "kind", "url")):
            raise ValueError("Source definition missing required strings")
        if source["kind"] not in ("feed", "youtube", "podcast") or source["source_id"] in seen:
            raise ValueError("Unknown source kind or repeated source_id")
        seen.add(source["source_id"])
        public_url(source["url"])
        if 'max_entries' in source and (type(source['max_entries']) is not int or source['max_entries']<1):
            raise ValueError('Source max_entries must be a positive integer')
        if 'episode_ids' in source:
            ids = source['episode_ids']
            if source['kind'] != 'podcast' or not isinstance(ids, list) or not ids or any(not isinstance(i, str) or not i.strip() for i in ids) or len(set(ids)) != len(ids):
                raise ValueError('episode_ids must be unique nonempty podcast native IDs')
    return [s for s in definitions if s["kind"] == kind]


def fetch_feed(url):
    try:
        response = requests.get(url, timeout=(10, 30), headers={
            "User-Agent": "Mozilla/5.0 (compatible; IntelligencePipeline/1.0)"
        })
        response.raise_for_status()
        content = response.content
        tree = ET.fromstring(content, parser=ET.XMLParser(target=FeedTreeBuilder()))
        if tree.tag.split("}")[-1] not in ("rss", "feed", "RDF"):
            raise SourceFailure("Response is not an RSS/Atom feed")
        parsed = feedparser.parse(content)
        elements = [e for e in tree.iter() if e.tag.split("}")[-1] in ("item", "entry")]
        return parsed.entries, elements
    except (requests.RequestException, ET.ParseError):
        raise SourceFailure("Feed retrieval/parsing failed") from None


def publication(entry):
    # Date-only metadata does not establish a precise publication timestamp.
    raw = entry.get("published")
    if raw and not re.search(r"\d{1,2}:\d{2}", raw):
        return None
    parsed = entry.get("published_parsed")
    if parsed:
        return datetime.fromtimestamp(calendar.timegm(parsed), timezone.utc).isoformat().replace("+00:00", "Z")
    return None


def candidate(source, entry, kind, iid, url, media=None):
    title = entry.get("title")
    if not isinstance(title, str) or not title.strip():
        raise SourceFailure("Discovered entry lacks title")
    return {"item_id": iid, "source_id": source["source_id"], "publisher_id": source["publisher_id"],
            "kind": kind, "title": title, "url": public_url(url), "published_at": publication(entry),
            "retrieved_at": utc_now(), "media_url": media}


def youtube_id(url):
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower()
    if host in ("youtu.be", "www.youtu.be"):
        vid = parsed.path.strip("/").split("/")[0]
    elif host in ("youtube.com", "www.youtube.com", "m.youtube.com"):
        vid = dict(parse_qsl(parsed.query)).get("v")
        if not vid and parsed.path.startswith(("/shorts/", "/embed/")):
            vid = parsed.path.split("/")[2]
    else:
        return None
    return vid if vid and re.fullmatch(r"[\w-]{11}", vid) else None


def episode_extra(element, base_url):
    extra = {"transcript_urls": [], "related_youtube_ids": []}
    for e in element.iter():
        local = e.tag.split("}")[-1]
        if local == "transcript" and e.attrib.get("url"):
            extra["transcript_urls"].append({"url": urljoin(base_url, e.attrib["url"]),
                                             "type": e.attrib.get("type")})
        if local == "duration" and e.text:
            try:
                parts = [float(x) for x in e.text.strip().split(":")]
                extra["duration_seconds"] = sum(v * 60 ** n for n, v in enumerate(reversed(parts)))
            except ValueError:
                pass
        # Links in the producer's episode metadata are leads; extraction still
        # verifies reciprocal links/producer identity before merging recordings.
        for url in re.findall(r'https?://[^\s<>"\']+', (e.text or "") + " " + " ".join(e.attrib.values())):
            vid = youtube_id(url.replace("&amp;", "&"))
            if vid and vid not in extra["related_youtube_ids"]:
                extra["related_youtube_ids"].append(vid)
    return extra


class QuietYDL:
    def debug(self, message):
        pass

    def warning(self, message):
        pass

    def error(self, message):
        pass


def ydl_options(**extra):
    return {"quiet": True, "no_warnings": True, "logger": QuietYDL(),
            "socket_timeout": 30, "retries": 1, **extra}


def run_collector(kind, discover):
    metrics = {"input_count": 0, "output_count": 0, "errors": [], "sources": [], "limited": False}
    code = 0
    try:
        args = options()
        definitions = sources(args.run_dir, kind)
        for source in definitions:
            if args.max_items and metrics["output_count"] >= args.max_items:
                metrics["limited"] = True
                metrics["sources"].append({"source_id": source["source_id"], "status": "not_searched_limit"})
                continue
            metrics["input_count"] += 1
            result = {"source_id": source["source_id"], "status": "completed", "output_count": 0}
            source_limit = source.get('max_entries')
            result['discovery_limit'] = source_limit
            if source.get('episode_ids'):
                result['episode_ids'] = source['episode_ids']
                metrics['limited'] = True
            if source_limit:
                metrics['limited'] = True
            discovery = None
            try:
                discovery = discover(source, args)
                selected = islice(discovery,source_limit) if source_limit else discovery
                for record in selected:
                    reject_credentials(record)
                    safe_public_url(record['url'])
                    if record.get('media_url') is not None:
                        safe_public_url(record['media_url'])
                    for transcript in record.get('transcript_urls',[]):
                        safe_public_url(transcript['url'])
                    duration = record.get("duration_seconds")
                    if duration is not None and duration > args.max_duration_minutes * 60:
                        message = f"Source {source['source_id']}: duration_limit: discovered media exceeds configured duration"
                        metrics["errors"].append(message)
                        print(message, file=sys.stderr)
                        result["status"] = "failed"
                        code = 1
                        continue
                    print(canonical(record), flush=True)
                    metrics["output_count"] += 1
                    result["output_count"] += 1
                    if args.max_items and metrics["output_count"] >= args.max_items:
                        metrics["limited"] = True
                        break
            except (SourceFailure, ValueError, TypeError, KeyError, OverflowError) as exc:
                result["status"] = "failed"
                reason = str(exc) if isinstance(exc, SourceFailure) else "Discovered source metadata is malformed"
                message = f"Source {source['source_id']}: {reason}"
                metrics["errors"].append(message)
                print(message, file=sys.stderr)
                code = 1
            finally:
                if hasattr(discovery,'close'):
                    discovery.close()
            metrics["sources"].append(result)
    except (ValueError, TypeError, OSError):
        metrics["errors"].append("Invalid collector arguments or source snapshot")
        print(metrics["errors"][-1], file=sys.stderr)
        code = 2
    finally:
        save_metrics(metrics)
    return code
