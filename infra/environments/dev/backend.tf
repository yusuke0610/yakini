terraform {
  backend "gcs" {
    bucket = "devforge-tfstate-dev"
    prefix = "terraform/state"
  }
}
