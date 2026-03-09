module "resume_stack" {
  source = "../../modules/resume_stack"

  project_id       = var.project_id
  app_name         = var.app_name
  environment      = "dev"
  template_version = var.template_version
}

output "stack_name" {
  value = module.resume_stack.stack_name
}

output "template_version" {
  value = module.resume_stack.template_version
}

output "frontend_url" {
  value = module.resume_stack.frontend_url
}
