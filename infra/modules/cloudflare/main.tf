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
}

# app.<zone> へ CNAME レコードを作成（Cloudflare Proxy 経由）
resource "cloudflare_record" "app" {
  zone_id = var.cloudflare_zone_id
  name    = var.subdomain
  type    = "CNAME"
  value   = cloudflare_pages_project.app.subdomain
  proxied = true
}
