"""FICTIONAL source identities: generated references obey per-piece assignments."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from editorial.create_briefs import include_coverage_claims, response_schema
from lib.schemas import validate


def test_generated_schema_enforces_exact_pairs_and_assignments():
    accepted = {'01': {('FICTIONAL-a', 'version-a')},
                '02': {('FICTIONAL-b', 'version-b')},
                '03': {('FICTIONAL-c', 'version-c')}}
    briefs = [{'piece_id': piece, 'title': 'FICTIONAL', 'question': 'FICTIONAL',
               'argument': 'FICTIONAL', 'synthesis': 'FICTIONAL', 'limitations': 'FICTIONAL',
               'claims': [{'claim_id': piece + '-c1', 'statement': 'FICTIONAL',
                           'type': 'source_claim', 'evidence': [
                               {'item_id': next(iter(keys))[0], 'version_id': next(iter(keys))[1],
                                'locator': {'type': 'text', 'quote': 'FICTIONAL'}}]}]}
              for piece, keys in accepted.items()]
    schema = response_schema(accepted)
    validate(schema, {'briefs': briefs})
    for wrong in ({'item_id': 'FICTIONAL-b', 'version_id': 'version-b'},
                  {'item_id': 'FICTIONAL-a', 'version_id': 'invented-version'},
                  {'item_id': 'FICTIONAL-a', 'version_id': 'version-b'}):
        changed = deepcopy(briefs)
        changed[0]['claims'][0]['evidence'][0].update(wrong)
        with pytest.raises(ValueError):
            validate(schema, {'briefs': changed})


def test_media_locator_schema_uses_only_actual_segment_ids():
    key = ('FICTIONAL-media', 'version-media')
    evidence = SimpleNamespace(items={key: {'kind': 'podcast', 'publisher_id':'FICTIONAL-pub'}},
                               segments={key: [{'segment_id': 's-000001'}, {'segment_id': 's-000003'}]})
    schema = response_schema({piece: {key} for piece in ('01', '02', '03')}, evidence)
    ref_schema = schema['properties']['briefs']['items']['anyOf'][0]['properties']['claims']['items']['properties']['evidence']['items']
    ref = {'item_id': key[0], 'version_id': key[1],
           'locator': {'type': 'segment', 'segment_id': 's-000003'}}
    validate(ref_schema, ref)
    ref['locator']['segment_id'] = 's-000002'
    with pytest.raises(ValueError):
        validate(ref_schema, ref)


def test_written_quote_schema_allows_full_source_not_only_quote_menu():
    text = 'FICTIONAL clients confirm current policy before starting their work. If confirmation fails, the client fails closed rather than using a stale policy.'
    key = ('FICTIONAL-feed', 'v1')
    evidence = SimpleNamespace(items={key:{'kind':'feed','publisher_id':'FICTIONAL-pub'}}, segments={key:[]}, text={key:text})
    schema = response_schema({piece:{key} for piece in ('01','02','03')}, evidence)
    ref_schema = schema['properties']['briefs']['items']['anyOf'][0]['properties']['claims']['items']['properties']['evidence']['items']
    ref = {'item_id':key[0],'version_id':key[1], 'locator':{'type':'text','quote':text[:40]}}
    validate(ref_schema, ref)
    ref['locator']['quote'] = text
    validate(ref_schema, ref)
    # Actual passage existence remains enforced by Evidence.reference, covered
    # by test_briefs_reject_invented_evidence_and_bad_shapes.


def test_generated_coverage_claims_are_included_without_silent_rewrites():
    claim = {'claim_id':'03-c99','statement':'FICTIONAL host observation',
             'type':'source_claim','evidence':[{'item_id':'FICTIONAL','version_id':'v1',
                 'locator':{'type':'segment','segment_id':'s-001'}}]}
    brief = {'claims':[], 'podcast_claim':deepcopy(claim)}
    include_coverage_claims([brief])
    assert brief == {'claims':[claim]}
    duplicate = {'claims':[deepcopy(claim)],'podcast_claim':deepcopy(claim)}
    include_coverage_claims([duplicate])
    assert duplicate['claims'] == [claim]
    conflicting = {'claims':[deepcopy(claim)],'podcast_claim':dict(claim,statement='FICTIONAL changed')}
    with pytest.raises(ValueError):
        include_coverage_claims([conflicting])


def test_coverage_claim_ids_follow_the_public_piece_contract():
    key = ('FICTIONAL-podcast', 'v1')
    evidence = SimpleNamespace(items={key: {'kind': 'podcast', 'publisher_id':'FICTIONAL-pub'}},
                               segments={key: [{'segment_id': 's-001'}]})
    schema = response_schema({'03': {key}}, evidence)
    brief = schema['properties']['briefs']['items']['anyOf'][0]
    for field, valid in ((brief['properties']['claims']['items'], '03-c1'),
                         (brief['properties']['podcast_claim'], '03-c93')):
        ids = field['properties']['claim_id']
        validate(ids, valid)
        for invalid in ('03-p1', '02-c1', '03-c0'):
            with pytest.raises(ValueError):
                validate(ids, invalid)
    with pytest.raises(ValueError):
        validate(brief['properties']['claims']['items']['properties']['claim_id'], '03-c93')
