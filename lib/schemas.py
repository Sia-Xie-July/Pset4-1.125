"""Focused JSON schemas and validation for editorial record boundaries."""
from copy import deepcopy
from jsonschema import Draft202012Validator

STRING = {"type": "string", "minLength": 1}
PIECE = {"type": "string", "enum": ["01", "02", "03"]}


def obj(properties):
    return {"type": "object", "properties": properties, "required": list(properties)}


def array(items, minimum=0, maximum=None):
    schema = {"type": "array", "items": items, "minItems": minimum}
    if maximum is not None:
        schema["maxItems"] = maximum
    return schema


REFERENCE = obj({"item_id": STRING, "version_id": STRING, "locator": {"anyOf": [
    obj({"type": {"const": "text", "type": "string"}, "quote": STRING}),
    obj({"type": {"const": "segment", "type": "string"}, "segment_id": STRING})]}})
CLAIM = obj({"claim_id": STRING, "statement": STRING,
             "type": {"type": "string", "enum": ["reported_fact", "source_claim", "inference"]},
             "evidence": array(REFERENCE, 1)})
DECISION = obj({"item_id": STRING, "version_id": STRING,
                "decision": {"type": "string", "enum": ["accept", "reject", "defer"]},
                "reason": STRING, "piece_ids": array(PIECE)})
BRIEF = obj({"piece_id": PIECE, "title": STRING, "question": STRING, "argument": STRING,
             "synthesis": STRING, "limitations": STRING, "claims": array(CLAIM, 1)})
MANIFEST = obj({"piece_id": PIECE, "path": STRING, "claim_ids": array(STRING, 1)})
# Model document envelope: Markdown plus a copy of the brief's supported claims.
# This is an internal transport shape; stdout still uses Content manifests.
DOCUMENT = obj({"piece_id": PIECE, "markdown": STRING, "claim_ids": array(STRING, 1), "claims": array(CLAIM, 1)})
RESPONSES = {"select_items": obj({"decisions": array(DECISION)}),
             "create_briefs": obj({"briefs": array(BRIEF, 3, 3)}),
             "write_articles": obj({"documents": array(DOCUMENT, 3, 3)}),
             "write_video_scripts": obj({"documents": array(DOCUMENT, 3, 3)})}


def validate(schema, value):
    if next(Draft202012Validator(schema).iter_errors(value), None) is not None:
        raise ValueError("Record does not match its required JSON schema")


def provider_schema(schema):
    # Strict providers require closed objects. The local contract still permits
    # additional fields, as ARCHITECTURE.md allows.
    result = deepcopy(schema)
    def close(value):
        if isinstance(value, dict):
            if value.get("type") == "object":
                value["additionalProperties"] = False
            for child in value.values():
                close(child)
        elif isinstance(value, list):
            for child in value:
                close(child)
    close(result)
    return result
