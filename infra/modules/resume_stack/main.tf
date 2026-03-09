locals {
  stack_name = "${var.app_name}-${var.environment}"
  region     = "asia-northeast1"

  secret_names = [
    "secret-key",
    "initial-username",
    "initial-password",
    "field-encryption-key",
    "admin-token",
  ]
}

resource "google_service_account" "app" {
  project      = var.project_id
  account_id   = "${local.stack_name}-run"
  display_name = "${local.stack_name} Cloud Run runtime SA"
}

resource "google_artifact_registry_repository" "app" {
  project       = var.project_id
  location      = local.region
  repository_id = local.stack_name
  format        = "DOCKER"
}

resource "google_storage_bucket" "db_backup" {
  project                     = var.project_id
  name                        = "${local.stack_name}-db"
  location                    = local.region
  uniform_bucket_level_access = true
  versioning { enabled = true }
}

resource "google_storage_bucket_iam_member" "app_db_backup" {
  bucket = google_storage_bucket.db_backup.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.app.email}"
}

resource "google_secret_manager_secret" "app" {
  for_each  = toset(local.secret_names)
  project   = var.project_id
  secret_id = "${local.stack_name}-${each.key}"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_iam_member" "app" {
  for_each  = google_secret_manager_secret.app
  project   = var.project_id
  secret_id = each.value.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.app.email}"
}

resource "google_cloud_run_v2_service" "app" {
  project             = var.project_id
  name                = local.stack_name
  location            = local.region
  deletion_protection = false

  template {
    service_account = google_service_account.app.email

    containers {
      image = "${local.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.app.repository_id}/${local.stack_name}:latest"

      resources {
        limits = {
          cpu    = "1000m"
          memory = "512Mi"
        }
      }
      ports {
        container_port = 8000
      }

      env {
        name  = "SQLITE_DB_PATH"
        value = "/tmp/yakini.sqlite"
      }
      env {
        name  = "GCS_BUCKET_NAME"
        value = google_storage_bucket.db_backup.name
      }
      env {
        name  = "GCS_DB_OBJECT"
        value = "db.sqlite"
      }
      env {
        name  = "CORS_ORIGINS"
        value = var.cors_origins
      }

      dynamic "env" {
        for_each = {
          SECRET_KEY           = "secret-key"
          INITIAL_USERNAME     = "initial-username"
          INITIAL_PASSWORD     = "initial-password"
          FIELD_ENCRYPTION_KEY = "field-encryption-key"
          ADMIN_TOKEN          = "admin-token"
        }
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.app[env.value].secret_id
              version = "latest"
            }
          }
        }
      }
    }

    max_instance_request_concurrency = 80

    scaling {
      max_instance_count = 1
      min_instance_count = 0
    }
  }
}

resource "google_cloud_run_v2_service_iam_member" "public_access" {
  project  = var.project_id
  location = local.region
  name     = google_cloud_run_v2_service.app.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_storage_bucket" "frontend" {
  project                     = var.project_id
  name                        = "${local.stack_name}-frontend"
  location                    = local.region
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
