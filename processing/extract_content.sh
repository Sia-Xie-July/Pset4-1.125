#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$REPO_ROOT"
source "$REPO_ROOT/lib/common.sh"
common_init extract_content "${1:-${RUN_DIR:-}}"
python3 "$REPO_ROOT/processing/extract_content.py" "$@"
