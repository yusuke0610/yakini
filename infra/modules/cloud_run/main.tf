locals {
  secret_names = [
    "secret-key",
    "field-encryption-key",
    "admin-token",
    "github-client-id",
    "github-client-secret",
  ]
}

resource "google_secret_manager_secret" "app" {
  for_each  = toset(local.secret_names)
  project   = var.project_id
  secret_id = "${var.stack_name}-${each.key}"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_iam_member" "app" {
  for_each  = google_secret_manager_secret.app
  project   = var.project_id
  secret_id = each.value.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}

resource "google_cloud_run_v2_service" "app" {
  project             = var.project_id
  name                = var.stack_name
  location            = var.region
  deletion_protection = false

  template {
    service_account = var.service_account_email

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_registry_repository_id}/${var.stack_name}:latest"

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
        value = "/tmp/devforge.sqlite"
      }
      env {
        name  = "GCS_BUCKET_NAME"
        value = var.db_backup_bucket_name
      }
      env {
        name  = "GCS_DB_OBJECT"
        value = "db.sqlite"
      }
      env {
        name  = "CORS_ORIGINS"
        value = var.cors_origins
      }

      env {
        name  = "LLM_PROVIDER"
        value = var.llm_provider
      }
      env {
        name  = "VERTEX_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "VERTEX_LOCATION"
        value = var.region
      }
      env {
        name  = "VERTEX_MODEL"
        value = var.vertex_model
      }

      dynamic "env" {
        for_each = {
          SECRET_KEY           = "secret-key"
          FIELD_ENCRYPTION_KEY = "field-encryption-key"
          ADMIN_TOKEN          = "admin-token"
          GITHUB_CLIENT_ID     = "github-client-id"
          GITHUB_CLIENT_SECRET = "github-client-secret"
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
  location = var.region
  name     = google_cloud_run_v2_service.app.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
