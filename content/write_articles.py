"""Own article generation, document validation, article files and manifests."""
import sys
import os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from content.files import publish
from content.validation import validate_documents
from lib.evidence import accepted_by_piece, eligible
from lib.model_provider import ask
from lib.records import canonical
from lib.schemas import MANIFEST, RESPONSES, validate
from lib.stage_runtime import records,run_directory,run_stage,snapshots


def main(metrics):
    run=run_directory()
    metadata,project,policy,prompt=snapshots(run,'write_articles')
    briefs=records(sys.stdin)
    metrics['input_count']=len(briefs)
    evidence=eligible(run,metadata)
    with (run/'decisions.jsonl').open(encoding='utf-8') as stream:
        accepted=accepted_by_piece(evidence,records(stream))
    evidence.briefs(briefs,accepted)
    keys={(ref['item_id'],ref['version_id']) for brief in briefs for claim in brief['claims'] for ref in claim['evidence']}
    if os.getenv('MODEL_PROVIDER', 'ollama_local') == 'ollama_local':
        from content.local_documents import generate
        documents = generate('write_articles',run,metadata,project,policy,prompt,briefs,evidence,metrics)
    else:
        output=ask('write_articles',run,metadata,policy,prompt,
        {'project':project,'as_of_date':metadata['as_of_date'],'briefs':briefs,'evidence':evidence.payload(keys),
         'requirements':['Three distinct 600–900-word audience articles excluding source notes',
                         'Copy the brief claims/references exactly into claims; preserve their markers in Markdown',
                         'Only quote exact cited passages; distinguish facts, source claims, interpretation and uncertainty']},
        RESPONSES['write_articles'],metrics)
        documents=output['documents']
    metrics['warnings'] = validate_documents(documents,briefs,evidence,accepted)
    manifests=publish(run,'articles',documents,briefs,evidence,metadata)
    for manifest in manifests:
        validate(MANIFEST,manifest)
        print(canonical(manifest))
        metrics['output_count']+=1


if __name__=='__main__':
    sys.exit(run_stage(main))
