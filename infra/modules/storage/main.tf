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

resource "google_storage_bucket" "frontend" {
  project                     = var.project_id
  name                        = "${var.stack_name}-frontend"
  location                    = var.region
  uniform_bucket_level_access = true

  website {
    main_page_suffix = "index.html"
    not_found_page   = "index.html"
  }

  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD"]
    response_header = ["Content-Type"]
    max_age_seconds = 3600
  }
}

resource "google_storage_bucket_iam_member" "frontend_public" {
  bucket = google_storage_bucket.frontend.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}
