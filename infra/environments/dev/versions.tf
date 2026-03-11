terraform {
  required_version = "~> 1.8"

  backend "gcs" {
    bucket = "devforge-tfstate-dev"
    prefix = "terraform/state"
  }
}
