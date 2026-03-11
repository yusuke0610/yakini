# Terraform Template

このディレクトリは `HCP Terraform Free` を前提にした環境テンプレートです。

## 構成
- `environments/dev|stg|prod`: 環境ごとのエントリポイント
- `modules/resume_stack`: 再利用モジュール

## バージョン管理
- Terraform本体: 各環境の `versions.tf` で `required_version` を固定
- インフラテンプレート: 各環境の `terraform.tfvars` で `template_version` を管理

## 初期設定 (HCP Terraform Free)
1. HCP Terraform で Organization を作成
2. Workspaces を3つ作成
   - `devforge-dev`
   - `devforge-stg`
   - `devforge-prod`
3. 各環境の `versions.tf` を編集し、`organization` を自分の組織名に変更

## ローカル検証コマンド
```bash
terraform -chdir=infra/environments/dev init -backend=false
terraform -chdir=infra/environments/dev validate
```

## plan/apply 実行
- `cloud {}` ブロックを使っているため、`plan` / `apply` は HCP Terraform Workspace 実行を前提にします。
- ローカルで `plan` したい場合は、`terraform login` 実施後に `-backend=false` を外して `terraform init` を実行してください。

## 運用ルール
- `dev` -> `stg` -> `prod` の順で `template_version` を更新
- `main` マージ前に GitHub Actions の `Terraform CI` が成功していることを確認
