output "db_backup_bucket_name" {
  description = "Database backup bucket name."
  value       = google_storage_bucket.db_backup.name
}
