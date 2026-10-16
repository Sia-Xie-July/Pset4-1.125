"""Discover episode identities, audio enclosures, and producer transcript links."""
import hashlib
import sys
from pathlib import Path
from urllib.parse import urljoin
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from collectors.support import SourceFailure, candidate, episode_extra, fetch_feed, public_url, run_collector


def discover(source, args):
    entries, elements = fetch_feed(source["url"])
    wanted = set(source.get("episode_ids", []))
    found = set()
    for index, entry in enumerate(entries):
        if wanted and entry.get("id") not in wanted:
            continue
        media = next((e.get("href") for e in entry.get("enclosures", [])
                      if e.get("type", "").startswith("audio/") or e.get("href", "").split("?")[0].endswith((".mp3", ".m4a", ".ogg", ".wav"))), None)
        if not media:
            raise SourceFailure("Episode lacks an audio enclosure")
        media = public_url(urljoin(source["url"], media))
        native = entry.get("id") or entry.get("link") or media
        found.add(native)
        iid = "podcast:" + hashlib.sha256((source["source_id"] + "\n" + native).encode()).hexdigest()
        record = candidate(source, entry, "podcast", iid, entry.get("link") or media, media)
        record["native_id"] = native
        if index < len(elements):
            record.update(episode_extra(elements[index], source["url"]))
        yield record
    if wanted - found:
        raise SourceFailure("Configured podcast episode IDs were not found in the feed")


if __name__ == "__main__":
    sys.exit(run_collector("podcast", discover))
