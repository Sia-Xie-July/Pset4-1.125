"""Bounded literal evidence retrieval; never generated summaries or new facts."""
import re


def passages(evidence, key, query, maximum=4):
    terms = set(re.findall(r'[a-z]{4,}', query.lower()))
    source = evidence.items[key]
    if source['kind'] == 'feed':
        # Preserve literal contiguous spans, including when splitting long paragraphs.
        text = evidence.text[key] or ''
        candidates = []
        for match in re.finditer(r'[^\n]+', text):
            paragraph = match.group().strip()
            for offset in range(0, len(paragraph), 600):
                quote = paragraph[offset:offset + 600].strip()
                if len(quote) >= 80:
                    candidates.append((quote, {'type': 'text', 'quote': quote}))
    else:
        # Captions are often incomplete phrases. Retrieve contiguous groups and
        # retain every segment reference so the complete passage is traceable.
        candidates = []
        segments = evidence.segments[key]
        for offset in range(0, len(segments), 8):
            group = segments[offset:offset + 8]
            text = ' '.join(s['text'] for s in group)
            if text.strip():
                candidates.append((text, [{'type': 'segment', 'segment_id': s['segment_id']} for s in group]))
    ranked = sorted(enumerate(candidates), key=lambda pair: (
        -len(terms & set(re.findall(r'[a-z]{4,}', pair[1][0].lower()))), pair[0]))
    selected = sorted(ranked[:maximum])
    result = []
    for _, (text, locator) in selected:
        locators = locator if isinstance(locator, list) else [locator]
        refs = [{'item_id': key[0], 'version_id': key[1], 'locator': loc} for loc in locators]
        result.append({'text': text, 'reference': refs[0], 'references': refs})
    return result


def packet(evidence, key, project, maximum=4):
    item = evidence.items[key]
    query = project['topic'] + ' ' + project['central_question']
    return {'title': item['title'], 'publisher_id': item['publisher_id'], 'kind': item['kind'],
            'published_at': item['published_at'], 'url': item['url'],
            'scope': 'Keyword-ranked literal excerpts, NOT the complete source. Do not infer missing context. Defer if insufficient.',
            'passages': passages(evidence, key, query, maximum)}
