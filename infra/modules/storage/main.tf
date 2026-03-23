resource "google_storage_bucket" "db_backup" {
  project                     = var.project_id
  name                        = "${var.stack_name}-db"
  location                    = var.region
  uniform_bucket_level_access = true
  versioning { enabled = true }
}

resource "google_storage_bucket_iam_member" "app_db_backup" {
  bucket = google_storage_bucket.db_backup.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.service_account_email}"
}
