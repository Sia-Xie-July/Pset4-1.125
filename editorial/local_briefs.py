"""Small per-piece synthesis requests using validated literal passage handles."""
from editorial.passages import packet
from itertools import permutations
from lib.model_provider import ask
from lib.schemas import obj, STRING, array
from lib.stage_runtime import OperationalFailure


def generate(run, metadata, project, policy, prompt, evidence, accepted, metrics):
    briefs = []
    purposes = {'01': 'What changed and why it matters',
                '02': 'Which claims withstand scrutiny and what remains uncertain',
                '03': 'Practical implications and what to watch next'}
    pieces = sorted(accepted)
    assignments = [dict(zip(pieces, kinds)) for kinds in permutations(['feed', 'youtube', 'podcast'])
                   if all(any(evidence.items[k]['kind'] == kind for k in accepted[piece])
                          for piece, kind in zip(pieces, kinds))]
    if not assignments:
        raise OperationalFailure('Cannot distribute accepted input kinds across the three local briefs')
    coverage = assignments[0]
    for piece, keys in sorted(accepted.items()):
        # A small, diverse candidate set, not a claim that all publishers corroborate.
        chosen, publishers = [], set()
        preferred = coverage[piece]
        ranked = sorted(keys, key=lambda k: (evidence.items[k]['kind'] != preferred,
                                             evidence.items[k]['publisher_id'], k))
        for key in ranked:
            publisher = evidence.items[key]['publisher_id']
            if publisher not in publishers:
                chosen.append(key)
                publishers.add(publisher)
            if len(chosen) == 3:
                break
        if len(chosen) < 3 or evidence.items[chosen[0]]['kind'] != preferred:
            raise OperationalFailure(f'Local brief {piece} needs three publishers and accepted {preferred} evidence')
        sources, refs = [], {}
        properties = {field: STRING for field in ('title', 'question', 'argument', 'synthesis', 'limitations')}
        for number, key in enumerate(chosen, 1):
            source = packet(evidence, key, project, maximum=3)
            handles = []
            for index, passage in enumerate(source['passages'], 1):
                handle = f's{number}p{index}'
                handles.append(handle)
                refs[handle] = passage.pop('references')
                passage.pop('reference')
                passage['passage_id'] = handle
            if not handles:
                raise OperationalFailure('No literal source passages available')
            sources.append(source)
            properties[f'source_{number}_claim'] = obj({'statement': STRING,
                'type': {'type': 'string', 'enum': ['reported_fact', 'source_claim', 'inference']},
                'passage_id': {'type': 'string', 'enum': handles}})
        properties['cross_source_inference'] = obj({'statement': STRING,
            'passage_ids': array({'type': 'string', 'enum': list(refs)}, 2, 3)})
        output = ask('create_briefs', run, metadata, policy, prompt,
            {'project': project, 'as_of_date': metadata['as_of_date'], 'piece_id': piece,
             'purpose': purposes[piece],
             'sources': sources,
             'instructions': 'Return ONE brief using this compact schema. Write argument as ONE concise sentence answering this piece purpose, not the overall project question. Write question specific to this piece purpose. Use ONLY the supplied sources; do not recall other sources or earlier responses. Each source claim must be supported by its own selected passage and attributed to its publisher. Do not assert increased quality, reduced review burden or faster delivery without measured evidence. Cross-source inference must connect different publishers and explain reasoning in synthesis. Do not invent conflict or outcomes. Acknowledge excerpt-only evidence and commercial/translation limits. Passage handles are expanded mechanically to the exact original references.'},
            obj(properties), metrics)
        brief = {field: output[field] for field in ('title', 'question', 'argument', 'synthesis', 'limitations')}
        brief.update(piece_id=piece, claims=[])
        for number in range(1, 4):
            claim = output[f'source_{number}_claim']
            brief['claims'].append({'claim_id': f'{piece}-c{number}', 'statement': claim['statement'],
                'type': claim['type'], 'evidence': refs[claim['passage_id']]})
        inference = output['cross_source_inference']
        inference_refs = [ref for handle in dict.fromkeys(inference['passage_ids']) for ref in refs[handle]]
        if len({evidence.items[(r['item_id'], r['version_id'])]['publisher_id'] for r in inference_refs}) < 2:
            raise OperationalFailure('Cross-source inference must connect at least two publishers')
        brief['claims'].append({'claim_id': f'{piece}-c4', 'statement': inference['statement'],
                                'type': 'inference', 'evidence': inference_refs})
        briefs.append(brief)
    return briefs
