# DevForge - Claude Code ガイドライン

## コーディング規約

### 共通ルール
- **コメント・ドキュメント**: コード内のコメント、docstring、JSDoc はすべて**日本語**で記述すること。
- **エラーメッセージ**: HTTPException の `detail` 等、ユーザーに返すエラーメッセージはすべて**日本語**で記述すること。

### Python (backend)
- PEP 8 / flake8 に準拠すること
- flake8 の設定は `backend/setup.cfg` に定義済み（max-line-length=120）
- コード変更後は `cd backend && .venv/bin/python -m flake8` を実行し、違反がないことを確認すること
- 未使用の import を残さないこと（F401）

### TypeScript/React (frontend)
- ESLint / Prettier の設定に従うこと
- `cd frontend && npm run lint` でリントチェック

## CI 確認ルール

アプリケーションの改修を行った場合、以下のコマンドで CI 相当のチェックをローカルで実行し、パスすることを確認すること:

```bash
# backend
cd backend && .venv/bin/python -m flake8 && .venv/bin/python -m pytest -q tests

# frontend
cd frontend && npm run lint && npm test && npm run build
```

CI 定義: `.github/workflows/ci.yml`

## アーキテクチャ上の重要な決定事項

### SQLite + Cloud Run + GCS 方式

- Cloud Run は `/tmp/devforge.sqlite` を使用（`SQLITE_DB_PATH` 環境変数）
- **起動時**: `bootstrap.py` が GCS から SQLite を復元（なければ空DBで起動）
- **多重起動防止**: `max_instances = 1` で SQLite の競合を回避
- **バックアップ方式**: tmp オブジェクト → `blob.rewrite()` → tmp削除（アトミック置き換え）
- **ローカルDB**: `backend/local.sqlite` は開発用の生成物であり、Git に含めないこと

### バックアップ失敗時の方針
- 明示実行された `POST /admin/backup` / `python -m app.backup` は失敗時にエラーを返す
- 通常の CRUD では自動バックアップしない
- 起動時の復元失敗は `WARNING` ログを出し、空DBで継続する

### 認証
- JWT（`python-jose`）+ bcrypt（`passlib`）
- **`bcrypt==3.2.2` に固定**（passlib 1.7.4 は bcrypt 4.x と非互換）
- GitHub OAuth ログインに対応（`GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` の設定が必要）
- GitHub OAuth の `state` は **backend 側 Cookie で検証**する。frontend だけで検証しないこと
- 認証Cookie属性は `COOKIE_SECURE` / `COOKIE_SAMESITE` で制御する

### 暗号化
- 履歴書（Rirekisho）の個人情報フィールド（email / phone / postal_code / address）は `encryption.py` で暗号化保存
- `FIELD_ENCRYPTION_KEY` 環境変数（Fernet）

### セキュリティ
- 外部API呼び出しや LLM 実行のような**高コスト endpoint**には rate limit を付けること
- OAuth 開始URLは backend で発行し、許可された `CORS_ORIGINS` のみをリダイレクト先に使うこと
- cookie 認証を使う変更では `Secure` / `SameSite` / CORS の整合を必ず確認すること

### システムパッケージと Dockerfile
- Pythonライブラリがシステムパッケージ（C ライブラリ等）に依存する場合、`backend/Dockerfile` の `apt-get install` にも該当パッケージを追加すること
- ローカルで `brew install` 等を行った場合は、必ず Dockerfile 側にも対応する Debian パッケージを追加し、Cloud Run デプロイに影響がないことを確認すること

## 命名規約

| 種別 | 名前 |
|---|---|
| 職務経歴書（career history） | `Resume` / `resumes` テーブル |
| 履歴書（personal CV） | `Rirekisho` / `rirekisho` テーブル |

> `rirekisho` は日本語ローマ字のため cSpell の警告が出るが無視してよい。

## DB設計ルール

- `basic_info` / `resumes` / `rirekisho` は **1ユーザー1件** を前提にし、`user_id` を一意制約で縛ること
- 可変長データを JSON カラムへ増やさないこと。資格・学歴・職歴・職務経歴の明細・ブログタグは子テーブルへ正規化すること
- 日付は可能な限り DB の `DATE` / `TIMESTAMP` を使うこと
- `blog_articles` は `account_id` 起点で管理し、`user_id` や `platform` を冗長保持しないこと

## 環境変数（必須）

```
SQLITE_DB_PATH       # Cloud Run: /tmp/devforge.sqlite
SECRET_KEY           # JWT署名キー
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
```
