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
  description = "Service account email for bucket IAM bindings."
  type        = string
}
