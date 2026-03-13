# devforge — CLAUDE.md

個人用Webアプリ（履歴書・職務経歴書の作成・PDF/Markdown出力）。
SRE志向のパイプライン学習を目的として構築中。

---

## 技術スタック

| 層 | 技術 |
|---|---|
| フロントエンド | React + TypeScript (Vite) |
| バックエンド | FastAPI (Python 3.11) |
| DB | SQLite（Cloud Run想定、GCSでバックアップ永続化） |
| インフラ | GCP: Cloud Run / GCS / Secret Manager / Artifact Registry |
| IaC | Terraform（環境別 dev/stg/prod、GCS backend） |
| CI/CD | GitHub Actions |

---

## ディレクトリ構成

```
devforge/
├── backend/                       # FastAPI アプリ
│   ├── app/
│   │   ├── main.py                # エンドポイント定義
│   │   ├── models.py              # SQLAlchemy モデル（User / BasicInfo / Resume / Rirekisho）
│   │   ├── repositories.py        # リポジトリ層
│   │   ├── schemas.py             # Pydantic スキーマ
│   │   ├── auth.py                # JWT + bcrypt 認証
│   │   ├── bootstrap.py           # 起動時処理（GCS復元 → migration）
│   │   ├── database.py            # DB接続設定
│   │   ├── encryption.py          # Fernet フィールド暗号化
│   │   ├── logging_utils.py       # 構造化ログ
│   │   ├── migrations.py          # Alembic実行
│   │   ├── settings.py            # 環境変数読み込み
│   │   ├── backup.py              # バックアップCLI
│   │   └── services/
│   │       ├── sqlite_backup.py   # GCSバックアップ/復元
│   │       ├── pdf/               # PDF出力
│   │       │   ├── pdf_service.py
│   │       │   ├── generators/    # resume_generator / rirekisho_generator
│   │       │   └── utils/         # pdf_utils
│   │       └── markdown/          # Markdown出力
│   │           ├── markdown_service.py
│   │           ├── generators/    # resume_generator / rirekisho_generator
│   │           ├── templates/     # resume_template / rirekisho_template
│   │           └── utils/         # markdown_utils
│   ├── alembic_migrations/
│   │   └── versions/              # 0001〜0007
│   ├── tests/
│   │   ├── test_auth.py
│   │   ├── test_schemas.py
│   │   └── test_pdf_generator.py
│   ├── scripts/entrypoint.sh      # bootstrap → uvicorn
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx                # メインコンポーネント（認証画面含む）
│   │   ├── api.ts                 # API クライアント
│   │   ├── types.ts               # 型定義
│   │   ├── payloadBuilders.ts     # フォーム → API ペイロード変換
│   │   ├── styles.css             # スタイル
│   │   └── main.tsx               # エントリポイント
│   ├── index.html
│   └── vite.config.ts
├── infra/
│   ├── environments/{dev,stg,prod}/  # 環境別 Terraform
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── terraform.tfvars
│   │   ├── versions.tf
│   │   └── backend.tf
│   └── modules/                      # リソース別モジュール
│       ├── artifact_registry/        # Docker イメージリポジトリ
│       ├── cloud_run/                # Cloud Run + Secret Manager
│       ├── service_account/          # Cloud Run 用 SA
│       └── storage/                  # GCS バケット（DB / フロントエンド）
├── .github/workflows/
│   ├── ci.yml                     # frontend + backend テスト
│   └── terraform-ci.yml           # fmt + validate
├── scripts/
│   └── setup-git-hooks.sh         # main保護用gitフック設定
├── docker-compose.yml
└── README.md
```

---

## アーキテクチャ上の重要な決定事項

### SQLite + Cloud Run + GCS 方式

- Cloud Run は `/tmp/devforge.sqlite` を使用（`SQLITE_DB_PATH` 環境変数）
- **起動時**: `bootstrap.py` が GCS から SQLite を復元（なければ空DBで起動）
- **多重起動防止**: `max_instances = 1` で SQLite の競合を回避
- **バックアップ方式**: tmp オブジェクト → `blob.rewrite()` → tmp削除（アトミック置き換え）

### バックアップ失敗時の方針
- アップロード失敗 → **APIは成功扱い**（データはローカルに保存済）
- ログに `WARNING` を出力して終了、リトライなし
- 次の書き込み時に再バックアップされるため個人利用では許容範囲

### 認証
- JWT（`python-jose`）+ bcrypt（`passlib`）
- `bcrypt==3.2.2` に固定（passlib 1.7.4 は bcrypt 4.x と非互換）
- 新規ユーザーは `/auth/register` エンドポイントで登録（画面から新規登録可能）
- GitHub OAuth ログインに対応（`GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` の設定が必要）

### 暗号化
- 履歴書（Rirekisho）の個人情報フィールド（email / phone / postal_code / address）は `encryption.py` で暗号化保存
- `FIELD_ENCRYPTION_KEY` 環境変数（Fernet）

---

## 命名規約

| 種別 | 名前 |
|---|---|
| 職務経歴書（career history） | `Resume` / `resumes` テーブル |
| 履歴書（personal CV） | `Rirekisho` / `rirekisho` テーブル |

> `rirekisho` は日本語ローマ字のため cSpell の警告が出るが無視してよい。

---

## 環境変数（必須）

```
SQLITE_DB_PATH       # Cloud Run: /tmp/devforge.sqlite
SECRET_KEY           # JWT署名キー（python -c "import secrets; print(secrets.token_hex(32))"）
FIELD_ENCRYPTION_KEY # Fernet鍵（cryptography.fernet.Fernet.generate_key()）
GCS_BUCKET_NAME      # バックアップ用 GCS バケット名
GCS_DB_OBJECT        # 例: devforge/dev/db.sqlite
ADMIN_TOKEN          # /admin/backup エンドポイント用
CORS_ORIGINS         # 例: https://devforge-dev.example.com
```

### オプション
```
GITHUB_CLIENT_ID     # GitHub OAuth Client ID
GITHUB_CLIENT_SECRET # GitHub OAuth Client Secret
```

docker-compose.yml では `${VAR}` 形式でルートの `.env` から読み込む。

---

## Terraform 構成方針

### GCS backend

```hcl
# infra/environments/{env}/backend.tf
terraform {
  backend "gcs" {
    bucket = "devforge-tfstate-{env}"   # 環境別バケット
    prefix = "terraform/state"
  }
}
```

tfstate バケットは手動で作成（Terraform管理外）:
```bash
gcloud storage buckets create gs://devforge-tfstate-dev \
  --location=asia-northeast1 --uniform-bucket-level-access
```

### Terraform モジュール構成

| モジュール | リソース |
|---|---|
| `service_account` | `google_service_account` — Cloud Run 実行 SA |
| `artifact_registry` | `google_artifact_registry_repository` — Docker イメージ |
| `storage` | `google_storage_bucket` × 2（DB バックアップ / フロントエンド）、`google_storage_bucket_iam_member` × 2 |
| `cloud_run` | `google_cloud_run_v2_service`、`google_cloud_run_v2_service_iam_member`、`google_secret_manager_secret`、`google_secret_manager_secret_iam_member` |

### Cloud Run 推奨設定（SQLite前提）

```hcl
max_instance_count = 1   # SQLite競合防止
min_instance_count = 0   # コスト最小（コールドスタート許容）
concurrency        = 80  # デフォルト値でOK（max=1なので競合なし）
cpu                = "1000m"
memory             = "512Mi"
```

### IAM 最小権限

Cloud Run SA に必要な権限:
- `roles/storage.objectAdmin`（バックアップ用バケットのみ）
- `roles/secretmanager.secretAccessor`（自環境の Secret のみ）

---

## CI/CD パイプライン設計

```
PR → main:
  ci.yml          : frontend test + build + backend test
  terraform-ci.yml: fmt check → validate（全環境）

merge → main:
  将来: dev apply（自動）
  stg/prod apply: workflow_dispatch（手動承認）
```

現状: fmt + validate のみ（init -backend=false）

---

## テスト

```bash
# バックエンド
cd backend && python -m pytest -q tests/

# フロントエンド
cd frontend && npm test
```

テストファイル:
- `tests/test_auth.py`        : hash_password / verify_password / create_access_token
- `tests/test_schemas.py`     : Resume / Rirekisho スキーマバリデーション
- `tests/test_pdf_generator.py`: PDF生成の smoke test

---

## ローカル開発

```bash
# バックエンド
cd backend && uvicorn app.main:app --reload --port 8000

# Docker（統合確認）
docker compose down -v && docker compose up --build
```

`.env`（ルート）は `docker-compose.yml` が参照。
`backend/.env` はローカル uvicorn 用（Docker には自動で読み込まれない）。

---

## stg / prod 環境の将来構成方針

**現状**: dev のみで開発・動作確認を継続（個人プロジェクト・学習目的）

**将来（実装時期未確定）**: アプリをユーザに提供できる状態になった段階で実装予定

| 項目 | 方針 |
|---|---|
| インフラ | GKE または Kubernetes ベースの構成に移行 |
| DB | RDB（費用対効果の良いもの、例: Cloud SQL / AlloyDB Omni 等を比較検討） |
| GCP プロジェクト | 環境ごとに分離（`devforge-stg` / `devforge-prod`） |
| tfstate | GCS backend（`devforge-tfstate-stg` / `devforge-tfstate-prod`） |

stg/prod の Terraform ファイルは現在プレースホルダー状態だが、backend・tfvars・variables・main は整備済み。
GKE/RDB への切り替え時に合わせて各モジュール（`modules/cloud_run` 等）も再設計する。

---

## Pending / Future Features

### パスワードリセット機能
- メールアドレスはユーザー登録時に保存済み
- SMTP基盤の導入後にメールベースのパスワードリセットフローを実装予定

### 書き込み後自動バックアップ
- 各 write エンドポイントに `BackgroundTasks` でバックアップを追加
- バックアップ失敗のアラート（ログ監視 or Cloud Monitoring アラート）

### PDF Generation History
- 生成した PDF を保存し、過去のドキュメントを閲覧可能にする
- 実装案: PDF をクラウドストレージに保存 + メタデータを DB に保存

### セキュリティ強化
- GitHub Actions を SA キー → Workload Identity Federation（OIDC）に移行
- Secret Manager の rotation 設定
- Cloud Run のカスタムドメイン + HTTPS
