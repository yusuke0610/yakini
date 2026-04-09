# --------------------------------------------------
# 通知チャンネル: メール（無料）
# --------------------------------------------------
resource "google_monitoring_notification_channel" "email" {
  project      = var.project_id
  display_name = "DevForge Alert Email"
  type         = "email"
  labels = {
    email_address = var.alert_email
  }
}

# --------------------------------------------------
# Uptime Check（無料枠: 月 1M チェックまで）
# 5分間隔で /health を監視する
# --------------------------------------------------
resource "google_monitoring_uptime_check_config" "api_health" {
  project      = var.project_id
  display_name = "DevForge API Health"
  timeout      = "10s"
  period       = "300s"

  http_check {
    path         = "/health"
    port         = "443"
    use_ssl      = true
    validate_ssl = true
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = var.cloud_run_domain
    }
  }
}

# --------------------------------------------------
# アラートポリシー: Uptime Check 失敗
# --------------------------------------------------
resource "google_monitoring_alert_policy" "uptime_failure" {
  project      = var.project_id
  display_name = "DevForge API Down"
  combiner     = "OR"

  conditions {
    display_name = "Uptime check failure"
    condition_threshold {
      filter          = "metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\" AND resource.type=\"uptime_url\""
      comparison      = "COMPARISON_LT"
      threshold_value = 1
      duration        = "300s"

      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_NEXT_OLDER"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.name]
}

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
      filter          = "metric.type=\"logging.googleapis.com/user/devforge/task_failed\""
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
