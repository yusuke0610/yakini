---
paths:
  - backend/**
---

# 認証・暗号化・セキュリティ

## 認証

- JWT（`python-jose`）+ bcrypt（`passlib`）、Cookie に 8 時間有効のトークンを格納
- **`bcrypt==3.2.2` に固定**（passlib 1.7.4 は bcrypt 4.x と非互換）
- GitHub OAuth ログインに対応（`GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` の設定が必要）
- GitHub OAuth の `state` は **backend 側 Cookie で検証**する。frontend だけで検証しないこと
- 認証Cookie属性は `COOKIE_SECURE` / `COOKIE_SAMESITE` で制御する

## 暗号化

- 履歴書（Rirekisho）の個人情報フィールド（email / phone / postal_code / address）は `encryption.py` で暗号化保存
- `FIELD_ENCRYPTION_KEY` 環境変数（Fernet）

## セキュリティ

- 外部API呼び出しや LLM 実行のような**高コスト endpoint**には rate limit を付けること（slowapi）
- OAuth 開始URLは backend で発行し、許可された `CORS_ORIGINS` のみをリダイレクト先に使うこと
- cookie 認証を使う変更では `Secure` / `SameSite` / CORS の整合を必ず確認すること
