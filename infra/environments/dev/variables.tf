variable "project_id" {
  description = "GCP project ID."
  type        = string
}

variable "app_name" {
  description = "Application name prefix."
  type        = string
}

variable "deployer_service_account_email" {
  description = "Optional deployer service account email that needs actAs on the runtime service account."
  type        = string
  default     = ""
}

variable "template_version" {
  description = "Infrastructure template version."
  type        = string
}

variable "cors_origins" {
  description = "Allowed CORS origins for the API."
  type        = string
}

variable "callback_base_url" {
  description = "OAuth callback の base URL（Firebase Hosting の URL）。"
  type        = string
  default     = ""
}

variable "enable_github_oauth" {
  description = "Whether to inject GitHub OAuth secrets into Cloud Run."
  type        = bool
  default     = false
}

variable "alert_email" {
  description = "監視アラート通知先メールアドレス。GitHub Secret → TF_VAR_alert_email で注入する。"
  type        = string
  sensitive   = true
}

variable "upstash_redis_url" {
  description = "Upstash Redis 接続 URL。GitHub Secret → TF_VAR_upstash_redis_url で注入する。"
  type        = string
  default     = ""
}

variable "upstash_redis_token" {
  description = "Upstash Redis 認証トークン。GitHub Secret → TF_VAR_upstash_redis_token で注入する。"
  type        = string
  sensitive   = true
  default     = ""
}
