---
paths:
  - infra/**
---

# Infrastructure (Terraform)

```
infra/
├── modules/             # cloud_run, artifact_registry, cloud_tasks, cloudflare, monitoring, service_account
└── environments/        # dev, stg, prod（各環境で tfvars 管理）
```

デプロイ: GitHub Actions で `dev` ブランチ push 時に frontend → Cloudflare Pages、backend → Docker → Artifact Registry → Cloud Run。

DB は Turso (libSQL) を使用。Terraform 対象外で `turso CLI` 手動管理。詳細は `infra/README.md` の「Turso のセットアップ」参照。
