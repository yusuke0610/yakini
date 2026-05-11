resource "google_artifact_registry_repository" "app" {
  project       = var.project_id
  location      = var.region
  repository_id = var.stack_name
  format        = "DOCKER"

  # 古いイメージの蓄積による GCP コスト削減のためクリーンアップポリシーを設定する。
  # dry_run = false で実際の削除が有効になっている。
  # 変更時は一時的に true に戻して terraform plan で影響範囲を確認すること。
  cleanup_policy_dry_run = false

  # 最新 3 件のタグ付きイメージを保持する
  cleanup_policies {
    id     = "keep-latest-3"
    action = "KEEP"
    most_recent_versions {
      keep_count = 3
    }
  }

  # タグなし（untagged）かつ 1 日以上経過したイメージを削除する
  cleanup_policies {
    id     = "delete-old-untagged"
    action = "DELETE"
    condition {
      tag_state  = "UNTAGGED"
      older_than = "86400s"
    }
  }
}
