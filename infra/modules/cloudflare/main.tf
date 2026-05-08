terraform {
  required_providers {
    cloudflare = {
      source = "cloudflare/cloudflare"
    }
  }
}

# Cloudflare Pages プロジェクト
resource "cloudflare_pages_project" "app" {
  account_id        = var.cloudflare_account_id
  name              = var.project_name
  production_branch = var.production_branch

  build_config {
    # wrangler-action による直接アップロードを使用するため、ここのビルド設定はドキュメント目的。
    # 実際のビルドは GitHub Actions 上で npm run build を実行し dist を wrangler でデプロイする。
    build_command       = "cd frontend && npm ci && npm run build"
    destination_dir     = "frontend/dist"
    root_dir            = ""
  }
}

# app.<zone> へ CNAME レコードを作成（Cloudflare Proxy 経由）
resource "cloudflare_record" "app" {
  zone_id = var.cloudflare_zone_id
  name    = var.subdomain
  type    = "CNAME"
  value   = cloudflare_pages_project.app.subdomain
  proxied = true
}
