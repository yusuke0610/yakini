---
paths:
  - infra/**
---

# Infrastructure (OpenTofu)

```
infra/
├── modules/             # cloud_run, storage, artifact_registry, service_account
└── environments/        # dev, stg, prod（各環境で tfvars 管理）
```

CLI: OpenTofu (`tofu`) を使用する。Nix で管理されており `nix develop` シェル内で利用可能。`.tf` の構文は Terraform と同一。
デプロイ: GitHub Actions で `dev` ブランチ push 時に frontend → GCS、backend → Docker → Artifact Registry → Cloud Run。
