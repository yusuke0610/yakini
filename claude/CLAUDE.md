# devforge — CLAUDE.md

個人用Webアプリ（履歴書・職務経歴書の作成・PDF出力）。
SRE志向のパイプライン学習を目的として構築中。

---

## 技術スタック

| 層 | 技術 |
|---|---|
| フロントエンド | React + TypeScript (Vite) |
| バックエンド | FastAPI (Python 3.11) |
| DB | SQLite（Cloud Run想定、GCSでバックアップ永続化） |
| インフラ | GCP: Cloud Run / GCS / Secret Manager |
| IaC | Terraform（環境別 dev/stg/prod） |
| CI/CD | GitHub Actions |

---

## ディレクトリ構成

```
devforge/
├── backend/               # FastAPI アプリ
│   ├── app/
│   │   ├── main.py        # エンドポイント定義
│   │   ├── models.py      # SQLAlchemy モデル（Resume / Rirekisho / User）
│   │   ├── repositories.py
│   │   ├── schemas.py     # Pydantic スキーマ
│   │   ├── auth.py        # JWT + bcrypt 認証
│   │   ├── bootstrap.py   # 起動時処理（GCS復元 → migration → user seed）
│   │   └── services/
│   │       ├── sqlite_backup.py   # GCSバックアップ/復元
│   │       └── pdf_generator.py  # PDF出力
│   ├── alembic_migrations/
│   ├── scripts/entrypoint.sh     # bootstrap → uvicorn
│   └── requirements.txt
├── frontend/
├── infra/
│   ├── environments/{dev,stg,prod}/  # 環境別 Terraform
│   └── modules/resume_stack/          # 共通モジュール（現在 locals のみ）
└── .github/workflows/
    ├── ci.yml             # frontend + backend テスト
    └── terraform-ci.yml   # fmt + validate
```

---

## アーキテクチャ上の重要な決定事項

### SQLite + Cloud Run + GCS 方式

- Cloud Run は `/tmp/devforge.sqlite` を使用（`SQLITE_DB_PATH` 環境変数）
- **起動時**: `bootstrap.py` が GCS から SQLite を復元（なければ空DBで起動）
- **書き込み後**: 各 write エンドポイントで `BackgroundTasks` を使い非同期バックアップ
- **多重起動防止**: `max_instances = 1` で SQLite の競合を回避
- **バックアップ方式**: tmp オブジェクト → `blob.rewrite()` → tmp削除（アトミック置き換え）

```python
# 書き込み後バックアップの実装パターン（未実装、次フェーズ）
from fastapi import BackgroundTasks
from .services.sqlite_backup import backup_sqlite_to_gcs

def _auto_backup() -> None:
    try:
        backup_sqlite_to_gcs()
    except Exception:
        log_event(logging.WARNING, "auto_backup_failed")  # APIは成功扱いのまま

@app.post("/api/rirekisho")
def create_rirekisho(payload: RirekishoCreate, background_tasks: BackgroundTasks, ...):
    result = RirekishoRepository(db).create(payload.model_dump())
    background_tasks.add_task(_auto_backup)
    return result
```

### バックアップ失敗時の方針
- アップロード失敗 → **APIは成功扱い**（データはローカルに保存済）
- ログに `WARNING` を出力して終了、リトライなし
- 次の書き込み時に再バックアップされるため個人利用では許容範囲

### 認証
- JWT（`python-jose`）+ bcrypt（`passlib`）
- `bcrypt==3.2.2` に固定（passlib 1.7.4 は bcrypt 4.x と非互換）
- 起動時に `INITIAL_USERNAME` / `INITIAL_PASSWORD` でユーザーをシード（users テーブルが空の場合のみ）

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
INITIAL_USERNAME     # 初回起動時のユーザー名
INITIAL_PASSWORD     # 初回起動時のパスワード
FIELD_ENCRYPTION_KEY # Fernet鍵（cryptography.fernet.Fernet.generate_key()）
GCS_BUCKET_NAME      # バックアップ用 GCS バケット名
GCS_DB_OBJECT        # 例: devforge/dev/db.sqlite
ADMIN_TOKEN          # /admin/backup エンドポイント用
CORS_ORIGINS         # 例: https://devforge-dev.example.com
```

docker-compose.yml では `${VAR}` 形式でルートの `.env` から読み込む。

---

## Terraform 構成方針

### GCS backend（HCP Cloud の代替）

```hcl
# infra/environments/{env}/versions.tf
terraform {
  required_version = "~> 1.8.0"
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

### 追加が必要な Terraform リソース（modules/resume_stack）

```
google_project_service        # Cloud Run, Secret Manager, GCS APIs
google_storage_bucket         # DBバックアップ用（versioning有効）
google_service_account        # Cloud Run 実行SA
google_storage_bucket_iam_member  # SA → バケット: storage.objects.{get,create,list}
google_secret_manager_secret  # SECRET_KEY, FIELD_ENCRYPTION_KEY 等
google_cloud_run_v2_service   # API（max_instance_count=1, min=0）
```

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
- `roles/storage.objectAdmin`（バックアップ用バケットのみ、条件付き）
- `roles/secretmanager.secretAccessor`（自環境の Secret のみ）

CI/CD 実行SA（GitHub Actions）:
- 当面: SA キーを GitHub Secrets に登録
- 将来: Workload Identity Federation（OIDC）に移行

---

## CI/CD パイプライン設計

```
PR → main:
  ci.yml          : frontend test + build + backend test
  terraform-ci.yml: fmt check → validate（全環境）→ plan dev（GCS backend認証あり）

merge → main:
  terraform-ci.yml: dev apply（自動）
  stg/prod apply  : workflow_dispatch（手動承認）
```

現状: fmt + validate のみ（init -backend=false）
次フェーズ: GCS backend 認証 → plan を PR に追加

---

## 優先タスク（次に実装すべき順）

### Phase 1: Cloud Run 稼働（最優先）
1. `versions.tf` の `cloud {}` ブロックを GCS backend に差し替え
2. Terraform module に最小リソースを追加（GCS bucket / Cloud Run / SA / IAM）
3. `docker-compose.yml` の Secret は `.env` から、本番は Secret Manager から
4. GitHub Actions に GCP 認証（SA キー）と `dev apply` ステップを追加

### Phase 2: 書き込み後自動バックアップ
5. 各 write エンドポイントに `BackgroundTasks` でバックアップを追加
6. バックアップ失敗のアラート（ログ監視 or Cloud Monitoring アラート）

### Phase 3: セキュリティ強化
7. GitHub Actions を SA キー → Workload Identity Federation（OIDC）に移行
8. Secret Manager の rotation 設定
9. Cloud Run のカスタムドメイン + HTTPS

### Phase 4: 将来の Postgres 移行（条件: 複数ユーザー or データ量増加時）
- Repository 層は既に分離済みのため、`DATABASE_URL` 環境変数を追加するだけで切替可能
- Alembic は既に使用中のためマイグレーション運用はそのまま流用
- データ移行: `sqlite3 .dump` → psql インポート or カスタムスクリプト

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
GKE/RDB への切り替え時に合わせて `modules/resume_stack` も再設計する。

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
# ※ -v でボリューム削除 → bootstrap が再実行されユーザーが再作成される
```

`.env`（ルート）は `docker-compose.yml` が参照。
`backend/.env` はローカル uvicorn 用（Docker には自動で読み込まれない）。

---

## Pending / Future Features

### PDF Generation History

**現在の動作:**
- PDF はオンデマンドで生成し、即時ダウンロード
- 生成されたファイルは保存されない

**将来の計画:**
- 生成した PDF を保存し、過去のドキュメントを閲覧可能にする
- 実装案:
  - PDF をクラウドストレージ（例: Google Cloud Storage）に保存
  - メタデータを DB に保存（user_id, document_type, created_at, file_path）

**備考:**
- 現在の実装をシンプルに保つため意図的に後回しにしている
- 実装時、PDF サービスは「直接ダウンロード」と「永続ストレージ」の両方をサポートする設計にすること
- 現在のアーキテクチャ（`build_resume_pdf` / `build_rirekisho_pdf` が bytes を返す設計）は将来のストレージ対応と互換性がある
