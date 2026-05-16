# --------------------------------------------------
# ログベースメトリクス: タスク失敗検知
# --------------------------------------------------
resource "google_logging_metric" "task_failed" {
  project = var.project_id
  name    = "devforge/task_failed"
  filter  = "jsonPayload.status=\"failed\""

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
}

# --------------------------------------------------
# アラートポリシー: タスク失敗
# --------------------------------------------------
resource "google_monitoring_alert_policy" "task_failed_alert" {
  project      = var.project_id
  display_name = "DevForge Task Failed"
  combiner     = "OR"

  conditions {
    display_name = "Task failure detected"
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/devforge/task_failed\" AND resource.type=\"cloud_run_revision\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      duration        = "0s"

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_COUNT"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.name]
}
