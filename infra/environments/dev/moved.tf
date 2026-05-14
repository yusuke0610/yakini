# firebase モジュール廃止に伴い、deployer IAM を service_account モジュールへ移設
# deployer_service_account_email が設定されている環境でのみ有効
moved {
  from = module.firebase.google_project_iam_member.deployer_artifact_registry_writer[0]
  to   = module.service_account.google_project_iam_member.deployer_artifact_registry_writer[0]
}

moved {
  from = module.firebase.google_project_iam_member.deployer_run_developer[0]
  to   = module.service_account.google_project_iam_member.deployer_run_developer[0]
}

moved {
  from = module.resume_stack.google_service_account.app
  to   = module.service_account.google_service_account.app
}

moved {
  from = module.resume_stack.google_artifact_registry_repository.app
  to   = module.artifact_registry.google_artifact_registry_repository.app
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
