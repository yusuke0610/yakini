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
