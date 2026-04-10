output "queue_id" {
  description = "Cloud Tasks キューの ID"
  value       = google_cloud_tasks_queue.ai_tasks.id
}

output "queue_name" {
  description = "Cloud Tasks キュー名"
  value       = google_cloud_tasks_queue.ai_tasks.name
}
