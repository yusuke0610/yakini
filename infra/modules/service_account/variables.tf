variable "project_id" {
  description = "GCP project ID."
  type        = string
}

variable "stack_name" {
  description = "Stack name ({app_name}-{environment})."
  type        = string
}

variable "deployer_service_account_email" {
  description = "Optional deployer service account email that needs actAs on the runtime service account."
  type        = string
  default     = ""
}
