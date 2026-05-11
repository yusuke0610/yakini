provider "google" {
  project = var.project_id
  region  = local.region
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

locals {
  stack_name = "${var.app_name}-prod"
  region     = "asia-northeast1"

  # 必要な GCP API 一覧
  required_apis = [
    "artifactregistry.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudtasks.googleapis.com",
    "storage.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
  ]
}

resource "google_project_service" "apis" {
  for_each = toset(local.required_apis)

  project                    = var.project_id
  service                    = each.value
  disable_on_destroy         = false
  disable_dependent_services = false
}

module "service_account" {
  source = "../../modules/service_account"

  project_id                     = var.project_id
  stack_name                     = local.stack_name
  deployer_service_account_email = var.deployer_service_account_email

  depends_on = [google_project_service.apis]
}

module "artifact_registry" {
  source = "../../modules/artifact_registry"

  project_id = var.project_id
  region     = local.region
  stack_name = local.stack_name

  depends_on = [google_project_service.apis]
}

module "storage" {
  source = "../../modules/storage"

  project_id            = var.project_id
  region                = local.region
  stack_name            = local.stack_name
  service_account_email = module.service_account.email

  depends_on = [google_project_service.apis]
}

module "cloud_tasks" {
  source = "../../modules/cloud_tasks"

  project_id = var.project_id
  location   = local.region
  queue_name = "devforge-ai-tasks-prod"

  depends_on = [google_project_service.apis]
}

module "cloud_run" {
  source = "../../modules/cloud_run"

  project_id                  = var.project_id
  region                      = local.region
  stack_name                  = local.stack_name
  service_account_email       = module.service_account.email
  enable_github_oauth         = var.enable_github_oauth
  db_backup_bucket_name       = module.storage.db_backup_bucket_name
  cors_origins                = var.cors_origins
  callback_base_url           = var.callback_base_url
  environment                 = "prod"
  task_runner                 = "cloud_tasks"
  cloud_tasks_queue           = module.cloud_tasks.queue_name
  cloud_tasks_location        = local.region
  cloud_tasks_service_account = module.service_account.email
  upstash_redis_url           = var.upstash_redis_url
  upstash_redis_token         = var.upstash_redis_token

  depends_on = [google_project_service.apis]
}

module "monitoring" {
  source = "../../modules/monitoring"

  project_id       = var.project_id
  cloud_run_domain = replace(module.cloud_run.service_url, "https://", "")
  alert_email      = var.alert_email

  depends_on = [google_project_service.apis]
}

module "cloudflare" {
  source = "../../modules/cloudflare"

  cloudflare_account_id = var.cloudflare_account_id
  cloudflare_zone_id    = var.cloudflare_zone_id
  project_name          = var.cloudflare_pages_project_name
  subdomain             = var.cloudflare_subdomain
  production_branch     = "main"
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
