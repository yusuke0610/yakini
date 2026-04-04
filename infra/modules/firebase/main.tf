# Firebase プロジェクトの有効化と Hosting サイトの管理

terraform {
  required_providers {
    google-beta = {
      source = "hashicorp/google-beta"
    }
  }
}

resource "google_firebase_project" "default" {
  provider = google-beta
  project  = var.project_id
}

resource "google_firebase_hosting_site" "default" {
  provider = google-beta
  project  = var.project_id
  site_id  = var.project_id

  depends_on = [google_firebase_project.default]
}

# デプロイ用 SA に Firebase Hosting Admin 権限を付与
resource "google_project_iam_member" "deployer_firebase_hosting_admin" {
  count = var.deployer_service_account_email != "" ? 1 : 0

  project = var.project_id
  role    = "roles/firebasehosting.admin"
  member  = "serviceAccount:${var.deployer_service_account_email}"
}

# Firebase CLI がプロジェクトメタデータを読み取るために必要
resource "google_project_iam_member" "deployer_viewer" {
  count = var.deployer_service_account_email != "" ? 1 : 0

  project = var.project_id
  role    = "roles/viewer"
  member  = "serviceAccount:${var.deployer_service_account_email}"
}
