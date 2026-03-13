terraform {
  backend "gcs" {
    bucket = "devforge-tfstate-prod"
    prefix = "terraform/state"
  }
}
