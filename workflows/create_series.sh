#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$REPO_ROOT"
source "$REPO_ROOT/lib/common.sh"
common_init create_series "${1:-${RUN_DIR:-}}"
require_arg_count "$#" 1 2 'Usage: create_series.sh RUN_DIR [--from-briefs]'
resume=0
if [[ ${2:-} == --from-briefs ]]; then
    resume=1
    [[ -s "$RUN_DIR/decisions.jsonl" ]] || fail 2 'Resuming requires saved decisions'
elif [[ -n ${2:-} ]]; then
    fail 2 'Unknown series option'
fi
[[ -f "$RUN_DIR/eligible.jsonl" ]] || fail 2 'The run eligible.jsonl artifact is required'

# A resumed attempt preserves prior outputs, review and human decisions.
archive="$RUN_DIR/attempts/$INVOCATION_ID"
for artifact in decisions.jsonl briefs.jsonl articles.jsonl video_scripts.jsonl articles video_scripts review.json approval.json series_status.json series_stages.jsonl; do
    if (( resume == 1 )) && [[ "$artifact" == decisions.jsonl ]]; then continue; fi
    if [[ -e "$RUN_DIR/$artifact" ]]; then
        mkdir -p "$archive"
        mv "$RUN_DIR/$artifact" "$archive/$artifact"
    fi
done
: > "$RUN_DIR/series_stages.jsonl"

run_component() {
    local script=$1 input=$2 output=$3 code=0
    bash "$script" "$RUN_DIR" < "$RUN_DIR/$input" > "$RUN_DIR/$output" || code=$?
    jq -nc --arg stage "${script%.sh}" --argjson code "$code" --arg path "$RUN_DIR/$output" \
        '{stage:$stage,exit_code:$code,output_path:$path}' >> "$RUN_DIR/series_stages.jsonl"
    if (( code != 0 )); then
        jq -n --argjson code "$code" --arg stage "$script" \
            '{status:"failed",exit_code:$code,failed_stage:$stage,human_review_required:true}' > "$RUN_DIR/series_status.json"
        cat "$RUN_DIR/series_status.json"
        fail "$code" "$script failed; later stages were not run"
    fi
}

if (( resume == 0 )); then
    run_component editorial/select_items.sh eligible.jsonl decisions.jsonl
fi
run_component editorial/create_briefs.sh decisions.jsonl briefs.jsonl
run_component content/write_articles.sh briefs.jsonl articles.jsonl
run_component content/write_video_scripts.sh briefs.jsonl video_scripts.jsonl
code=0
bash review/check_content.sh "$RUN_DIR" > "$RUN_DIR/review.json" || code=$?
jq -nc --argjson code "$code" '{stage:"review/check_content",exit_code:$code,output_path:"review.json"}' >> "$RUN_DIR/series_stages.jsonl"
if (( code != 0 )); then
    jq -n --argjson code "$code" '{status:"failed",exit_code:$code,failed_stage:"review/check_content",human_review_required:true}' > "$RUN_DIR/series_status.json"
    cat "$RUN_DIR/series_status.json"
    fail "$code" 'Content assessment could not run'
fi
if ! jq -e '.passed == true' "$RUN_DIR/review.json" >/dev/null; then
    jq -n '{status:"failed",exit_code:1,failed_stage:"review/check_content",human_review_required:true}' > "$RUN_DIR/series_status.json"
    cat "$RUN_DIR/series_status.json"
    fail 1 'Content checks found blocking errors; human repair is required'
fi
jq -n '{status:"awaiting_review",exit_code:0,human_review_required:true}' > "$RUN_DIR/series_status.json"
cat "$RUN_DIR/series_status.json"
