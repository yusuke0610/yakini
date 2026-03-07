terraform {
  required_version = "~> 1.8"

  backend "gcs" {
    bucket = "yakini-tfstate-dev"
    prefix = "terraform/state"
  }
}
