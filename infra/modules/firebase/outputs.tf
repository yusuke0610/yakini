output "site_id" {
  description = "Firebase Hosting サイト ID。"
  value       = google_firebase_hosting_site.default.site_id
}

output "default_url" {
  description = "Firebase Hosting のデフォルト URL。"
  value       = google_firebase_hosting_site.default.default_url
}
