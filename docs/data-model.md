# データベース・データモデル

Turso (libSQL) の運用、Alembic マイグレーション、テーブル設計方針を扱います。

## データベース・マイグレーション

### Turso (libSQL)

- **本番**: Turso Cloud（東京リージョン `nrt`）。`turso CLI` で DB と auth token を発行し、URL は Cloud Run 環境変数、トークンは Secret Manager に登録
- **ローカル**: `turso dev --db-file ./backend/local.sqlite` で libSQL HTTP サーバーを起動
- **接続**: `app.core.settings.build_sqlalchemy_database_url()` が `TURSO_DATABASE_URL` を SQLAlchemy URL（HTTP/HTTPS は `sqlite+libsql://`、ローカルファイルは `sqlite:///`）に変換
- **ローカル DB**: `backend/local.sqlite` はコミットしない。必要時に自動生成/再作成する

### Turso CLI セットアップ（本番）

DB は Turso (libSQL) を使用します。OpenTofu の対象外なので、`turso CLI` で各環境のリソースを手動作成します。

```bash
# 認証
turso auth login

# dev / stg / prod それぞれの DB を東京リージョン (nrt) で作成
turso db create devforge-dev --location nrt
turso db create devforge-stg --location nrt
turso db create devforge-prod --location nrt

# 接続 URL を確認（libsql://devforge-<env>-<username>.turso.io）
turso db show devforge-dev --url

# 認証トークンを発行（環境ごとに分ける）
turso db tokens create devforge-dev
turso db tokens create devforge-stg
turso db tokens create devforge-prod
```

発行した URL とトークンは次のように設定します。

| 値 | 配置先 |
|---|---|
| `TURSO_DATABASE_URL` | Cloud Run 環境変数（OpenTofu `terraform.tfvars` の `turso_database_url`） |
| `TURSO_AUTH_TOKEN` | Secret Manager `devforge-<env>-turso-auth-token`（OpenTofu で secret 本体は作成済み、version は手動で追加） |

GitHub Actions の OpenTofu CI でも `TF_VAR_turso_database_url` を GitHub Secrets 経由で渡してください。

### Alembic マイグレーション

本番環境では Cloud Run 起動時に自動実行される（`alembic upgrade head`）。
手動実行は `make` 経由（Nix devshell ラップ）で行う:

```bash
make migrate                                 # alembic upgrade head
make migrate-create MSG="add user table"     # 新規マイグレーション生成
```

設定: `backend/alembic.ini` / `backend/alembic_migrations/versions`
libSQL は SQLite 互換で ALTER COLUMN 非対応のため、複雑なスキーマ変更は `batch_alter_table` を使う。

## データ設計メモ

- `basic_info` / `resumes` は **1ユーザー1件**
- `career_analyses` は **複数バージョン保持可能**（分析履歴として蓄積）
- `intelligence_cache` / `blog_summary_cache` は **1ユーザー1件**（最新結果のみ保持）
- 可変長データは JSON ではなく子テーブルに正規化
  - `basic_info_qualifications`
  - `resume_experiences` / `resume_clients` / `resume_projects` / `resume_project_*`
  - `blog_article_tags`
- 日付は DB では `DATE` として保持
  - 日単位: `record_date` / `birthday` / `blog_articles.published_at`
  - 月単位: 職務経歴・学歴・職歴は月初日に正規化して保存し、API では `YYYY-MM` で返却
- `blog_articles` は `account_id` 起点で管理し、`platform` は `blog_accounts` から解決
- 非同期タスクはステータスフィールド（`pending` / `running` / `completed` / `failed`）で管理し、フロントエンドはポーリングで結果を取得する
