output "stack_name" {
  description = "Stack 名（{app_name}-{environment}）。"
  value       = local.stack_name
}

output "artifact_registry_url" {
  description = "Artifact Registry リポジトリ URL（{region}-docker.pkg.dev/{project_id}/{stack_name}）。"
  value       = module.artifact_registry.url
}

output "cloudflare_pages_subdomain" {
  description = "Cloudflare Pages のデフォルトサブドメイン（{project_name}.pages.dev）。"
  value       = module.cloudflare.pages_subdomain
}

output "cloudflare_pages_project_name" {
  description = "Cloudflare Pages プロジェクト名。"
  value       = module.cloudflare.pages_project_name
}

output "service_url" {
  description = "Cloud Run service URL。"
  value       = module.cloud_run.service_url
}
