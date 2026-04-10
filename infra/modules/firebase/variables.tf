variable "project_id" {
  description = "GCP project ID."
  type        = string
}

variable "deployer_service_account_email" {
  description = "デプロイ用サービスアカウントのメールアドレス。Firebase Hosting Admin 権限を付与する。"
  type        = string
  default     = ""
}
