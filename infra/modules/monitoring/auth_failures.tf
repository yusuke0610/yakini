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
