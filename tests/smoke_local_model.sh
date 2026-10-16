#!/usr/bin/env bash
set -euo pipefail
source lib/common.sh
common_init local_smoke "${1:-}"
require_arg_count "$#" 1 1 'Usage: bash tests/smoke_local_model.sh RUN_DIR'
export MODEL_PROVIDER=ollama_local
export MODEL_NAME=qwen3:8b
export MODEL_MAX_OUTPUT_TOKENS=128
export MODEL_TIMEOUT_SECONDS=180
PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}" python3 tests/smoke_local_model.py
