module "resume_stack" {
  source = "../../modules/resume_stack"

  project_id       = var.project_id
  app_name         = var.app_name
  environment      = "stg"
  template_version = var.template_version
  cors_origins     = var.cors_origins
}

output "stack_name" {
  value = module.resume_stack.stack_name
}

output "template_version" {
  value = module.resume_stack.template_version
}
