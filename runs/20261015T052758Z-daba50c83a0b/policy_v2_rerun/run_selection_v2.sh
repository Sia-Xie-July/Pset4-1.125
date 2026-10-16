#!/usr/bin/env bash
set -euo pipefail
# Policy-revision rerun of ONE stage (editorial/select_items.sh) on the same
# 28 eligible items, same as_of_date, same prompts, same model; only the policy
# snapshot differs (v2). This is a labelled same-date stage replay, not a new run.
# Needs Ollama running locally:  OLLAMA_NO_CLOUD=1 ollama serve
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$HERE/../../.." && pwd)
cd "$REPO_ROOT"
D=${HERE#"$REPO_ROOT/"}
export PATH="$REPO_ROOT/.venv/bin:$PATH"
unset MODEL_API_KEY OPENAI_API_KEY MODEL_BASE_URL SELECT_ITEMS_MODEL
export MODEL_PROVIDER=ollama_local
export MODEL_NAME="${LOCAL_MODEL_NAME:-qwen3:8b}"
export MODEL_RESPONSE_FORMAT=json_schema
export MODEL_TOKEN_LIMIT_FIELD=max_completion_tokens
export MODEL_MAX_OUTPUT_TOKENS=8192
export MODEL_TIMEOUT_SECONDS=1800
bash editorial/select_items.sh "$D" < "$D/eligible.jsonl" > "$D/decisions_v2.jsonl.tmp"
mv "$D/decisions_v2.jsonl.tmp" "$D/decisions_v2.jsonl"
python3 "$D/compare_decisions.py" "$D" | tee "$D/comparison.md"
