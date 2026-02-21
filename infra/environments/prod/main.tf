module "resume_stack" {
  source = "../../modules/resume_stack"

  app_name         = var.app_name
  environment      = "prod"
  template_version = var.template_version
}

output "stack_name" {
  value = module.resume_stack.stack_name
}

output "template_version" {
  value = module.resume_stack.template_version
}
