"""Pure evidence-v1 hashing, reusable by extraction; never opens the index."""
import hashlib
import math
import unicodedata
from lib.records import asset_path, canonical, load_json, reject_credentials


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def version_payload(item, root):
    payload = {key: item[key] for key in (
        "item_id", "source_id", "publisher_id", "kind", "title", "url", "published_at"
    )}
    payload["algorithm"] = "evidence-v1"
    payload["text_sha256"] = None
    payload["segments_sha256"] = None
    if item["text_path"] is not None:
        text = asset_path(root, item["text_path"]).read_text(encoding="utf-8")
        reject_credentials(text)
        text = unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))
        if not text.strip():
            raise ValueError("Empty substantive text asset")
        payload["text_sha256"] = digest(text)
    elif item["kind"] == "feed":
        raise ValueError("Written evidence requires a text asset")
    if item["segments_path"] is not None:
        segments = load_json(asset_path(root, item["segments_path"]).read_text(encoding="utf-8"))
        reject_credentials(segments)
        if not isinstance(segments, list) or not segments:
            raise ValueError("Segment asset must be a nonempty array")
        seen, previous_start, normalized = set(), -1, []
        for segment in segments:
            if not isinstance(segment, dict):
                raise ValueError("Segment must be an object")
            sid, text = segment.get("segment_id"), segment.get("text")
            start, end = segment.get("start_seconds"), segment.get("end_seconds")
            if not isinstance(sid, str) or not sid or sid in seen or not isinstance(text, str):
                raise ValueError("Invalid segment ID or text")
            if any(type(t) not in (int, float) or not math.isfinite(t) for t in (start, end)):
                raise ValueError("Invalid segment times")
            if not 0 <= start <= end or start < previous_start:
                raise ValueError("Invalid segment interval/order")
            seen.add(sid)
            previous_start = start
            # Numerically identical 1 and 1.0 have the same hash encoding.
            normalized.append({"segment_id": sid, "text": text,
                               "start_seconds": float(start), "end_seconds": float(end)})
        payload["segments_sha256"] = digest(canonical(normalized))
    return payload


def version_id(item, root):
    return digest(canonical(version_payload(item, root)))
