---
paths:
  - backend/**
---

# Backend アーキテクチャ (FastAPI)

```
backend/app/
├── main.py              # FastAPI アプリ（lifespan で DB bootstrap）
├── core/                # 設定・メッセージ・認証・暗号化などの横断基盤
│   ├── settings.py
│   ├── messages.py
│   ├── logging_utils.py
│   ├── date_utils.py
│   ├── encryption.py
│   └── security/
│       ├── auth.py
│       ├── csrf.py
│       └── dependencies.py
├── db/                  # DB接続・bootstrap・backup・seed・migration 補助
│   ├── database.py
│   ├── bootstrap.py
│   ├── backup.py
│   ├── migrations.py
│   ├── seed.py
│   └── sqlite_backup.py
├── routers/             # エンドポイント（auth, basic_info, resumes, rirekisho, blog, intelligence, admin, health, master_data）
├── models/              # SQLAlchemy 2.0 宣言的マッピング
├── schemas/             # Pydantic リクエスト/レスポンススキーマ
├── repositories/        # データアクセス層（UserRepository 等）
├── services/
│   ├── blog/                    # ブログ収集・技術記事判定・スコア算出
│   │   ├── collector.py
│   │   ├── scorer.py
│   │   └── tech_keywords.json
│   ├── intelligence/           # GitHub 分析パイプラインと LLM 連携
│   │   ├── pipeline.py
│   │   ├── github_collector.py
│   │   ├── llm_summarizer.py
│   │   ├── response_mapper.py
│   │   ├── position_scorer.py
│   │   ├── skill_*.py
│   │   └── llm/
│   │       ├── base.py
│   │       ├── factory.py
│   │       ├── ollama_client.py
│   │       └── vertex_client.py
│   ├── markdown/                # Markdown テンプレート生成
│   ├── pdf/                     # WeasyPrint による PDF 生成
│   └── shared/                  # ドメイン横断の service util
│       └── sort_utils.py
```
