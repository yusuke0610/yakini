variable "app_name" {
  description = "Application name prefix for this stack."
  type        = string
}

variable "environment" {
  description = "Environment name (dev/stg/prod)."
  type        = string
}

variable "template_version" {
  description = "Infrastructure template version for change management."
  type        = string
}
