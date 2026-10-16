"""Discover written articles; substantive retrieval belongs to extraction."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from collectors.support import SourceFailure, candidate, fetch_feed, public_url, run_collector


def discover(source, args):
    entries, _ = fetch_feed(source["url"])
    for entry in entries:
        url = entry.get("link")
        if not url:
            raise SourceFailure("Written entry lacks source URL")
        yield candidate(source, entry, "feed", "feed:" + public_url(url), url)


if __name__ == "__main__":
    sys.exit(run_collector("feed", discover))
