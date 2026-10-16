#!/usr/bin/env bash
set -euo pipefail

# Source this file; call common_init before validating component arguments.
readonly EXIT_OK=0 EXIT_OPERATIONAL=1 EXIT_INVALID=2

log() { printf '%s\n' "$*" >&2; }
fail() { COMMON_ERROR=$2; log "$2"; exit "$1"; }
require_arg_count() {
    local count=$1 minimum=$2 maximum=$3
    if (( count < minimum || count > maximum )); then
        fail "$EXIT_INVALID" "$4"
    fi
}

common_init() {
    COMMON_STAGE=$1
    RUN_DIR=${2:-}
    [[ -n "$RUN_DIR" ]] || fail 2 'RUN_DIR must name an existing run directory'
    command -v jq >/dev/null || fail 1 'jq is required for receipts'
    command -v python3 >/dev/null || fail 1 'python3 is required'
    # Validate the receipt home before writing anything. In particular a caller
    # cannot route another component's logs into the canonical evidence index.
    if ! python3 - "$RUN_DIR" <<'PY'
import sys
from pathlib import Path
root = Path.cwd().resolve()
directory = Path(sys.argv[1]).resolve()
if not directory.is_relative_to(root) or directory.is_relative_to(root/'data/evidence') or not directory.is_dir():
    sys.exit(2)
PY
    then fail 2 'RUN_DIR must be an existing repository directory outside the evidence index'; fi
    mkdir -p "$RUN_DIR/logs" || fail 1 'Cannot create receipt directory'
    COMMON_STARTED=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
    COMMON_PARENT=${INVOCATION_ID:-}
    INVOCATION_ID=$(python3 -c 'import uuid; print(uuid.uuid4())')
    COMMON_ERROR=''
    RECEIPT_METRICS="$RUN_DIR/logs/.${INVOCATION_ID}.metrics"
    printf '%s\n' '{"input_count":null,"output_count":null,"errors":[]}' > "$RECEIPT_METRICS"
    export RUN_DIR INVOCATION_ID RECEIPT_METRICS
    trap 'common_finish "$?"' EXIT
    trap 'COMMON_ERROR="Interrupted"; exit 1' INT TERM HUP
    common_receipt running null
}

common_receipt() {
    local status=$1 code=$2 finished=null target temporary
    target="$RUN_DIR/logs/${COMMON_STAGE//\//_}-${INVOCATION_ID}-${status}.json"
    temporary="${target}.tmp"
    if [[ "$status" != running ]]; then
        finished=$(jq -Rn --arg value "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" '$value')
    fi
    jq -n --slurpfile metrics "$RECEIPT_METRICS" \
        --arg stage "$COMMON_STAGE" --arg id "$INVOCATION_ID" --arg parent "$COMMON_PARENT" \
        --arg start "$COMMON_STARTED" --arg status "$status" --arg error "$COMMON_ERROR" \
        --argjson finish "$finished" --argjson code "$code" \
        --arg bash_version "$BASH_VERSION" --arg python_version "$(python3 --version 2>&1)" \
        --arg jq_version "$(jq --version)" '
        $metrics[0] + {
          invocation_id:$id, parent_invocation_id:(if $parent=="" then null else $parent end),
          stage:$stage, status:$status, exit_code:$code, started_at:$start, finished_at:$finish,
          tools:([$bash_version,$python_version,$jq_version] + ($metrics[0].tools // [])),
          models:($metrics[0].models // []),
          cost_usd:($metrics[0].cost_usd // null), cost_is_estimate:($metrics[0].cost_is_estimate // false),
          errors: (($metrics[0].errors // []) + (if $error=="" then [] else [$error] end))
        }' > "$temporary" && mv "$temporary" "$target"
}

common_finish() {
    local code=$1 status=completed
    trap - EXIT
    # Unexpected runtime failures also obey the public 0/1/2 contract.
    if (( code != 0 && code != 2 )); then code=1; fi
    if (( code != 0 )); then
        status=failed
        if [[ -z "$COMMON_ERROR" ]] && ! jq -e '.errors | length > 0' "$RECEIPT_METRICS" >/dev/null; then
            COMMON_ERROR='Component did not complete'
        fi
    fi
    if ! common_receipt "$status" "$code"; then
        log 'Could not write final receipt'
        if (( code == 0 )); then code=1; fi
    fi
    rm -f "$RECEIPT_METRICS"
    exit "$code"
}
