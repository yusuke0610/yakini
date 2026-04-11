terraform {
  backend "gcs" {
    bucket = "devforge-tfstate-stg"
    prefix = "terraform/state"
  }
}
