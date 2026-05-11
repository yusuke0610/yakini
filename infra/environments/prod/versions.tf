terraform {
  required_version = "~> 1.8"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.22"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
}
