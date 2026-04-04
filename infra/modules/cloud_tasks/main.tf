resource "google_cloud_tasks_queue" "ai_tasks" {
  name     = var.queue_name
  location = var.location
  project  = var.project_id

  rate_limits {
    max_dispatches_per_second = 1
    max_concurrent_dispatches = 1 # SQLite 同時書き込み防止
  }

  retry_config {
    max_attempts       = 3
    min_backoff        = "10s"
    max_backoff        = "300s"
    max_retry_duration = "3600s"
  }
}
