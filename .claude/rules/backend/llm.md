---
paths:
  - backend/app/services/intelligence/**
---

# LLM 統合

- `LLM_PROVIDER` 環境変数で `ollama`（デフォルト）/ `vertex` を切替
- `LLMClient` 抽象基底クラスの `generate(system_prompt, user_prompt)` インターフェースに従うこと
- Vertex AI は `google-genai` SDK（`genai.Client(vertexai=True)` + `client.aio.models.generate_content()`）を使用
- 非同期 API は `client.aio.models.generate_content()` を使う（`generate_content_async` ではない）
