"""FICTIONAL episode allowlist tests; no network or collected evidence."""
import pytest

from collectors import fetch_podcasts
from collectors.support import SourceFailure


def test_selected_episode_ids_skip_other_episodes_and_report_missing(monkeypatch):
    entries = [{'id': name, 'title': 'FICTIONAL ' + name,
                'link': 'https://fictional.example/' + name,
                'enclosures': [{'href': 'https://fictional.example/' + name + '.mp3', 'type': 'audio/mpeg'}]}
               for name in ('unselected', 'selected')]
    monkeypatch.setattr(fetch_podcasts, 'fetch_feed', lambda url: (entries, []))
    source = {'source_id': 'FICTIONAL', 'publisher_id': 'FICTIONAL',
              'url': 'https://fictional.example/feed', 'episode_ids': ['selected']}
    rows = list(fetch_podcasts.discover(source, None))
    assert len(rows) == 1 and rows[0]['native_id'] == 'selected'
    assert rows[0]['media_url'].endswith('/selected.mp3')
    source['episode_ids'].append('missing')
    output = fetch_podcasts.discover(source, None)
    assert next(output)['native_id'] == 'selected'
    with pytest.raises(SourceFailure, match='not found'):
        next(output)
