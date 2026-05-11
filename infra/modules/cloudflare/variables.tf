variable "cloudflare_account_id" {
  description = "Cloudflare アカウント ID。"
  type        = string
  sensitive   = true
}

variable "cloudflare_zone_id" {
  description = "Cloudflare DNS ゾーン ID（devforge.app ドメインのゾーン）。"
  type        = string
  sensitive   = true
}

variable "project_name" {
  description = "Cloudflare Pages プロジェクト名（例: devforge, devforge-dev）。*.pages.dev のサブドメインになる。"
  type        = string
}

variable "subdomain" {
  description = "DNS レコード名（例: app, app-dev）。zone と組み合わせて app.devforge.app のようなカスタムドメインを作成する。"
  type        = string
  default     = "app"
}

variable "production_branch" {
  description = "Cloudflare Pages の本番ブランチ名。"
  type        = string
  default     = "main"
}
