variable "project_id" {
  description = "GCP project ID."
  type        = string
}

variable "region" {
  description = "GCP region."
  type        = string
}

variable "stack_name" {
  description = "Stack name ({app_name}-{environment})."
  type        = string
}

variable "service_account_email" {
  description = "Cloud Run runtime service account email."
  type        = string
}

variable "enable_github_oauth" {
  description = "Whether to inject GitHub OAuth secrets into Cloud Run."
  type        = bool
  default     = false
}

variable "db_backup_bucket_name" {
  description = "GCS bucket name for database backups."
  type        = string
}

variable "cors_origins" {
  description = "Allowed CORS origins for the API."
  type        = string
}

variable "callback_base_url" {
  description = "OAuth callback の base URL（例: https://devforge-dev-20260311.web.app）。Firebase Hosting 経由の redirect_uri を固定するために使用する。未設定の場合は build_external_base_url にフォールバック。"
  type        = string
  default     = ""
}

variable "task_runner" {
  description = "バックグラウンドタスク実行方式 (local / cloud_tasks)。"
  type        = string
  default     = "cloud_tasks"
}

variable "cloud_tasks_queue" {
  description = "Cloud Tasks キュー名。"
  type        = string
  default     = ""
}

variable "cloud_tasks_location" {
  description = "Cloud Tasks キューのロケーション。"
  type        = string
  default     = "asia-northeast1"
}

variable "cloud_tasks_service_account" {
  description = "Cloud Tasks OIDC 認証用サービスアカウントメール。"
  type        = string
  default     = ""
}

variable "cloud_tasks_service_url" {
  description = "Cloud Tasks からコールバックする Cloud Run サービス URL。初回 apply 後に設定する。"
  type        = string
  default     = ""
}

variable "environment" {
  description = "実行環境 (dev / stg / prod)。構造化ログの形式制御に使用。"
  type        = string
  default     = "dev"
}

variable "upstash_redis_url" {
  description = "Upstash Redis 接続 URL（rediss://host:port 形式）。未設定の場合は進捗機能を無効化。"
  type        = string
  default     = ""
}

variable "upstash_redis_token" {
  description = "Upstash Redis 認証トークン。"
  type        = string
  sensitive   = true
  default     = ""
}
