#!/usr/bin/env bash
set -euo pipefail

# Local environment setup only; run.sh owns orchestration and run receipts.
# Deliberately do not load legacy .env cloud credentials/settings.
REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$REPO_ROOT"

if [[ ! -x "$REPO_ROOT/.venv/bin/python3" ]]; then
    printf '%s\n' 'Missing .venv; follow SETUP.md before running.' >&2
    exit 2
fi

export PATH="$REPO_ROOT/.venv/bin:$PATH"
unset MODEL_API_KEY OPENAI_API_KEY MODEL_BASE_URL
unset SELECT_ITEMS_MODEL CREATE_BRIEFS_MODEL WRITE_ARTICLES_MODEL WRITE_VIDEO_SCRIPTS_MODEL
export MODEL_PROVIDER=ollama_local
export MODEL_NAME="${LOCAL_MODEL_NAME:-qwen3:8b}"
export MODEL_RESPONSE_FORMAT="${MODEL_RESPONSE_FORMAT:-json_schema}"
export MODEL_TOKEN_LIMIT_FIELD="${MODEL_TOKEN_LIMIT_FIELD:-max_completion_tokens}"
export MODEL_MAX_OUTPUT_TOKENS="${LOCAL_MODEL_MAX_OUTPUT_TOKENS:-8192}"
export MODEL_TIMEOUT_SECONDS="${LOCAL_MODEL_TIMEOUT_SECONDS:-1800}"
export WHISPER_MODEL="${WHISPER_MODEL:-base}"
export WHISPER_DEVICE="${WHISPER_DEVICE:-cpu}"
export WHISPER_COMPUTE_TYPE="${WHISPER_COMPUTE_TYPE:-int8}"
export MAX_DURATION_MINUTES="${MAX_DURATION_MINUTES:-70}"

exec bash "$REPO_ROOT/run.sh" "$@"
