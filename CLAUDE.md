# DevForge - Claude Code ガイドライン

## コーディング規約

### 共通ルール
- **コメント・ドキュメント**: コード内のコメント、docstring、JSDoc はすべて**日本語**で記述すること。
- **エラーメッセージ**: HTTPException の `detail` 等、ユーザーに返すエラーメッセージはすべて**日本語**で記述すること。

### Python (backend)
- PEP 8 / flake8 に準拠すること
- flake8 の設定は `backend/setup.cfg` に定義済み（max-line-length=120）
- コード変更後は `cd backend && flake8` を実行し、違反がないことを確認すること
- 未使用の import を残さないこと（F401）

### TypeScript/React (frontend)
- ESLint / Prettier の設定に従うこと
- `cd frontend && npm run lint` でリントチェック

## CI 確認ルール

アプリケーションの改修を行った場合、以下のコマンドで CI 相当のチェックをローカルで実行し、パスすることを確認すること:

```bash
# backend
cd backend && flake8 && python -m pytest -q tests

# frontend
cd frontend && npm test && npm run build
```

CI 定義: `.github/workflows/ci.yml`

## アーキテクチャ上の重要な決定事項

### SQLite + Cloud Run + GCS 方式

- Cloud Run は `/tmp/devforge.sqlite` を使用（`SQLITE_DB_PATH` 環境変数）
- **起動時**: `bootstrap.py` が GCS から SQLite を復元（なければ空DBで起動）
- **多重起動防止**: `max_instances = 1` で SQLite の競合を回避
- **バックアップ方式**: tmp オブジェクト → `blob.rewrite()` → tmp削除（アトミック置き換え）

### バックアップ失敗時の方針
- アップロード失敗 → **APIは成功扱い**（データはローカルに保存済）
- ログに `WARNING` を出力して終了、リトライなし
- 次の書き込み時に再バックアップされるため個人利用では許容範囲

### 認証
- JWT（`python-jose`）+ bcrypt（`passlib`）
- **`bcrypt==3.2.2` に固定**（passlib 1.7.4 は bcrypt 4.x と非互換）
- GitHub OAuth ログインに対応（`GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` の設定が必要）

### 暗号化
- 履歴書（Rirekisho）の個人情報フィールド（email / phone / postal_code / address）は `encryption.py` で暗号化保存
- `FIELD_ENCRYPTION_KEY` 環境変数（Fernet）

## 命名規約

| 種別 | 名前 |
|---|---|
| 職務経歴書（career history） | `Resume` / `resumes` テーブル |
| 履歴書（personal CV） | `Rirekisho` / `rirekisho` テーブル |

> `rirekisho` は日本語ローマ字のため cSpell の警告が出るが無視してよい。

## 環境変数（必須）

```
SQLITE_DB_PATH       # Cloud Run: /tmp/devforge.sqlite
SECRET_KEY           # JWT署名キー
FIELD_ENCRYPTION_KEY # Fernet鍵
GCS_BUCKET_NAME      # バックアップ用 GCS バケット名
GCS_DB_OBJECT        # 例: devforge/dev/db.sqlite
ADMIN_TOKEN          # /admin/backup エンドポイント用
CORS_ORIGINS         # 例: https://devforge-dev.example.com
```

### オプション
```
GITHUB_CLIENT_ID     # GitHub OAuth Client ID
GITHUB_CLIENT_SECRET # GitHub OAuth Client Secret
```
