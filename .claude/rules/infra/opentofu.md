---
paths:
  - infra/**
---

# Infrastructure (OpenTofu)

```
infra/
├── modules/             # cloud_run, artifact_registry, cloud_tasks, cloudflare, monitoring, service_account
└── environments/        # dev, stg, prod（各環境で tfvars 管理）
```

CLI: OpenTofu (`tofu`) を使用する。Nix で管理されており `nix develop` シェル内で利用可能。`.tf` の構文は Terraform と同一。
デプロイ: GitHub Actions で `dev` ブランチ push 時に frontend → Cloudflare Pages、backend → Docker → Artifact Registry → Cloud Run。

DB は Turso (libSQL) を使用。Terraform 対象外で `turso CLI` 手動管理。詳細は `docs/data-model.md` の「Turso CLI セットアップ」参照。
