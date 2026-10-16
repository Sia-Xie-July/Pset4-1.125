#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$REPO_ROOT"
source "$REPO_ROOT/lib/common.sh"
common_init summarize_run "${1:-${RUN_DIR:-}}"
require_arg_count "$#" 1 1 'Usage: summarize_run.sh RUN_DIR'
python3 "$REPO_ROOT/reporting/summarize_run.py"
