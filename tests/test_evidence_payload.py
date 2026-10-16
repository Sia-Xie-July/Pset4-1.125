"""FICTIONAL payload: retain full evidence without duplicating media prose."""
from lib.evidence import Evidence


def test_model_payload_keeps_full_text_or_all_timed_segments():
    evidence = object.__new__(Evidence)
    written, media = ('FICTIONAL-feed','v1'), ('FICTIONAL-media','v2')
    evidence.items = {written: {'kind':'feed'}, media: {'kind':'podcast'}}
    evidence.text = {written:'FICTIONAL full article', media:'FICTIONAL full transcript'}
    evidence.segments = {written:[], media:[{'segment_id':'s-000001',
        'start_seconds':0,'end_seconds':2,'text':'FICTIONAL full transcript'}]}
    rows = evidence.payload()
    assert rows[0]['text'] == evidence.text[written]
    assert rows[1]['text'] is None and rows[1]['segments'] == evidence.segments[media]
    assert evidence.text[media] == 'FICTIONAL full transcript'
    assert evidence.payload({media}) == [rows[1]]
