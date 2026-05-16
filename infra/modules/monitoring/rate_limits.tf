# --------------------------------------------------
# ログベースメトリクス: レートリミット超過検知
# main.py の _rate_limit_handler が出力する 429 WARNING ログを集計する。
# slowapi の default_limits (300/min) または個別 @limiter.limit に
# 引っかかったリクエストすべてを含む。
# --------------------------------------------------
resource "google_logging_metric" "rate_limit_exceeded" {
  project = var.project_id
  name    = "devforge/rate_limit_exceeded"
  filter  = <<-EOT
    resource.type="cloud_run_revision"
    severity="WARNING"
    jsonPayload.message="rate_limit_exceeded"
  EOT

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
}

# --------------------------------------------------
# アラートポリシー: レートリミット連発
# 5 分間に 500 件超で発火（攻撃が遮断されている状態の検知）。
# auth_failed_alert より閾値を低くし、攻撃が遮断中であることを早期に把握できるようにする。
# --------------------------------------------------
resource "google_monitoring_alert_policy" "rate_limit_exceeded_alert" {
  project      = var.project_id
  display_name = "DevForge Rate Limit Surge"
  combiner     = "OR"

  conditions {
    display_name = "rate_limit_exceeded > 500 / 5min"
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/devforge/rate_limit_exceeded\" AND resource.type=\"cloud_run_revision\""
      comparison      = "COMPARISON_GT"
      threshold_value = 500
      duration        = "60s"

      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_COUNT"
      }
    }
  }

  alert_strategy {
    auto_close = "1800s"
  }

  documentation {
    content   = <<-EOT
      レートリミット超過（429）が 5 分間に 500 件を超えました。
      攻撃が slowapi で自動遮断されている状態です。

      初動:
      1. Cloud Logging で `jsonPayload.message="rate_limit_exceeded"` をフィルタ
      2. `jsonPayload.client_ip` で攻撃元 IP を特定
      3. 必要なら GCP Armor で恒久ブロック

      runbook: docs/runbooks/alert-policies.md
    EOT
    mime_type = "text/markdown"
  }

  notification_channels = [google_monitoring_notification_channel.email.name]
}
