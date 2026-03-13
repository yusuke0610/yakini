output "repository_id" {
  description = "Artifact Registry repository ID."
  value       = google_artifact_registry_repository.app.repository_id
}

output "url" {
  description = "Artifact Registry repository URL."
  value       = "${google_artifact_registry_repository.app.location}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.app.repository_id}"
}
