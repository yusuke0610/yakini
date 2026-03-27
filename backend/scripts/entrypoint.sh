#!/usr/bin/env sh
set -eu

python -m app.db.bootstrap
export APP_BOOTSTRAPPED=1

# Pull Ollama model in background if OLLAMA_BASE_URL is set
if [ -n "${OLLAMA_BASE_URL:-}" ]; then
  OLLAMA_MODEL="${OLLAMA_MODEL:-qwen2.5:3b}"
  OLLAMA_TIMEOUT="${OLLAMA_TIMEOUT:-600}"
  echo "Pulling Ollama model in background: ${OLLAMA_MODEL} ..."
  (curl -sf "${OLLAMA_BASE_URL}/api/pull" \
    -d "{\"name\":\"${OLLAMA_MODEL}\",\"stream\":false}" \
    -H "Content-Type: application/json" \
    --max-time 600 \
    && echo "Ollama model pull complete: ${OLLAMA_MODEL}" \
    && echo "Warming up Ollama model in background: ${OLLAMA_MODEL} ..." \
    && curl -sf "${OLLAMA_BASE_URL}/api/generate" \
      -d "{\"model\":\"${OLLAMA_MODEL}\",\"prompt\":\"Respond with OK.\",\"stream\":false}" \
      -H "Content-Type: application/json" \
      --max-time "${OLLAMA_TIMEOUT}" >/dev/null \
    && echo "Ollama model warm-up complete: ${OLLAMA_MODEL}" \
    || echo "Warning: Ollama model preparation failed (AI summary may be slow or unavailable)") &
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
