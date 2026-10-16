#!/usr/bin/env bash
set -euo pipefail

# Coordinate components; substantive logic remains in their owning directories.
REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$REPO_ROOT"
source "$REPO_ROOT/lib/common.sh"
PACKAGE_MODE=0
RESUME_MODE=0
if [[ ${1:-} == --package ]]; then
    PACKAGE_MODE=1
    RUN_DIR=${2:-}
    common_init run.package "$RUN_DIR"
elif [[ ${1:-} == --resume-series ]]; then
    RESUME_MODE=1
    RUN_DIR=${2:-}
    common_init run.resume "$RUN_DIR"
else
    RUN_DIR=$(python3 run_setup.py allocate)
    common_init run "$RUN_DIR"
fi

finish_run() {
    local code=$1 report_code=0
    trap - EXIT
    # Summarize even invalid configuration, interrupted collection, or init failure.
    RUN_EXIT_CODE="$code" bash reporting/summarize_run.sh "$RUN_DIR" > "$RUN_DIR/.summary-$INVOCATION_ID.tmp" || report_code=$?
    if (( report_code == 0 )); then
        mv "$RUN_DIR/.summary-$INVOCATION_ID.tmp" "$RUN_DIR/summary.json"
        cat "$RUN_DIR/summary.json"
    else
        log 'Could not complete the run summary'
        if (( code == 0 )); then code=1; fi
    fi
    common_finish "$code"
}
trap 'finish_run "$?"' EXIT
log "Run directory: $RUN_DIR"

if (( RESUME_MODE == 1 )); then
    require_arg_count "$#" 2 2 'Usage: run.sh --resume-series RUN_DIR'
    # Reuse the immutable run date, snapshots and saved model decisions.
    bash workflows/create_series.sh "$RUN_DIR" --from-briefs > /dev/null
    exit 0
fi

if (( PACKAGE_MODE == 1 )); then
    require_arg_count "$#" 2 2 'Usage: run.sh --package RUN_DIR'
    code=0
    bash review/check_content.sh "$RUN_DIR" > "$RUN_DIR/.review-$INVOCATION_ID.tmp" || code=$?
    if (( code != 0 )); then fail "$code" 'Content assessment could not run'; fi
    mv "$RUN_DIR/.review-$INVOCATION_ID.tmp" "$RUN_DIR/review.json"
    bash publishing/prepare_package.sh "$RUN_DIR" > /dev/null || code=$?
    if (( code != 0 )); then fail "$code" 'Production package requires current passing checks and matching human approval'; fi
    exit 0
fi

code=0
python3 run_setup.py configure "$RUN_DIR" "$@" >&2 || code=$?
if (( code != 0 )); then fail "$code" 'Configuration validation/snapshot failed'; fi
if [[ ! -f "$RUN_DIR/config/project.json" ]]; then exit 0; fi # --help: no stages run

code=0
bash data/store.sh init || code=$?
if (( code != 0 )); then fail "$code" 'Evidence store initialization failed'; fi

code=0
bash workflows/collect_sources.sh "$RUN_DIR" > /dev/null || code=$?
if (( code != 0 )); then
    COMMON_ERROR='Collection coverage is incomplete; inspect component receipts'
fi
if (( code != 2 )) && [[ $(jq -r '.scope' "$RUN_DIR/run.json") != collection_only ]]; then
    series_code=0
    bash workflows/create_series.sh "$RUN_DIR" > /dev/null || series_code=$?
    if (( series_code == 2 || code == 0 )); then code=$series_code; fi
    if (( series_code != 0 )); then COMMON_ERROR='Series workflow needs repair; inspect receipts'; fi
fi
exit "$code"
