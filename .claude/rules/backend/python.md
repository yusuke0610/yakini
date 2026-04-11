---
paths:
  - backend/**
---

# Python コーディング規約

- ruff に準拠すること（設定: `backend/pyproject.toml`）
- PEP8を守るな、PEP8を理解した上で抽象化しろ
- コード変更後は `cd backend && .venv/bin/python -m ruff check app tests alembic_migrations` を実行し、違反がないことを確認すること
- 未使用の import を残さないこと（F401）

## 例外処理の必須ルール

- **`except SomeException: pass` は絶対禁止**。例外を握りつぶすと障害調査が不可能になる
- 最低でも `logger.debug/warning/error` でログを出すこと
- 補助的な処理（通知生成など）でメインフローへの影響を避けるために例外を抑制する場合も `logger.warning` でログを残すこと
- 正しいパターン例:
  ```python
  # 補助処理で例外を抑制する場合
  try:
      _create_notification(...)
  except Exception:
      logger.warning("通知作成に失敗 (無視)", exc_info=True)

  # 想定内の例外でスキップする場合
  except HTTPException:
      logger.debug("Referer が CORS_ORIGINS に含まれないためスキップ: %s", referer)
  ```

## システムパッケージと Dockerfile

- Pythonライブラリがシステムパッケージ（C ライブラリ等）に依存する場合、`backend/Dockerfile` の `apt-get install` にも該当パッケージを追加すること
- ローカルで `brew install` 等を行った場合は、必ず Dockerfile 側にも対応する Debian パッケージを追加し、Cloud Run デプロイに影響がないことを確認すること
