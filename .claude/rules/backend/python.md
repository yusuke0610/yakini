---
paths:
  - backend/**
---

# Python コーディング規約

- flake8 に準拠すること（設定: `backend/setup.cfg`）
- PEP8を守るな、PEP8を理解した上で抽象化しろ
- コード変更後は `cd backend && .venv/bin/python -m flake8` を実行し、違反がないことを確認すること
- 未使用の import を残さないこと（F401）

## システムパッケージと Dockerfile

- Pythonライブラリがシステムパッケージ（C ライブラリ等）に依存する場合、`backend/Dockerfile` の `apt-get install` にも該当パッケージを追加すること
- ローカルで `brew install` 等を行った場合は、必ず Dockerfile 側にも対応する Debian パッケージを追加し、Cloud Run デプロイに影響がないことを確認すること
