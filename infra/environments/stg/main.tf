locals {
  stack_name = "${var.app_name}-stg"
  region     = "asia-northeast1"
}

module "service_account" {
  source = "../../modules/service_account"

  project_id = var.project_id
  stack_name = local.stack_name
}

module "artifact_registry" {
  source = "../../modules/artifact_registry"

  project_id = var.project_id
  region     = local.region
  stack_name = local.stack_name
}

module "storage" {
  source = "../../modules/storage"

  project_id            = var.project_id
  region                = local.region
  stack_name            = local.stack_name
  service_account_email = module.service_account.email
}

module "cloud_run" {
  source = "../../modules/cloud_run"

  project_id                      = var.project_id
  region                          = local.region
  stack_name                      = local.stack_name
  service_account_email           = module.service_account.email
  artifact_registry_repository_id = module.artifact_registry.repository_id
  db_backup_bucket_name           = module.storage.db_backup_bucket_name
  cors_origins                    = var.cors_origins
}

output "stack_name" {
  value = local.stack_name
}

output "template_version" {
  value = var.template_version
}
