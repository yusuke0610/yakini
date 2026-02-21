terraform {
  required_version = "~> 1.8.0"

  cloud {
    organization = "REPLACE_WITH_YOUR_HCP_ORG"

    workspaces {
      name = "yakini-dev"
    }
  }
}
