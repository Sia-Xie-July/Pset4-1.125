"""FICTIONAL identities constrain selection without deciding acceptance."""
from copy import deepcopy

import pytest

from editorial.select_items import response_schema
from lib.schemas import validate


def test_selection_schema_constrains_identity_and_record_count():
    schema = response_schema([{'item_id':'FICTIONAL-item','version_id':'FICTIONAL-version'}])
    good = {'decisions':[{'item_id':'FICTIONAL-item','version_id':'FICTIONAL-version',
                          'decision':'reject','reason':'FICTIONAL reason','piece_ids':[]}]}
    validate(schema, good)
    for bad in ({'decisions':[]}, {'decisions':good['decisions']*2}):
        with pytest.raises(ValueError):
            validate(schema, bad)
    for field in ('item_id','version_id'):
        bad = deepcopy(good)
        bad['decisions'][0][field] = 'FICTIONAL-invented'
        with pytest.raises(ValueError):
            validate(schema, bad)
