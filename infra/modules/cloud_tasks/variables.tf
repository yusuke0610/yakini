variable "project_id" {
  description = "GCP プロジェクト ID"
  type        = string
}

variable "location" {
  description = "Cloud Tasks キューのロケーション"
  type        = string
  default     = "asia-northeast1"
}

variable "queue_name" {
  description = "Cloud Tasks キュー名"
  type        = string
  default     = "devforge-ai-tasks"
}
