"""YouTube discovery with native IDs; no media/transcript extraction."""
import sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError
from collectors.support import SourceFailure, run_collector, utc_now, ydl_options


def discover(source, args):
    limit = args.max_items or None
    try:
        with YoutubeDL(ydl_options(extract_flat="in_playlist", playlistend=limit)) as ydl:
            info = ydl.extract_info(source["url"], download=False)
            if info is None:
                raise SourceFailure("YouTube discovery returned no metadata")
            entries = info.get("entries") if "entries" in info else [info]
            for entry in entries:
                if not entry:
                    raise SourceFailure("Unavailable video in discovery results")
                if entry.get("_type") in ("url", "url_transparent"):
                    entry = ydl.extract_info(entry["url"], download=False)
                if not entry or not entry.get("id") or not entry.get("title"):
                    raise SourceFailure("YouTube metadata lacks ID/title")
                timestamp = entry.get("timestamp") or entry.get("release_timestamp")
                yield {"item_id": "youtube:" + entry["id"], "native_id": entry["id"],
                       "source_id": source["source_id"], "publisher_id": source["publisher_id"],
                       "kind": "youtube", "title": entry["title"],
                       "url": entry.get("webpage_url") or "https://www.youtube.com/watch?v=" + entry["id"],
                       "published_at": datetime.fromtimestamp(timestamp, timezone.utc).isoformat().replace("+00:00", "Z") if timestamp else None,
                       "publication_date_only": entry.get("upload_date"), "retrieved_at": utc_now(),
                       "media_url": None, "duration_seconds": entry.get("duration")}
    except DownloadError:
        raise SourceFailure("YouTube request failed (network, access, or extractor error)") from None


if __name__ == "__main__":
    sys.exit(run_collector("youtube", discover))
