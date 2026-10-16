#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$REPO_ROOT"
source "$REPO_ROOT/lib/common.sh"
common_init write_video_scripts "${1:-${RUN_DIR:-}}"
require_arg_count "$#" 1 1 'Usage: write_video_scripts.sh RUN_DIR'
python3 "$REPO_ROOT/content/write_video_scripts.py"
