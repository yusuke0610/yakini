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
  default     = "https://storage.googleapis.com"
}

variable "container_image_tag" {
  description = "Container image tag used when Terraform creates Cloud Run."
  type        = string
  default     = "latest"
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
