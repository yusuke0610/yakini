---
paths:
  - backend/**
---

# DB設計ルール

- `basic_info` / `resumes` / `rirekisho` は **1ユーザー1件** を前提にし、`user_id` を一意制約で縛ること
- 可変長データを JSON カラムへ増やさないこと。資格・学歴・職歴・職務経歴の明細・ブログタグは子テーブルへ正規化すること
- 日付は可能な限り DB の `DATE` / `TIMESTAMP` を使うこと
- `blog_articles` は `account_id` 起点で管理し、`user_id` や `platform` を冗長保持しないこと
- マイグレーション: Alembic（`backend/alembic_migrations/versions/`）。SQLite は ALTER COLUMN 非対応のため `batch_alter_table` を使うこと

## SQLite + Cloud Run + GCS 方式

- Cloud Run は `/tmp/devforge.sqlite` を使用（`SQLITE_DB_PATH` 環境変数）
- **起動時**: `bootstrap.py` が GCS から SQLite を復元（なければ空DBで起動）
- **多重起動防止**: `max_instances = 1` で SQLite の競合を回避
- **バックアップ方式**: tmp オブジェクト → `blob.rewrite()` → tmp削除（アトミック置き換え）
- **ローカルDB**: `backend/local.sqlite` は開発用の生成物であり、Git に含めないこと

## バックアップ失敗時の方針

- 明示実行された `POST /admin/backup` / `python -m app.backup` は失敗時にエラーを返す
- 通常の CRUD では自動バックアップしない
- 起動時の復元失敗は `WARNING` ログを出し、空DBで継続する
