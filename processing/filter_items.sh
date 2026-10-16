#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$REPO_ROOT"
source "$REPO_ROOT/lib/common.sh"
common_init filter_items "${1:-${RUN_DIR:-}}"
require_arg_count "$#" 1 1 'Usage: filter_items.sh RUN_DIR'
python3 "$REPO_ROOT/processing/filter_items.py"
