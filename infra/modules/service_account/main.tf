resource "google_service_account" "app" {
  project      = var.project_id
  account_id   = "${var.stack_name}-run"
  display_name = "${var.stack_name} Cloud Run runtime SA"
}
