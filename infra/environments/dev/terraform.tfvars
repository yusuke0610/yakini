project_id          = "devforge-dev-20260311"
app_name            = "devforge"
template_version    = "v0.1.0"
cors_origins        = "https://storage.googleapis.com"
enable_github_oauth = true
terraform -chdir=infra/environments/dev plan
terraform -chdir=infra/environments/dev apply
