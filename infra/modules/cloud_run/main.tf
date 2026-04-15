locals {
  secret_names = [
    "secret-key",
    "field-encryption-key",
    "admin-token",
    "github-client-id",
    "github-client-secret",
    # 棚卸し TODO: "field-encryption-key"（FIELD_ENCRYPTION_KEY / Fernet 鍵）は
    # PII 削除対応（Rirekisho 個人情報フィールドの暗号化廃止）が完了した場合、
    # このリストから除外し対応する Secret Manager シークレットを削除すること。
    # 削除前に全環境（dev/stg/prod）の Cloud Run 設定から環境変数を外すこと。
  ]
  required_secret_env = {
    SECRET_KEY           = "secret-key"
    FIELD_ENCRYPTION_KEY = "field-encryption-key"
    ADMIN_TOKEN          = "admin-token"
  }
  github_secret_env = var.enable_github_oauth ? {
    GITHUB_CLIENT_ID     = "github-client-id"
    GITHUB_CLIENT_SECRET = "github-client-secret"
  } : {}
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
      image = var.bootstrap_image != "" ? var.bootstrap_image : "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_registry_repository_id}/${var.stack_name}:${var.container_image_tag}"

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
        name  = "ENVIRONMENT"
        value = var.environment
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

      env {
        name  = "TASK_RUNNER"
        value = var.task_runner
      }
      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "CLOUD_TASKS_QUEUE"
        value = var.cloud_tasks_queue
      }
      env {
        name  = "CLOUD_TASKS_LOCATION"
        value = var.cloud_tasks_location
      }
      env {
        name  = "CLOUD_TASKS_SERVICE_URL"
        value = var.cloud_tasks_service_url
      }
      env {
        name  = "CLOUD_TASKS_SERVICE_ACCOUNT"
        value = var.cloud_tasks_service_account
      }
      env {
        name  = "UPSTASH_REDIS_URL"
        value = var.upstash_redis_url
      }
      env {
        name  = "UPSTASH_REDIS_TOKEN"
        value = var.upstash_redis_token
      }
      env {
        # Cloud Logging 向け JSON フォーマットを有効化
        name  = "LOG_FORMAT"
        value = "json"
      }
      env {
        # 通常運用は INFO。パフォーマンス分析時のみ DEBUG に変更する
        name  = "LOG_LEVEL"
        value = "INFO"
      }

      dynamic "env" {
        for_each = local.required_secret_env
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

      dynamic "env" {
        for_each = local.github_secret_env
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

  lifecycle {
    # CI deploys new revisions with gcloud run deploy, so Terraform should not
    # try to force the service back to the bootstrap image tag on later applies.
    ignore_changes = [template[0].containers[0].image]
  }
}

resource "google_cloud_run_v2_service_iam_member" "public_access" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.app.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
