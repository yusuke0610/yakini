#!/usr/bin/env sh
set -eu

python -m app.db.bootstrap
export APP_BOOTSTRAPPED=1

# Ollama モデルを同期で pull してから uvicorn を起動する
# バックグラウンド pull だと pull 完了前にリクエストが来た際に 404 になるため同期化する
if [ -n "${OLLAMA_BASE_URL:-}" ]; then
  OLLAMA_MODEL="${OLLAMA_MODEL:-gemma3:4b}"
  OLLAMA_TIMEOUT="${OLLAMA_TIMEOUT:-600}"

  # Ollama サーバが起動するまで最大 30 秒待機
  echo "Waiting for Ollama to be ready..."
  for i in $(seq 1 30); do
    if curl -sf "${OLLAMA_BASE_URL}/api/tags" >/dev/null 2>&1; then
      echo "Ollama is ready."
      break
    fi
    sleep 1
  done

  # モデルを同期で pull（失敗してもサーバは起動する）
  echo "Pulling Ollama model: ${OLLAMA_MODEL} ..."
  if curl -sf "${OLLAMA_BASE_URL}/api/pull" \
    -d "{\"name\":\"${OLLAMA_MODEL}\",\"stream\":false}" \
    -H "Content-Type: application/json" \
    --max-time 600; then
    echo "Ollama model pull complete: ${OLLAMA_MODEL}"
    echo "Warming up Ollama model: ${OLLAMA_MODEL} ..."
    curl -sf "${OLLAMA_BASE_URL}/api/generate" \
      -d "{\"model\":\"${OLLAMA_MODEL}\",\"prompt\":\"Respond with OK.\",\"stream\":false}" \
      -H "Content-Type: application/json" \
      --max-time "${OLLAMA_TIMEOUT}" >/dev/null \
      && echo "Ollama model warm-up complete: ${OLLAMA_MODEL}" \
      || echo "Warning: Ollama model warm-up failed (AI features may be slow on first request)"
  else
    echo "Warning: Ollama model pull failed (AI features may be unavailable)"
  fi
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
