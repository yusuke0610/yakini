# Resume Builder

職務経歴をUIから入力し、PostgreSQLに保存してPDF出力できるアプリです。

## 構成
- `frontend`: TypeScript + React (Vite)
- `backend`: Python + FastAPI + SQLAlchemy
- `db`: PostgreSQL (Docker Compose)

## 1. PostgreSQL起動

```bash
docker compose up -d
```

## 2. バックエンド起動

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 3. フロントエンド起動

別ターミナルで:

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

ブラウザで `http://localhost:5173` を開きます。

## API概要
- `POST /api/resumes`: 職務経歴を作成
- `PUT /api/resumes/{id}`: 職務経歴を更新
- `GET /api/resumes/{id}`: 職務経歴を取得
- `GET /api/resumes/{id}/pdf`: PDFをダウンロード
- `GET /health`: ヘルスチェック

## メモ
- DBテーブルはFastAPI起動時に自動作成されます。
- CORS許可元は `backend/.env` の `CORS_ORIGINS` で調整できます。
