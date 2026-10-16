"""Small-context transport contracts using explicitly synthetic evidence."""
from types import SimpleNamespace
from editorial.passages import passages
from editorial.local_briefs import generate as brief_generate
from content.local_documents import generate as document_generate


def evidence():
    keys = [('fictional-a', 'v1'), ('fictional-b', 'v1'), ('fictional-c', 'v1')]
    items = {key: {'kind': kind, 'publisher_id': key[0], 'title': 'FICTIONAL test',
                   'url': 'https://example.invalid', 'published_at': '2026-10-15T00:00:00Z'}
             for key, kind in zip(keys, ['feed', 'youtube', 'podcast'])}
    return SimpleNamespace(items=items,
        text={keys[0]: 'This synthetic example discusses testing code and review workflows, not a real observed result. ' * 20},
        segments={keys[1]: [{'segment_id': 's1', 'text': 'Synthetic coding review test.'}],
                  keys[2]: [{'segment_id': 's1', 'text': 'Synthetic podcast testing example.'}]}), keys


def test_literal_passage_bounds():
    ev, keys = evidence()
    result = passages(ev, keys[0], 'code review', maximum=2)
    assert len(result) == 2
    assert all(p['reference']['locator']['quote'] in ev.text[keys[0]] for p in result)
    assert all(len(p['text']) <= 600 for p in result)


def test_media_passage_preserves_contiguous_segment_references():
    ev, keys = evidence()
    ev.segments[keys[1]] = [{'segment_id': f's{i}', 'text': f'Synthetic review phrase {i}.'} for i in range(10)]
    result = passages(ev, keys[1], 'review', maximum=1)
    assert len(result[0]['references']) == 8
    assert result[0]['text'] == ' '.join(s['text'] for s in ev.segments[keys[1]][:8])


def test_compact_briefs_keep_exact_refs(monkeypatch):
    ev, keys = evidence()
    def fake(stage, run, metadata, policy, prompt, payload, schema, metrics):
        result = {name: 'FICTIONAL ' + payload['piece_id'] for name in ('title','question','argument','synthesis','limitations')}
        for n in range(1, 4):
            result[f'source_{n}_claim'] = {'statement': 'Synthetic only', 'type': 'source_claim', 'passage_id': f's{n}p1'}
        result['cross_source_inference'] = {'statement': 'Synthetic inference', 'passage_ids': ['s1p1','s2p1']}
        return result
    monkeypatch.setattr('editorial.local_briefs.ask', fake)
    # Podcast is assigned only to piece 01; it must not be forced onto 03.
    fourth = ('fictional-d', 'v1')
    ev.items[fourth] = dict(ev.items[keys[0]], publisher_id='fictional-d')
    ev.text[fourth] = ev.text[keys[0]]
    accepted = {'01': set(keys), '02': {keys[0], keys[1], fourth}, '03': {keys[0], keys[1], fourth}}
    briefs = brief_generate(None, {'as_of_date': '2026-10-15'}, {'topic':'code','central_question':'review'},
                           '', '', ev, accepted, {})
    assert briefs[0]['claims'][0]['evidence'][0]['item_id'] == keys[2][0]
    for brief in briefs:
        assert len(brief['claims']) == 4
        assert len({c['evidence'][0]['item_id'] for c in brief['claims'][:3]}) == 3
    def document_fake(*args):
        brief = args[5]['brief']
        return {'introduction':'Synthetic introduction', 'conclusion':'Synthetic conclusion',
                'sections': {c['claim_id']: 'Synthetic section' for c in brief['claims']}}
    monkeypatch.setattr('content.local_documents.ask', document_fake)
    docs = document_generate('write_articles', None, {'as_of_date':'2026-10-15'}, {}, '', '', briefs, ev, {})
    assert [d['claims'] for d in docs] == [b['claims'] for b in briefs]
    assert all(all(cid in doc['markdown'] for cid in doc['claim_ids']) for doc in docs)
