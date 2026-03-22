---
paths:
  - backend/**
---

# Backend アーキテクチャ (FastAPI)

```
backend/app/
├── main.py              # FastAPI アプリ（lifespan で DB bootstrap）
├── routers/             # エンドポイント（auth, basic_info, resumes, rirekisho, blog, intelligence, admin, health, master_data）
├── models.py            # SQLAlchemy 2.0 宣言的マッピング
├── schemas.py           # Pydantic リクエスト/レスポンススキーマ
├── repositories.py      # データアクセス層（UserRepository 等）
├── database.py          # DB接続設定
├── auth.py              # JWT + bcrypt + Cookie認証
├── encryption.py        # Fernet フィールド暗号化
├── services/
│   └── intelligence/
│       ├── pipeline.py          # GitHub 分析パイプライン（オーケストレーター）
│       ├── github_collector.py  # GitHub API からリポジトリ取得
│       ├── skill_extractor.py   # 言語/トピックからスキル抽出
│       ├── blog_collector.py    # Zenn/note 記事収集
│       ├── llm_summarizer.py    # LLM による AI 要約
│       ├── llm/
│       │   ├── base.py          # LLMClient 抽象基底クラス（generate, check_available）
│       │   ├── factory.py       # LLM_PROVIDER 環境変数でクライアント切替
│       │   ├── ollama_client.py # ローカル LLM
│       │   └── vertex_client.py # google-genai SDK（Vertex AI）
│       ├── pdf/                 # WeasyPrint による PDF 生成
│       └── markdown/            # Markdown テンプレート生成
├── bootstrap.py         # 起動時 GCS → SQLite 復元
└── backup.py            # SQLite → GCS バックアップ
```
