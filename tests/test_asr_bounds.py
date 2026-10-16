"""FICTIONAL timing estimates; recording bounds come from measured media."""
import pytest

from processing.transcripts import bound_asr_segments, normalize


def test_asr_tail_is_bounded_without_retiming_earlier_speech():
    segments = normalize([(0, 2, 'FICTIONAL first'), (2, 4, 'FICTIONAL tail'),
                          (4, 5, 'FICTIONAL beyond recording')])
    bounded, report = bound_asr_segments(segments, 3.5)
    assert bounded[0] == segments[0]
    assert bounded[1] == dict(segments[1], end_seconds=3.5)
    assert segments[1]['end_seconds'] == 4
    assert report == {'measured_duration_seconds': 3.5, 'clipped_end_count': 1,
                      'discarded_after_end_count': 1}
    assert [s['segment_id'] for s in bounded] == ['s-000001', 's-000002']


def test_asr_without_speech_in_recording_is_rejected():
    with pytest.raises(ValueError, match='No ASR speech'):
        bound_asr_segments(normalize([(4, 5, 'FICTIONAL')]), 3.5)


def test_youtube_format_is_selected_before_download(monkeypatch):
    from processing import media
    class FictionalDownloader:
        def __init__(self, options):
            assert options['format'] == 'bestaudio/best'
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def extract_info(self, url, download):
            assert download is False
            return {'id':'FICTIONAL'}
    monkeypatch.setattr(media, 'YoutubeDL', FictionalDownloader)
    assert media.youtube_info('https://fictional.example/video')['id'] == 'FICTIONAL'
