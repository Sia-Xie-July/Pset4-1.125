"""Content-only validation of model document claims, markers and direct quotes."""
import re
from lib.stage_runtime import InvalidInput


def claim_contract(claim):
    references=[]
    for ref in claim['evidence']:
        locator=ref['locator']
        field='quote' if locator['type']=='text' else 'segment_id'
        references.append({'item_id':ref['item_id'],'version_id':ref['version_id'],
                           'locator':{'type':locator['type'],field:locator[field]}})
    return {'claim_id':claim['claim_id'],'statement':claim['statement'],'type':claim['type'],'evidence':references}


def validate_documents(documents, briefs, evidence, accepted):
    warnings = []
    if len(documents) != 3 or {doc['piece_id'] for doc in documents} != {'01','02','03'}:
        raise InvalidInput('Exactly three unique generated piece IDs are required')
    index = {brief['piece_id']:brief for brief in briefs}
    for document in documents:
        brief = index[document['piece_id']]
        expected = {claim['claim_id']:claim for claim in brief['claims']}
        claims = {claim['claim_id']:claim for claim in document['claims']}
        if len(claims) != len(document['claims']) or {key:claim_contract(value) for key,value in claims.items()} != {key:claim_contract(value) for key,value in expected.items()}:
            raise InvalidInput('Generated claims must preserve the validated brief claims and exact references')
        ids = document['claim_ids']
        if len(ids) != len(set(ids)) or set(ids) != set(expected):
            raise InvalidInput('Generated manifest claims do not match the brief')
        markers = set(re.findall(r'\b(?:01|02|03)-c[1-9]\d*\b', document['markdown']))
        if markers != set(ids):
            raise InvalidInput('Draft claim markers are missing or refer to unsupported claims')
        supporting_passages = []
        for claim in document['claims']:
            for ref in claim['evidence']:
                evidence.reference(ref, accepted[document['piece_id']])
                if ref['locator']['type'] == 'text':
                    supporting_passages.append(ref['locator']['quote'])
                else:
                    key = ref['item_id'],ref['version_id']
                    supporting_passages.extend(seg['text'] for seg in evidence.segments[key] if seg['segment_id']==ref['locator']['segment_id'])
        # Quotation marks also delimit labels and suggested questions. A lexical
        # mismatch is a human-review warning, not proof of a fabricated quote.
        # Structured evidence locators above still must match actual sources.
        quotations = re.findall(r'"([^"\n]+)"|“([^”\n]+)”', document['markdown'])
        quotes = [straight or curly for straight,curly in quotations]
        quotes += [line[2:].strip() for line in document['markdown'].splitlines() if line.startswith('> ')]
        if any(not quote.strip() or not any(quote in passage for passage in supporting_passages) for quote in quotes):
            warnings.append({'piece_id': document['piece_id'],
                             'explanation': 'Quotation-marked text could not be matched to cited passages; human review must check attribution and wording before publication'})
    return warnings
