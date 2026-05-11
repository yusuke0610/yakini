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
    ├── service_account/     # Cloud Run 用サービスアカウント
    └── storage/             # GCS バケット (DB バックアップ / フロントエンド)
```

## モジュール

| モジュール | 概要 |
|---|---|
| `service_account` | Cloud Run ランタイム用のサービスアカウント |
| `artifact_registry` | Docker イメージの Artifact Registry リポジトリ |
| `storage` | DB バックアップ用バケットとフロントエンドホスティング用バケット |
| `cloud_run` | Cloud Run サービス、Secret Manager シークレット、IAM |

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

Secret Manager は secret 本体だけでなく secret version が必要です。Cloud Run 起動前に最低でも以下 3 つの version を追加してください。

- `devforge-<env>-secret-key`
- `devforge-<env>-field-encryption-key`
- `devforge-<env>-admin-token`

GitHub OAuth を使う場合だけ `enable_github_oauth = true` を設定し、さらに以下 2 つの version も追加してください。

- `devforge-<env>-github-client-id`
- `devforge-<env>-github-client-secret`

## 運用ルール

- `dev` -> `stg` -> `prod` の順で `template_version` を更新
- `main` マージ前に GitHub Actions の `Terraform CI` が成功していることを確認

## State 移行 (resume_stack からの移行)

各 environment には `moved` ブロックを定義してあり、`module.resume_stack.*` から新しい module address への state 移行は `terraform plan/apply` 時に自動で処理されます。

既に旧構成に対して `apply` を途中まで実行してしまった場合は、最新の設定を反映してから再度 `plan` を実行してください。`resume_stack` 配下の既存 state が残っているリソースは自動で移動され、実際に削除済みのリソースだけが再作成対象として残ります。
