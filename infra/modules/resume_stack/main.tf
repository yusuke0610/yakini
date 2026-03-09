locals {
  stack_name = "${var.app_name}-${var.environment}"
  region     = "asia-northeast1"
}

resource "google_artifact_registry_repository" "app" {
  project       = var.project_id
  location      = local.region
  repository_id = local.stack_name
  format        = "DOCKER"
}

resource "google_cloud_run_v2_service" "app" {
  project             = var.project_id
  name                = local.stack_name
  location            = local.region
  deletion_protection = false

  template {
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
