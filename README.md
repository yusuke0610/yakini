# Resume Builder

基本情報・職務経歴書・履歴書をUIから入力し、PostgreSQLに保存してPDF出力できるアプリです。

## 入力項目
### 基本情報
- 氏名
- 記載日
- 資格（取得日 + 名称、複数追加/削除）

### 職務経歴書
- 自己PR
- 職務経歴（開始、在職の有無: 離職/在職、離職年月、会社名、職種、業務内容、実績、従業員数、資本金）
- 技術スタック（言語、OS、DB、クラウドリソース、開発支援ツールを複数追加/削除）

### 履歴書
- 郵便番号
- 都道府県
- 住所（フリー入力）
- メールアドレス
- 電話番号
- 学歴（複数追加/削除）
- 職歴（複数追加/削除）
- 志望動機

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
### 基本情報
- `POST /api/basic-info`: 作成
- `PUT /api/basic-info/{id}`: 更新
- `GET /api/basic-info/latest`: 最新データ取得

### 職務経歴書
- `POST /api/resumes`: 作成
- `PUT /api/resumes/{id}`: 更新
- `GET /api/resumes/{id}`: 取得
- `GET /api/resumes/{id}/pdf`: PDFダウンロード

### 履歴書
- `POST /api/rirekisho`: 作成
- `PUT /api/rirekisho/{id}`: 更新
- `GET /api/rirekisho/{id}`: 取得
- `GET /api/rirekisho/{id}/pdf`: PDFダウンロード

### その他
- `GET /health`: ヘルスチェック

## メモ
- DBテーブルはFastAPI起動時に自動作成されます。
- CORS許可元は `backend/.env` の `CORS_ORIGINS` で調整できます。
- 旧スキーマのテーブルがある場合は `docker compose down -v` でボリュームを削除して再作成してください。
