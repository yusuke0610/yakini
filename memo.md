変更まとめ

  backend/app/services/intelligence/llm/vertex_client.py

  - _extract_usage() を追加：response.usage_metadata から prompt_tokens / output_tokens / total_tokens / cached_tokens を取得（欠損・SDK 差分に耐える getattr + isinstance
  ガード）
  - 生成成功ログ（vertex_client.py:100）の extra= に展開

  ruff 通過、既存 LLM テスト 26 件 pass。

  dev での確認手順

  1. デプロイ: このブランチを dev 環境（Cloud Run）に適用
  2. キャリア分析を 1〜2 回実行: 実運用経路で走らせる
  3. Cloud Logging で確認: 以下クエリで当該ログを抽出

  resource.type="cloud_run_revision"
  jsonPayload.message="Vertex AI 生成完了"
  jsonPayload.prompt_tokens>0

  4. 見るべき値:
    - duration_ms: 現状の単発呼び出しレイテンシ（P95 のベースライン）
    - prompt_tokens / output_tokens / total_tokens: 統合版の現行トークン消費
    - これで 「分割すると概ね ×3 + 共通コンテキスト重複分で +XX%」 の見積りと突き合わせ可能

  動作確認ができたら、ログ値を貼ってもらえれば Phase 0 の runbook 化に進みます。