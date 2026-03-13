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

## 運用ルール

- `dev` -> `stg` -> `prod` の順で `template_version` を更新
- `main` マージ前に GitHub Actions の `Terraform CI` が成功していることを確認

## State 移行 (resume_stack からの移行)

既存環境で state 移行が必要な場合、以下のコマンドを実行してください:

```bash
# 各環境ディレクトリで実行
terraform state mv 'module.resume_stack.google_service_account.app' 'module.service_account.google_service_account.app'
terraform state mv 'module.resume_stack.google_artifact_registry_repository.app' 'module.artifact_registry.google_artifact_registry_repository.app'
terraform state mv 'module.resume_stack.google_storage_bucket.db_backup' 'module.storage.google_storage_bucket.db_backup'
terraform state mv 'module.resume_stack.google_storage_bucket_iam_member.app_db_backup' 'module.storage.google_storage_bucket_iam_member.app_db_backup'
terraform state mv 'module.resume_stack.google_storage_bucket.frontend' 'module.storage.google_storage_bucket.frontend'
terraform state mv 'module.resume_stack.google_storage_bucket_iam_member.frontend_public' 'module.storage.google_storage_bucket_iam_member.frontend_public'
terraform state mv 'module.resume_stack.google_secret_manager_secret.app' 'module.cloud_run.google_secret_manager_secret.app'
terraform state mv 'module.resume_stack.google_secret_manager_secret_iam_member.app' 'module.cloud_run.google_secret_manager_secret_iam_member.app'
terraform state mv 'module.resume_stack.google_cloud_run_v2_service.app' 'module.cloud_run.google_cloud_run_v2_service.app'
terraform state mv 'module.resume_stack.google_cloud_run_v2_service_iam_member.public_access' 'module.cloud_run.google_cloud_run_v2_service_iam_member.public_access'
```
