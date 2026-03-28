terraform {
  required_version = "~> 1.8"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.22"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 7.22"
    }
  }
}
