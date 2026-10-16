# FICTIONAL EDITORIAL FIXTURES

The text, segments, publishers, sources, claims and model usage in these tests are
invented. `tests/editorial_fixture.py` builds an isolated example run with twelve
fixture items from six declared fictional publishers and canned model responses.
Responses are explicitly marked `fixture: true`; their token counts are synthetic.
The provider reads those files without performing any API calls or inventing new
references. The pure versioning utility computes IDs for these labeled assets.
Only the isolated copy of store.sh opens the evidence index.
