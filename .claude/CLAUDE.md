# DevForge - Claude Code ガイドライン

## コーディング規約

### 共通ルール
- **コメント・ドキュメント**: コード内のコメント、docstring、JSDoc はすべて**日本語**で記述すること。
- **エラーメッセージ**: HTTPException の `detail` 等、ユーザーに返すエラーメッセージはすべて**日本語**で記述すること。
- **例外の握りつぶし禁止**: `except SomeException: pass` は禁止。最低でも `logger.debug/warning/error` でログを出すこと。補助的な処理（通知など）で例外を抑制する場合も `logger.warning` でログを残すこと。

### Python (backend)
- ruff に準拠すること
- PEP8を守るな、PEP8を理解した上で抽象化しろ
- ruff の設定は `backend/pyproject.toml` に定義済み
- コード変更後は `cd backend && .venv/bin/python -m ruff check app tests alembic_migrations` を実行し、違反がないことを確認すること
- 未使用の import を残さないこと（F401）

### TypeScript/React (frontend)
- ESLint / Prettier の設定に従うこと
- `cd frontend && npm run lint` でリントチェック

## CI 確認ルール

アプリケーションの改修を行った場合、以下のコマンドで CI 相当のチェックをローカルで実行し、パスすることを確認すること:

```bash
# backend
cd backend && .venv/bin/python -m ruff check app tests alembic_migrations && .venv/bin/python -m pytest -q tests

# frontend（ユニット・ビルド）
cd frontend && npm run lint && npm test && npm run build

# frontend E2E（新機能・ページ追加・ルーティング変更・認証フロー変更を行った場合は必須）
cd frontend && npm run test:e2e
```

**E2E テスト実行のトリガー**: 以下のいずれかに該当する変更を行った場合、必ず E2E テストを実行すること:
- 新しいページまたはルートの追加
- 認証・ナビゲーション・レイアウトの変更
- 通知ベルなどサイドバーコンポーネントの変更
- バックエンド API の追加・変更で、フロントエンドの UI フローに影響するもの

CI 定義: `.github/workflows/ci.yml`

## 命名規約

| 種別 | 名前 |
|---|---|
| 職務経歴書（career history） | `Resume` / `resumes` テーブル |
| 履歴書（personal CV） | `Rirekisho` / `rirekisho` テーブル |

> `rirekisho` は日本語ローマ字のため cSpell の警告が出るが無視してよい。

## 環境変数（必須）

```
SQLITE_DB_PATH       # Cloud Run: /tmp/devforge.sqlite
SECRET_KEY           # CSRF等で引き続き使用
JWT_PRIVATE_KEY      # RS256署名用秘密鍵（PEM形式）
JWT_PUBLIC_KEY       # RS256検証用公開鍵（PEM形式）
FIELD_ENCRYPTION_KEY # Fernet鍵
GCS_BUCKET_NAME      # バックアップ用 GCS バケット名
GCS_DB_OBJECT        # 例: devforge/dev/db.sqlite
ADMIN_TOKEN          # /admin/backup エンドポイント用
CORS_ORIGINS         # 例: https://devforge-dev.example.com
COOKIE_SECURE        # 例: true
COOKIE_SAMESITE      # lax / strict / none
```

### オプション
```
GITHUB_CLIENT_ID     # GitHub OAuth Client ID
GITHUB_CLIENT_SECRET # GitHub OAuth Client Secret
LLM_PROVIDER         # ollama / vertex
VERTEX_PROJECT_ID    # Vertex AI 用
VERTEX_LOCATION      # 例: asia-northeast1
VERTEX_MODEL         # 例: gemini-2.5-flash-lite
```

## スコープ別ルール

バックエンド・フロントエンド・インフラ固有のルール（アーキテクチャ、DB設計、認証、LLM統合等）は `.claude/rules/` に分割済み。対象パスのファイルを編集する際に自動でロードされる。
