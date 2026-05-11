output "pages_subdomain" {
  description = "Cloudflare Pages のデフォルトサブドメイン（{project_name}.pages.dev）。"
  value       = cloudflare_pages_project.app.subdomain
}

output "pages_project_name" {
  description = "Cloudflare Pages プロジェクト名。"
  value       = cloudflare_pages_project.app.name
}
