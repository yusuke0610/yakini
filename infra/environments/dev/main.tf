provider "google" {
  project = var.project_id
  region  = "asia-northeast1"
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

# --------------------------------------------------------------------
# dev 環境の stack composition
# 各 module の呼び出しは ../../modules/devforge_stack に集約されている。
# 環境差分（環境名、Cloudflare Pages 設定、production branch）のみここで渡す。
# --------------------------------------------------------------------
module "devforge_stack" {
  source = "../../modules/devforge_stack"

  environment                    = "dev"
  project_id                     = var.project_id
  app_name                       = var.app_name
  template_version               = var.template_version
  deployer_service_account_email = var.deployer_service_account_email

  cors_origins        = var.cors_origins
  callback_base_url   = var.callback_base_url
  enable_github_oauth = var.enable_github_oauth

  alert_email = var.alert_email

  upstash_redis_url   = var.upstash_redis_url
  upstash_redis_token = var.upstash_redis_token

  turso_database_url = var.turso_database_url

  cloudflare_account_id         = var.cloudflare_account_id
  cloudflare_zone_id            = var.cloudflare_zone_id
  cloudflare_pages_project_name = var.cloudflare_pages_project_name
  cloudflare_subdomain          = var.cloudflare_subdomain
  cloudflare_production_branch  = "dev"
}

output "stack_name" {
  value = module.devforge_stack.stack_name
}

output "template_version" {
  value = var.template_version
}

output "artifact_registry_url" {
  value = module.devforge_stack.artifact_registry_url
}

output "cloudflare_pages_subdomain" {
  value = module.devforge_stack.cloudflare_pages_subdomain
}

output "cloudflare_pages_project_name" {
  value = module.devforge_stack.cloudflare_pages_project_name
}
