"""Own the eligible-item selection request and one-decision-per-item checks."""
import sys
import os
from copy import deepcopy
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.evidence import Evidence
from lib.model_provider import ask
from lib.records import canonical
from lib.schemas import DECISION, RESPONSES
from editorial.passages import packet
from lib.stage_runtime import OperationalFailure, records, run_directory, run_stage, snapshots


def response_schema(items):
    schema = deepcopy(RESPONSES["select_items"])
    choices = []
    for item in items:
        decision = deepcopy(DECISION)
        for field in ("item_id", "version_id"):
            decision["properties"][field] = {"type": "string", "enum": [item[field]]}
        choices.append(decision)
    schema["properties"]["decisions"].update(items={"anyOf": choices}, minItems=len(items), maxItems=len(items))
    return schema


def main(metrics):
    run = run_directory()
    metadata, project, policy, prompt = snapshots(run, "select_items")
    items = records(sys.stdin)
    metrics["input_count"] = len(items)
    if not items:
        raise OperationalFailure("No eligible evidence is available for editorial selection")
    evidence = Evidence(items, metadata)
    if os.getenv('MODEL_PROVIDER', 'ollama_local') == 'ollama_local':
        decisions = []
        schema = deepcopy(DECISION)
        for field in ('item_id', 'version_id'):
            del schema['properties'][field]
            schema['required'].remove(field)
        for index, item in enumerate(items, 1):
            print(f'Selecting item {index}/{len(items)} with local model', file=sys.stderr)
            key = item['item_id'], item['version_id']
            candidate = packet(evidence, key, project)
            # Selection needs passage text, not repeated long reference objects.
            for passage in candidate['passages']:
                passage.pop('references', None)
            decision = ask('select_items', run, metadata, policy, prompt,
                {'project': project, 'as_of_date': metadata['as_of_date'],
                 'candidate': candidate,
                 'batch_instruction': 'Decide only this candidate. Return the single decision object, not an array. Assign all pieces for which these passages are useful; use [] for reject/defer. State excerpt limitations in the reason.'},
                schema, metrics)
            decision.update(item_id=key[0], version_id=key[1])
            decisions.append(decision)
    else:
        output = ask("select_items", run, metadata, policy, prompt,
                 {"project": project, "as_of_date": metadata["as_of_date"], "eligible_evidence": evidence.payload()},
                 response_schema(items), metrics)
        decisions = output["decisions"]
    evidence.decisions(decisions)
    # Preserve input ordering even if the model returns decisions out of order.
    indexed = {(d["item_id"], d["version_id"]): d for d in decisions}
    for item in items:
        print(canonical(indexed[item["item_id"], item["version_id"]]))
        metrics["output_count"] += 1


if __name__ == "__main__":
    sys.exit(run_stage(main))
