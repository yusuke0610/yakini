resource "google_service_account" "app" {
  project      = var.project_id
  account_id   = "${var.stack_name}-run"
  display_name = "${var.stack_name} Cloud Run runtime SA"
}

resource "google_project_iam_member" "aiplatform_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.app.email}"
}
