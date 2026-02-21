output "stack_name" {
  description = "Computed stack name."
  value       = local.stack_name
}

output "environment" {
  description = "Environment that this module represents."
  value       = var.environment
}

output "template_version" {
  description = "Infrastructure template version."
  value       = var.template_version
}
