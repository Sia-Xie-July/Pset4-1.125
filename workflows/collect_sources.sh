#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$REPO_ROOT"
source "$REPO_ROOT/lib/common.sh"
common_init collect_sources "${1:-${RUN_DIR:-}}"
require_arg_count "$#" 1 1 'Usage: collect_sources.sh RUN_DIR'
[[ -f "$RUN_DIR/run.json" && -f "$RUN_DIR/config/sources.json" ]] || fail 2 'Run metadata and source snapshot are required'

# Retain earlier outputs when resuming this workflow in the same run. Receipts
# remain in logs/ with their original unique names.
archive="$RUN_DIR/attempts/$INVOCATION_ID"
for artifact in candidates candidates.jsonl items.jsonl changes.jsonl corpus.jsonl eligible.jsonl exclusions.jsonl collection_stages.jsonl collection_status.json; do
    if [[ -e "$RUN_DIR/$artifact" ]]; then
        mkdir -p "$archive"
        mv "$RUN_DIR/$artifact" "$archive/$artifact"
    fi
done
mkdir -p "$RUN_DIR/candidates"
: > "$RUN_DIR/collection_stages.jsonl"
overall=0

record_stage() {
    local stage=$1 code=$2 output=$3
    jq -nc --arg stage "$stage" --argjson code "$code" --arg path "$output" \
        '{stage:$stage,exit_code:$code,output_path:$path}' >> "$RUN_DIR/collection_stages.jsonl"
    if (( code == 2 )); then overall=2
    elif (( code != 0 && overall == 0 )); then overall=1
    fi
    if (( code != 0 )); then log "$stage exited $code; coverage remains incomplete"; fi
}

# Sequential collection makes source order and canonical representative choice
# reproducible. Separate files/statuses still preserve every collector outcome.
for kind in feeds youtube podcasts; do
    code=0
    bash "collectors/fetch_${kind}.sh" "$RUN_DIR" > "$RUN_DIR/candidates/$kind.jsonl" || code=$?
    record_stage "fetch_$kind" "$code" "$RUN_DIR/candidates/$kind.jsonl"
done

# Mechanical stream validation retains valid partial results. Both pipe ends
# have their statuses captured immediately (portable Bash 3.2 arrays).
set +e
cat "$RUN_DIR/candidates/feeds.jsonl" "$RUN_DIR/candidates/youtube.jsonl" "$RUN_DIR/candidates/podcasts.jsonl" |
    python3 lib/candidate_stream.py > "$RUN_DIR/candidates.jsonl"
merge_codes=("${PIPESTATUS[@]}")
set -e
record_stage merge_reader "${merge_codes[0]}" "$RUN_DIR/candidates.jsonl"
record_stage merge_validate "${merge_codes[1]}" "$RUN_DIR/candidates.jsonl"

code=0
bash processing/extract_content.sh "$RUN_DIR" < "$RUN_DIR/candidates.jsonl" > "$RUN_DIR/items.jsonl" || code=$?
record_stage extract_content "$code" "$RUN_DIR/items.jsonl"
if (( code == 0 || code == 1 )); then
    code=0
    bash data/store.sh upsert "$RUN_DIR" < "$RUN_DIR/items.jsonl" > "$RUN_DIR/changes.jsonl" || code=$?
    record_stage store.upsert "$code" "$RUN_DIR/changes.jsonl"
else
    jq -nc '{stage:"store.upsert",exit_code:null,output_path:null,reason:"Invalid extraction input/output"}' >> "$RUN_DIR/collection_stages.jsonl"
fi

# Actual Item stream pipe: retain corpus while feeding the freshness component.
set +e
bash data/store.sh list | tee "$RUN_DIR/corpus.jsonl" |
    bash processing/filter_items.sh "$RUN_DIR" > "$RUN_DIR/eligible.jsonl"
filter_codes=("${PIPESTATUS[@]}")
set -e
record_stage store.list "${filter_codes[0]}" "$RUN_DIR/corpus.jsonl"
record_stage corpus_writer "${filter_codes[1]}" "$RUN_DIR/corpus.jsonl"
record_stage filter_items "${filter_codes[2]}" "$RUN_DIR/eligible.jsonl"

jq -n --slurpfile stages "$RUN_DIR/collection_stages.jsonl" --arg id "$INVOCATION_ID" --argjson code "$overall" '
  {invocation_id:$id,exit_code:$code,status:(if $code==0 then "completed" else "incomplete" end),
   coverage_incomplete:($code!=0),stages:$stages,
   collector_exit_codes:($stages | map(select(.stage|startswith("fetch_"))) | map({key:.stage,value:.exit_code}) | from_entries)}
' > "$RUN_DIR/collection_status.json"
jq -n --argjson code "$overall" '{input_count:null,output_count:null,
    errors:(if $code==0 then [] else ["Collection incomplete; inspect collection_status.json and component receipts"] end)}' > "$RECEIPT_METRICS"
cat "$RUN_DIR/collection_status.json"
exit "$overall"
