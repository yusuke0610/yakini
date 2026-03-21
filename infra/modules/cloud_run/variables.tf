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
