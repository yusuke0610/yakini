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
  description = "OAuth callback の base URL（例: https://app.devforge.app）。GitHub OAuth の redirect_uri を固定する。"
  type        = string
  default     = ""
}

variable "cloudflare_api_token" {
  description = "Cloudflare API トークン。GitHub Secret → TF_VAR_cloudflare_api_token で注入する。"
  type        = string
  sensitive   = true
  default     = ""
}

variable "cloudflare_account_id" {
  description = "Cloudflare アカウント ID。GitHub Secret → TF_VAR_cloudflare_account_id で注入する。"
  type        = string
  sensitive   = true
  default     = ""
}

variable "cloudflare_zone_id" {
  description = "Cloudflare DNS ゾーン ID（devforge.app ドメイン）。GitHub Secret → TF_VAR_cloudflare_zone_id で注入する。"
  type        = string
  sensitive   = true
  default     = ""
}

variable "cloudflare_pages_project_name" {
  description = "Cloudflare Pages プロジェクト名（例: devforge）。"
  type        = string
  default     = "devforge"
}

variable "cloudflare_subdomain" {
  description = "Cloudflare DNS レコード名（例: app）。app.devforge.app となる。"
  type        = string
  default     = "app"
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
