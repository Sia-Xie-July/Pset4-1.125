"""Generate one document at a time; reuse validated claims, not full corpora."""
from copy import deepcopy
from lib.model_provider import ask
from lib.schemas import obj, STRING


def generate(stage, run, metadata, project, policy, prompt, briefs, evidence, metrics):
    documents = []
    video = stage == 'write_video_scripts'
    for brief in briefs:
        passages = []
        for claim in brief['claims']:
            groups = {}
            for ref in claim['evidence']:
                key = ref['item_id'], ref['version_id']
                item = evidence.items[key]
                locator = ref['locator']
                text = locator.get('quote')
                if text is None:
                    text = next(s['text'] for s in evidence.segments[key] if s['segment_id'] == locator['segment_id'])
                group = groups.setdefault(key, {'claim_id': claim['claim_id'], 'title': item['title'],
                                 'publisher_id': item['publisher_id'], 'kind': item['kind'], 'passages': []})
                if text not in group['passages']:
                    group['passages'].append(text)
            passages.extend(groups.values())
        compact_brief = {k: v for k, v in brief.items() if k != 'claims'}
        compact_brief['claims'] = [{k: v for k, v in claim.items() if k != 'evidence'} for claim in brief['claims']]
        sections = {claim['claim_id']: STRING for claim in brief['claims']}
        schema = obj({'introduction': STRING, 'sections': obj(sections), 'conclusion': STRING})
        result = ask(stage, run, metadata, policy, prompt,
            {'project': project, 'as_of_date': metadata['as_of_date'], 'brief': compact_brief,
             'cited_passages_only': passages,
             'instructions': ('Generate ONE audience-facing English video script, 450–600 spoken words total (3–5 minutes). Include visual directions in [Visual: ...] and label spoken text Narration. ' if video else
                              'Generate ONE English article, 650–800 words total, excluding sources. ')
                 + 'Use 80–100 words for introduction, 120–140 words for EACH of the four claim sections, and 80–100 words for conclusion. Each section must discuss its corresponding claim, not merely repeat it. Explain the cross-source reasoning and limitations. Do not invent facts, measurements, quotations or source names. Do not include sources/claim markers; the renderer attaches the original validated references. Return only the requested section object.'},
            schema, metrics)
        body = '# ' + brief['title'] + '\n\n' + result['introduction'] + '\n\n'
        body += '\n\n'.join(result['sections'][claim['claim_id']] + ' [' + claim['claim_id'] + ']'
                            for claim in brief['claims'])
        body += '\n\n' + result['conclusion'] + '\n'
        documents.append({'piece_id': brief['piece_id'], 'markdown': body,
                          'claim_ids': [c['claim_id'] for c in brief['claims']],
                          'claims': deepcopy(brief['claims'])})
    return documents
