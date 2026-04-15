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

variable "artifact_registry_repository_id" {
  description = "Artifact Registry repository ID for container images."
  type        = string
}

variable "container_image_tag" {
  description = "Container image tag used for the initial Cloud Run deployment."
  type        = string
  default     = "latest"
}

variable "bootstrap_image" {
  description = "初回デプロイ用のブートストラップイメージ。空文字の場合は Artifact Registry のイメージを使用する。ignore_changes により CI が上書きしても Terraform は戻さない。"
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello:latest"
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
  default     = "https://storage.googleapis.com"
}

variable "llm_provider" {
  description = "LLM バックエンド (ollama / vertex)。"
  type        = string
  default     = "vertex"
}

variable "vertex_model" {
  description = "Vertex AI で使用するモデル名。"
  type        = string
  default     = "gemini-2.5-flash-lite"
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
