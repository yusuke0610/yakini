# Resume Builder

基本情報・職務経歴書・履歴書をUIから入力し、PostgreSQLに保存してPDF出力できるアプリです。

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
- `db`: PostgreSQL (Docker Compose)

## 1. PostgreSQL起動

```bash
docker compose up -d
```

## 2. バックエンド起動

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 3. フロントエンド起動

別ターミナルで:

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

ブラウザで `http://localhost:5173` を開きます。

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

### その他
- `GET /health`: ヘルスチェック

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
   - `yakini-dev`
   - `yakini-stg`
   - `yakini-prod`
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
  - `terraform plan -backend=false` 相当のローカル検証

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

## メモ
- DBテーブルはFastAPI起動時に自動作成されます。
- CORS許可元は `backend/.env` の `CORS_ORIGINS` で調整できます。
- 旧スキーマのテーブルがある場合は `docker compose down -v` でボリュームを削除して再作成してください。
