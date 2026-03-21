#!/usr/bin/env sh
set -eu

python -m app.bootstrap
export APP_BOOTSTRAPPED=1

# Pull Ollama model in background if OLLAMA_BASE_URL is set
if [ -n "${OLLAMA_BASE_URL:-}" ]; then
  OLLAMA_MODEL="${OLLAMA_MODEL:-qwen2.5:7b}"
  echo "Pulling Ollama model in background: ${OLLAMA_MODEL} ..."
  (curl -sf "${OLLAMA_BASE_URL}/api/pull" \
    -d "{\"name\":\"${OLLAMA_MODEL}\",\"stream\":false}" \
    -H "Content-Type: application/json" \
    --max-time 600 \
    && echo "Ollama model pull complete: ${OLLAMA_MODEL}" \
    || echo "Warning: Ollama model pull failed (AI summary unavailable)") &
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
