resource "google_service_account" "app" {
  project      = var.project_id
  account_id   = "${var.stack_name}-run"
  display_name = "${var.stack_name} Cloud Run runtime SA"
}

resource "google_service_account_iam_member" "deployer_act_as" {
  count = var.deployer_service_account_email != "" ? 1 : 0

  service_account_id = google_service_account.app.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${var.deployer_service_account_email}"
}

# firebase モジュールから移設（Cloudflare Pages 移行に伴う整理）
resource "google_project_iam_member" "deployer_artifact_registry_writer" {
  count = var.deployer_service_account_email != "" ? 1 : 0

  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${var.deployer_service_account_email}"
}

resource "google_project_iam_member" "deployer_run_developer" {
  count = var.deployer_service_account_email != "" ? 1 : 0

  project = var.project_id
  role    = "roles/run.developer"
  member  = "serviceAccount:${var.deployer_service_account_email}"
}

resource "google_project_iam_member" "aiplatform_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.app.email}"
}

resource "google_project_iam_member" "cloud_tasks_enqueuer" {
  project = var.project_id
  role    = "roles/cloudtasks.enqueuer"
  member  = "serviceAccount:${google_service_account.app.email}"
}
