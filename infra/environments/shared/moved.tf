# 既存の root module 直下の module 群を devforge_stack 配下へネストした移行。
# pre-release で state が空でも、途中で state を残した環境があっても no-op へ寄せる。
moved {
  from = module.service_account
  to   = module.devforge_stack.module.service_account
}

moved {
  from = module.artifact_registry
  to   = module.devforge_stack.module.artifact_registry
}

moved {
  from = module.cloud_tasks
  to   = module.devforge_stack.module.cloud_tasks
}

moved {
  from = module.cloud_run
  to   = module.devforge_stack.module.cloud_run
}

moved {
  from = module.monitoring
  to   = module.devforge_stack.module.monitoring
}

moved {
  from = module.cloudflare
  to   = module.devforge_stack.module.cloudflare
}

moved {
  from = google_project_service.apis["artifactregistry.googleapis.com"]
  to   = module.devforge_stack.google_project_service.apis["artifactregistry.googleapis.com"]
}

moved {
  from = google_project_service.apis["run.googleapis.com"]
  to   = module.devforge_stack.google_project_service.apis["run.googleapis.com"]
}

moved {
  from = google_project_service.apis["secretmanager.googleapis.com"]
  to   = module.devforge_stack.google_project_service.apis["secretmanager.googleapis.com"]
}

moved {
  from = google_project_service.apis["cloudtasks.googleapis.com"]
  to   = module.devforge_stack.google_project_service.apis["cloudtasks.googleapis.com"]
}

moved {
  from = google_project_service.apis["monitoring.googleapis.com"]
  to   = module.devforge_stack.google_project_service.apis["monitoring.googleapis.com"]
}

moved {
  from = google_project_service.apis["logging.googleapis.com"]
  to   = module.devforge_stack.google_project_service.apis["logging.googleapis.com"]
}

# firebase モジュール廃止に伴う古い address からの移行。
moved {
  from = module.firebase.google_project_iam_member.deployer_artifact_registry_writer[0]
  to   = module.devforge_stack.module.service_account.google_project_iam_member.deployer_artifact_registry_writer[0]
}

moved {
  from = module.firebase.google_project_iam_member.deployer_run_developer[0]
  to   = module.devforge_stack.module.service_account.google_project_iam_member.deployer_run_developer[0]
}

moved {
  from = module.resume_stack.google_service_account.app
  to   = module.devforge_stack.module.service_account.google_service_account.app
}

moved {
  from = module.resume_stack.google_artifact_registry_repository.app
  to   = module.devforge_stack.module.artifact_registry.google_artifact_registry_repository.app
}

moved {
  from = module.resume_stack.google_secret_manager_secret.app
  to   = module.devforge_stack.module.cloud_run.google_secret_manager_secret.app
}

moved {
  from = module.resume_stack.google_secret_manager_secret_iam_member.app
  to   = module.devforge_stack.module.cloud_run.google_secret_manager_secret_iam_member.app
}

moved {
  from = module.resume_stack.google_cloud_run_v2_service.app
  to   = module.devforge_stack.module.cloud_run.google_cloud_run_v2_service.app
}

moved {
  from = module.resume_stack.google_cloud_run_v2_service_iam_member.public_access
  to   = module.devforge_stack.module.cloud_run.google_cloud_run_v2_service_iam_member.public_access
}
