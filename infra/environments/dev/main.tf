provider "google" {
  project = var.project_id
  region  = local.region
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

locals {
  stack_name = "${var.app_name}-dev"
  region     = "asia-northeast1"
}

module "service_account" {
  source = "../../modules/service_account"

  project_id                     = var.project_id
  stack_name                     = local.stack_name
  deployer_service_account_email = var.deployer_service_account_email
}

module "artifact_registry" {
  source = "../../modules/artifact_registry"

  project_id = var.project_id
  region     = local.region
  stack_name = local.stack_name
}

module "cloud_tasks" {
  source = "../../modules/cloud_tasks"

  project_id = var.project_id
  location   = local.region
  queue_name = "devforge-ai-tasks-dev"
}

module "cloud_run" {
  source = "../../modules/cloud_run"

  project_id                  = var.project_id
  region                      = local.region
  stack_name                  = local.stack_name
  service_account_email       = module.service_account.email
  enable_github_oauth         = var.enable_github_oauth
  turso_database_url          = var.turso_database_url
  cors_origins                = var.cors_origins
  callback_base_url           = var.callback_base_url
  environment                 = "dev"
  task_runner                 = "cloud_tasks"
  cloud_tasks_queue           = module.cloud_tasks.queue_name
  cloud_tasks_location        = local.region
  cloud_tasks_service_account = module.service_account.email
  upstash_redis_url           = var.upstash_redis_url
  upstash_redis_token         = var.upstash_redis_token
}

module "monitoring" {
  source = "../../modules/monitoring"

  project_id       = var.project_id
  cloud_run_domain = replace(module.cloud_run.service_url, "https://", "")
  alert_email      = var.alert_email
}

module "cloudflare" {
  source = "../../modules/cloudflare"

  cloudflare_account_id = var.cloudflare_account_id
  cloudflare_zone_id    = var.cloudflare_zone_id
  project_name          = var.cloudflare_pages_project_name
  subdomain             = var.cloudflare_subdomain
  production_branch     = "dev"
}

output "stack_name" {
  value = local.stack_name
}

output "template_version" {
  value = var.template_version
}

output "artifact_registry_url" {
  value = module.artifact_registry.url
}

output "cloudflare_pages_subdomain" {
  value = module.cloudflare.pages_subdomain
}

output "cloudflare_pages_project_name" {
  value = module.cloudflare.pages_project_name
}
