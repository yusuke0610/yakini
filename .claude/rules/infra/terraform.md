---
paths:
  - infra/**
---

# Infrastructure (Terraform)

```
infra/
├── modules/             # cloud_run, storage, artifact_registry, service_account
└── environments/        # dev, stg, prod（各環境で tfvars 管理）
```

デプロイ: GitHub Actions で `dev` ブランチ push 時に frontend → GCS、backend → Docker → Artifact Registry → Cloud Run。
