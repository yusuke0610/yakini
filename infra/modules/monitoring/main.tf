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

# --------------------------------------------------
# ログベースメトリクス: 認証失敗検知
# auth.py の _raise_auth_failed が出力する WARNING ログを集計する。
# reason ラベルにより jwt_decode_error / missing_cookie / user_not_found 等を
# Cloud Monitoring 側で分解できる。
# --------------------------------------------------
resource "google_logging_metric" "auth_failed" {
  project = var.project_id
  name    = "devforge/auth_failed"
  filter  = <<-EOT
    resource.type="cloud_run_revision"
    severity="WARNING"
    jsonPayload.message="auth_failed"
  EOT

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    labels {
      key         = "reason"
      value_type  = "STRING"
      description = "認証失敗の理由（jwt_decode_error / missing_cookie / user_not_found 等）"
    }
  }
  label_extractors = {
    "reason" = "EXTRACT(jsonPayload.reason)"
  }
}

# --------------------------------------------------
# アラートポリシー: 認証失敗の急増
# 1 万リクエスト級のブルートフォース攻撃検知用。
# 5 分間に 1,000 件超で発火（= 平均 200/min 持続）。
# --------------------------------------------------
resource "google_monitoring_alert_policy" "auth_failed_alert" {
  project      = var.project_id
  display_name = "DevForge Auth Failed Surge"
  combiner     = "OR"

  conditions {
    display_name = "auth_failed > 1000 / 5min"
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/devforge/auth_failed\" AND resource.type=\"cloud_run_revision\""
      comparison      = "COMPARISON_GT"
      threshold_value = 1000
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
      認証失敗（auth_failed）が 5 分間に 1,000 件を超えました。
      ブルートフォース攻撃の可能性があります。

      初動:
      1. Cloud Logging で `jsonPayload.message="auth_failed"` をフィルタ
      2. `jsonPayload.client_ip` でグルーピングし攻撃元 IP を特定
      3. `jsonPayload.path` / `jsonPayload.reason` から狙われている経路を特定
      4. 必要なら Cloud Run の ingress 制限・GCP Armor で IP ブロック

      runbook: docs/runbooks/alert-policies.md
    EOT
    mime_type = "text/markdown"
  }

  notification_channels = [google_monitoring_notification_channel.email.name]
}

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
