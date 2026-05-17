variable "project_id" {
  description = "GCP プロジェクト ID"
  type        = string
}

variable "app_name" {
  description = "アプリケーション名 prefix"
  type        = string
}

variable "environment" {
  description = "環境名 suffix"
  type        = string
}

variable "location" {
  description = "Cloud Tasks キューのロケーション"
  type        = string
  default     = "asia-northeast1"
}
