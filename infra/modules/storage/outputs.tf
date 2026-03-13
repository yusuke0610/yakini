output "db_backup_bucket_name" {
  description = "Database backup bucket name."
  value       = google_storage_bucket.db_backup.name
}

output "frontend_bucket_name" {
  description = "Frontend hosting bucket name."
  value       = google_storage_bucket.frontend.name
}

output "frontend_url" {
  description = "Frontend static site URL."
  value       = "https://storage.googleapis.com/${google_storage_bucket.frontend.name}/index.html"
}
