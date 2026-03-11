# Resume Builder

基本情報・職務経歴書・履歴書をUIから入力し、SQLiteに保存してPDF出力できるアプリです。

## 入力項目
### 基本情報
- 氏名
- 記載日
- 資格（取得日 + 名称、複数追加/削除）

### 職務経歴書
- 職務要約
- 自己PR
- 職務経歴（開始、在職の有無: 離職/在職、離職年月、会社名、職種、業務内容、実績、従業員数、資本金）
- 技術スタック（言語、フレームワーク、OS、DB、クラウドリソース、開発支援ツールを複数追加/削除）

### 履歴書
- 郵便番号
- 都道府県
- 住所（フリー入力）
- メールアドレス
- 電話番号
- 学歴（複数追加/削除）
- 職歴（複数追加/削除）
- 志望動機

## 構成
- `frontend`: TypeScript + React (Vite)
- `backend`: Python + FastAPI + SQLAlchemy
- `db`: SQLite

## 1. バックエンド起動 (SQLite)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.bootstrap
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

`SQLITE_DB_PATH=./local.sqlite` でローカル永続ファイルを使います。

## 2. フロントエンド起動

別ターミナルで:

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

ブラウザで `http://localhost:5173` を開きます。

## 3. Docker起動 (FastAPIのみ)
```bash
docker compose up --build
```

## API概要
### 基本情報
- `POST /api/basic-info`: 作成
- `PUT /api/basic-info/{id}`: 更新
- `GET /api/basic-info/latest`: 最新データ取得

### 職務経歴書
- `POST /api/resumes`: 作成
- `PUT /api/resumes/{id}`: 更新
- `GET /api/resumes/{id}`: 取得
- `GET /api/resumes/{id}/pdf`: PDFダウンロード

### 履歴書
- `POST /api/rirekisho`: 作成
- `PUT /api/rirekisho/{id}`: 更新
- `GET /api/rirekisho/{id}`: 取得
- `GET /api/rirekisho/{id}/pdf`: PDFダウンロード

### 管理
- `POST /admin/backup`: SQLite DBをGCSへバックアップ（Bearerトークン必須）

### その他
- `GET /health`: ヘルスチェック

## SQLite + GCSバックアップ/復元
### 環境変数
- `SQLITE_DB_PATH`: SQLiteファイルパス（例: `/tmp/devforge.sqlite`）
- `GCS_BUCKET_NAME`: バックアップ先バケット名（未設定ならGCS処理はスキップ）
- `GCS_DB_OBJECT`: バケット内オブジェクトキー（例: `devforge/dev/db.sqlite`）
- `ADMIN_TOKEN`: `/admin/backup` 用Bearerトークン

### 起動時フロー
1. `GCS_BUCKET_NAME` と `GCS_DB_OBJECT` が設定されていれば、GCS上のDBを `SQLITE_DB_PATH` へ復元
2. Alembicで `upgrade head` を適用
3. アプリ起動

### 復元失敗時の方針
- 復元失敗は警告ログを出して空DBで起動（初回起動を許容）
- ログはJSON形式の構造化ログで出力

### バックアップ
- 明示実行: `POST /admin/backup`（`Authorization: Bearer <ADMIN_TOKEN>`）
- CLI実行（任意）: `python -m app.backup`
- GCSアップロードは `tmp object` -> `final object(rewrite)` -> `tmp delete` の順で実施

## Alembicマイグレーション
- 設定: `backend/alembic.ini`
- マイグレーション: `backend/alembic_migrations/versions`
- 手動適用:
```bash
cd backend
alembic upgrade head
```
- SQLiteはDDL制約があるため、複雑なALTERはテーブル再作成型マイグレーションを推奨

## Cloud Run IAM最小権限
- `storage.objects.get`（復元）
- `storage.objects.create`（バックアップ）
- `storage.objects.list`（存在確認）

`ADMIN_TOKEN` などの秘密情報は Secret Manager 経由の環境変数注入を推奨。

## テスト
### フロントエンド
```bash
cd frontend
npm run test
```

### バックエンド
```bash
cd backend
.venv/bin/python -m pytest -q
```

## CI (GitHub Actions)
- ワークフロー: `.github/workflows/ci.yml`
- 実行タイミング:
  - `pull_request` (target: `main`, `frontend/**` または `backend/**` の変更時)
  - `push` (`main`, `frontend/**` または `backend/**` の変更時)
- 実行内容:
  - frontend: `npm run test`, `npm run build`
  - backend: `python -m pytest -q tests` (working-directory: `backend`)
- 低コスト運用の工夫:
  - Linuxランナーのみ使用
  - Node/Python依存キャッシュを利用
  - `concurrency` で古い実行を自動キャンセル

## Terraform (HCP Terraform Free)
- テンプレート配置: `infra/`
- 構成:
  - `infra/environments/dev|stg|prod`
  - `infra/modules/resume_stack`
- バージョン管理:
  - Terraform本体: 各環境の `versions.tf` (`required_version`)
  - テンプレート版: 各環境の `terraform.tfvars` (`template_version`)

### 初期設定
1. このリポジトリを `public` に設定
2. HCP Terraform で Organization を作成
3. Workspaces を作成
   - `devforge-dev`
   - `devforge-stg`
   - `devforge-prod`
4. `infra/environments/*/versions.tf` の `organization` を実値に変更

### Terraform検証CI
- ワークフロー: `.github/workflows/terraform-ci.yml`
- 実行タイミング:
  - `pull_request` (target: `main`, `infra/**` 変更時)
  - `push` (`main`, `infra/**` 変更時)
- 実行内容:
  - `terraform fmt -check -recursive`
  - `terraform init -backend=false`
  - `terraform validate`

### HCP Terraform での plan / apply
- `cloud {}` を使っているため、実際の `plan` / `apply` は HCP Terraform Workspace で実行
- GitHub Actions 側は無料枠を意識して静的検証 (`fmt/init/validate`) のみを実施

## main ブランチ保護
### ローカル（ターミナル）での直コミット/直push防止
```bash
./scripts/setup-git-hooks.sh
```

- `.githooks/pre-commit`: `main` への直接コミットを拒否
- `.githooks/pre-push`: `main` への直接pushを拒否

### GitHub 側での強制保護（推奨）
1. GitHub リポジトリの `Settings` -> `Branches` -> `Add branch protection rule`
2. `Branch name pattern` に `main` を設定
3. 以下を有効化
   - `Require a pull request before merging`
   - `Require status checks to pass before merging`
     - `test` (Application CI)
     - `terraform-fmt`
     - `terraform-validate-dev`
     - `terraform-validate-stg`
     - `terraform-validate-prod`
   - `Do not allow bypassing the above settings`（利用可能な場合）
4. 保存

---

## GCP デプロイ手順（dev 環境）

### 1. 事前準備

```bash
# gcloud 認証
gcloud auth login
gcloud config set project devforge-dev-20260223

# 必要な GCP API を有効化
gcloud services enable artifactregistry.googleapis.com
gcloud services enable run.googleapis.com
```

### 2. Terraform でインフラを構築する

GCS tfstate バケットが未作成の場合は先に作成する（Terraform 管理外）:

```bash
gcloud storage buckets create gs://devforge-tfstate-dev \
  --location=asia-northeast1 --uniform-bucket-level-access
```

インフラ構築:

```bash
cd infra/environments/dev
terraform init
terraform plan
terraform apply
```

### 3. Docker イメージをビルドして push する

> **注意**: Apple Silicon Mac（M1/M2/M3）は必ず `--platform linux/amd64` を付けること。
> 省略すると Cloud Run で `exec format error` が発生する。

```bash
# Docker → Artifact Registry の認証設定（初回のみ）
gcloud auth configure-docker asia-northeast1-docker.pkg.dev

# イメージをビルド（プロジェクトルートで実行）
docker build --platform linux/amd64 -t devforge-dev ./backend

# Artifact Registry 用にタグ付け
docker tag devforge-dev asia-northeast1-docker.pkg.dev/devforge-dev-20260223/devforge-dev/devforge-dev:latest

# push
docker push asia-northeast1-docker.pkg.dev/devforge-dev-20260223/devforge-dev/devforge-dev:latest
```

### 4. Cloud Run にデプロイする

```bash
gcloud run deploy devforge-dev \
  --image asia-northeast1-docker.pkg.dev/devforge-dev-20260223/devforge-dev/devforge-dev:latest \
  --region asia-northeast1 \
  --platform managed
```

デプロイ確認:

```bash
# サービス情報（URL 含む）を確認
gcloud run services describe devforge-dev --region asia-northeast1

# URL のみ取得
gcloud run services describe devforge-dev --region asia-northeast1 \
  --format "value(status.url)"
```

### 5. トラブルシューティング

#### GCP API が無効になっている

```
Error: googleapi: Error 403: ... is disabled
```

該当 API を有効化して再実行する:

```bash
gcloud services enable <API名>
# 例: gcloud services enable artifactregistry.googleapis.com
```

#### exec format error（arm64/amd64 の不一致）

```
exec /scripts/entrypoint.sh: exec format error
```

Apple Silicon Mac でビルドする際に `--platform linux/amd64` が抜けている。
イメージを再ビルドして push し直す:

```bash
docker build --platform linux/amd64 -t devforge-dev ./backend
docker tag devforge-dev asia-northeast1-docker.pkg.dev/devforge-dev-20260223/devforge-dev/devforge-dev:latest
docker push asia-northeast1-docker.pkg.dev/devforge-dev-20260223/devforge-dev/devforge-dev:latest
```

#### deletion_protection エラー（terraform destroy 時）

```
Error: Instance cannot be deleted because deletion protection is enabled
```

Terraform リソースの `deletion_protection = false` に変更して `terraform apply` 後、
`terraform destroy` を実行する。

---

## メモ
- DBスキーマは起動時にAlembicで適用されます。
- CORS許可元は `backend/.env` の `CORS_ORIGINS` で調整できます。
- Cloud Runのローカルファイルは永続化されないため、必要に応じてGCSバックアップを実行してください。
