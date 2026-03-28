moved {
  from = module.resume_stack.google_service_account.app
  to   = module.service_account.google_service_account.app
}

moved {
  from = module.resume_stack.google_artifact_registry_repository.app
  to   = module.artifact_registry.google_artifact_registry_repository.app
}

moved {
  from = module.resume_stack.google_storage_bucket.db_backup
  to   = module.storage.google_storage_bucket.db_backup
}

moved {
  from = module.resume_stack.google_storage_bucket_iam_member.app_db_backup
  to   = module.storage.google_storage_bucket_iam_member.app_db_backup
}

moved {
  from = module.resume_stack.google_secret_manager_secret.app
  to   = module.cloud_run.google_secret_manager_secret.app
}

moved {
  from = module.resume_stack.google_secret_manager_secret_iam_member.app
  to   = module.cloud_run.google_secret_manager_secret_iam_member.app
}

moved {
  from = module.resume_stack.google_cloud_run_v2_service.app
  to   = module.cloud_run.google_cloud_run_v2_service.app
}

moved {
  from = module.resume_stack.google_cloud_run_v2_service_iam_member.public_access
  to   = module.cloud_run.google_cloud_run_v2_service_iam_member.public_access
}
