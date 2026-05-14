# Terraform Infrastructure

GCP インフラストラクチャを Terraform で管理するディレクトリです。

## 構成

```
infra/
├── environments/
│   ├── dev/          # 開発環境
│   ├── stg/          # ステージング環境
│   └── prod/         # 本番環境
└── modules/
    ├── artifact_registry/   # Docker イメージリポジトリ
    ├── cloud_run/           # Cloud Run サービス + Secret Manager
    ├── cloud_tasks/         # Cloud Tasks キュー
    ├── cloudflare/          # Cloudflare Pages + DNS
    ├── monitoring/          # Cloud Monitoring アラート
    └── service_account/     # Cloud Run 用サービスアカウント
```

## モジュール

| モジュール | 概要 |
|---|---|
| `service_account` | Cloud Run ランタイム用のサービスアカウント |
| `artifact_registry` | Docker イメージの Artifact Registry リポジトリ |
| `cloud_run` | Cloud Run サービス、Secret Manager シークレット、IAM |
| `cloud_tasks` | バックグラウンドタスク用 Cloud Tasks キュー |
| `cloudflare` | Cloudflare Pages プロジェクトと DNS レコード |
| `monitoring` | Cloud Run エラーレート等のアラート設定 |

> **DB は Turso (libSQL) に移行済み**。GCS の SQLite バックアップ用バケット (`storage` モジュール) は廃止済みです。Turso のリソースは Terraform 外（`turso CLI` 手動）で管理します。詳細は下記「Turso のセットアップ」を参照してください。

## バージョン管理

- Terraform 本体: 各環境の `versions.tf` で `required_version` を固定
- インフラテンプレート: 各環境の `terraform.tfvars` で `template_version` を管理

## ローカル検証コマンド

```bash
terraform -chdir=infra/environments/dev init -backend=false
terraform -chdir=infra/environments/dev validate
```

## plan/apply 実行

GCS backend を使用しているため、`terraform init` 時にバックエンドの認証が必要です。
ローカルで `plan` する場合は `gcloud auth application-default login` を実施してください。

Cloud Run サービスを Terraform で初回作成する場合は、`modules/cloud_run/main.tf` の `local.bootstrap_image` に定義された公開 hello イメージで起動します。Artifact Registry にアプリイメージが push されていなくても初回 apply が成立します。

GitHub Actions はその後 `gcloud run deploy` で新しいリビジョンを配備します。Terraform では Cloud Run の `image` 差分を無視するため、後続の `apply` で CI 配備済みイメージへ巻き戻しません。

Secret Manager は secret 本体だけでなく secret version が必要です。Cloud Run 起動前に最低でも以下 4 つの version を追加してください。

- `devforge-<env>-secret-key`
- `devforge-<env>-field-encryption-key`
- `devforge-<env>-admin-token`
- `devforge-<env>-turso-auth-token`

GitHub OAuth を使う場合だけ `enable_github_oauth = true` を設定し、さらに以下 2 つの version も追加してください。

- `devforge-<env>-github-client-id`
- `devforge-<env>-github-client-secret`

## Turso のセットアップ

DB は Turso (libSQL) を使用します。Terraform の対象外なので、`turso CLI` で各環境のリソースを手動作成します。

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
| `TURSO_DATABASE_URL` | Cloud Run 環境変数（Terraform `terraform.tfvars` の `turso_database_url`）|
| `TURSO_AUTH_TOKEN` | Secret Manager `devforge-<env>-turso-auth-token`（Terraform で secret 本体は作成済み、version は手動で追加）|

GitHub Actions の Terraform CI でも `TF_VAR_turso_database_url` を GitHub Secrets 経由で渡してください。

## 運用ルール

- `dev` -> `stg` -> `prod` の順で `template_version` を更新
- `main` マージ前に GitHub Actions の `Terraform CI` が成功していることを確認

## State 移行 (resume_stack からの移行)

各 environment には `moved` ブロックを定義してあり、`module.resume_stack.*` から新しい module address への state 移行は `terraform plan/apply` 時に自動で処理されます。

既に旧構成に対して `apply` を途中まで実行してしまった場合は、最新の設定を反映してから再度 `plan` を実行してください。`resume_stack` 配下の既存 state が残っているリソースは自動で移動され、実際に削除済みのリソースだけが再作成対象として残ります。
