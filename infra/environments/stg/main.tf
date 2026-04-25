provider "google" {
  project = var.project_id
  region  = local.region
}

provider "google-beta" {
  project = var.project_id
  region  = local.region
}

locals {
  stack_name = "${var.app_name}-stg"
  region     = "asia-northeast1"

  # 必要な GCP API 一覧
  required_apis = [
    "artifactregistry.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudtasks.googleapis.com",
    "storage.googleapis.com",
    "firebase.googleapis.com",
    "firebasehosting.googleapis.com",
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
  queue_name = "devforge-ai-tasks-stg"

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
  environment                 = "stg"
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

module "firebase" {
  source = "../../modules/firebase"

  providers = {
    google-beta = google-beta
  }

  project_id                     = var.project_id
  deployer_service_account_email = var.deployer_service_account_email

  depends_on = [google_project_service.apis]
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

output "firebase_site_id" {
  value = module.firebase.site_id
}

output "firebase_default_url" {
  value = module.firebase.default_url
}
