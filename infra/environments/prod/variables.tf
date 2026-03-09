variable "project_id" {
  description = "GCP project ID."
  type        = string
}

variable "app_name" {
  description = "Application name prefix."
  type        = string
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
