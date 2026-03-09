output "artifact_registry_url" {
  description = "Artifact Registry repository URL."
  value       = "${google_artifact_registry_repository.app.location}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.app.repository_id}"
}

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

output "frontend_url" {
  description = "Frontend static site URL."
  value       = "https://storage.googleapis.com/${google_storage_bucket.frontend.name}/index.html"
}
