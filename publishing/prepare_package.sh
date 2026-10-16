#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$REPO_ROOT"
source "$REPO_ROOT/lib/common.sh"
common_init prepare_package "${1:-${RUN_DIR:-}}"
require_arg_count "$#" 1 1 'Usage: prepare_package.sh RUN_DIR'
python3 "$REPO_ROOT/publishing/prepare_package.py"
