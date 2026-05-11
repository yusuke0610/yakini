.PHONY: help \
	setup install-hooks install-backend install-frontend generate-keys \
	dev dev-build dev-down dev-frontend preview-frontend \
	test test-backend test-frontend \
	lint lint-backend lint-frontend lint-fix \
	format format-check \
	ci \
	build-frontend build-backend deploy-frontend \
	gen-redirects \
	migrate migrate-create \
	clean

# デフォルトターゲット: ヘルプ表示
help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "セットアップ"
	@echo "  setup             初回セットアップ (hooks + backend + frontend)"
	@echo "  install-hooks     git hooks を設定"
	@echo "  install-backend   Backend 依存パッケージをインストール"
	@echo "  install-frontend  Frontend 依存パッケージをインストール"
	@echo "  generate-keys     JWT RSA 鍵ペアを生成"
	@echo ""
	@echo "ローカル開発"
	@echo "  dev               docker-compose で API + Ollama を起動"
	@echo "  dev-build         再ビルドして起動"
	@echo "  dev-down          docker-compose を停止"
	@echo "  dev-frontend      Frontend 開発サーバーを起動 (Vite / localhost:5173)"
	@echo "  preview-frontend  ビルド済みを wrangler でローカル提供 (HMR なし / localhost:8788)"
	@echo ""
	@echo "テスト・リント"
	@echo "  ci                lint + test + build-frontend を一括実行 (CI 相当)"
	@echo "  test              全テスト (backend + frontend)"
	@echo "  test-backend      Backend: pytest"
	@echo "  test-frontend     Frontend: vitest"
	@echo "  lint              全リント (backend + frontend)"
	@echo "  lint-backend      Backend: ruff check"
	@echo "  lint-frontend     Frontend: eslint"
	@echo "  lint-fix          リント自動修正 (ruff + eslint)"
	@echo "  format            Prettier で整形"
	@echo "  format-check      Prettier チェック"
	@echo ""
	@echo "ビルド"
	@echo "  build-frontend    Vite ビルド"
	@echo "  build-backend     Docker イメージビルド"
	@echo "  deploy-frontend   Cloudflare Pages へビルド＆デプロイ (CLOUD_RUN_URL=... 指定可)"
	@echo "  gen-redirects     Cloudflare Pages 用 _redirects を生成 (CLOUD_RUN_URL=... 指定可)"
	@echo ""
	@echo "マイグレーション"
	@echo "  migrate           alembic upgrade head"
	@echo "  migrate-create    マイグレーション生成 (例: make migrate-create MSG=\"add user table\")"
	@echo ""
	@echo "クリーンアップ"
	@echo "  clean             docker-compose 停止 + キャッシュ削除"

# ------------------------------------------------------------------ #
# セットアップ
# ------------------------------------------------------------------ #

setup: install-hooks install-backend install-frontend

install-hooks:
	./scripts/setup-git-hooks.sh

install-backend:
	nix develop --command bash -c "cd backend && (.venv/bin/python --version > /dev/null 2>&1 || (rm -rf .venv && uv venv)) && uv pip install --python .venv/bin/python -r requirements.txt"

install-frontend:
	nix develop --command bash -c "cd frontend && npm ci"

generate-keys:
	nix develop --command bash -c "cd backend && python scripts/generate_keys.py"

# ------------------------------------------------------------------ #
# ローカル開発
# ------------------------------------------------------------------ #

dev:
	docker compose up

dev-build:
	docker compose up --build

dev-down:
	docker compose down

dev-frontend:
	nix develop --command bash -c "cd frontend && npm run dev"

preview-frontend:
	nix develop --command bash -c "cd frontend && CLOUD_RUN_URL='http://localhost:8000' npm run build && npx wrangler pages dev dist --port 8788"

# ------------------------------------------------------------------ #
# テスト・リント
# ------------------------------------------------------------------ #

ci: lint test build-frontend

test: test-backend test-frontend

test-backend:
	nix develop --command bash -c "cd backend && .venv/bin/python -m pytest -q tests"

test-frontend:
	nix develop --command bash -c "cd frontend && npm test"

lint: lint-backend lint-frontend

lint-backend:
	nix develop --command bash -c "cd backend && .venv/bin/python -m ruff check app tests alembic_migrations"

lint-frontend:
	nix develop --command bash -c "cd frontend && npm run lint"

lint-fix:
	nix develop --command bash -c "cd backend && .venv/bin/python -m ruff check --fix app tests alembic_migrations"
	cd frontend && npm run lint:fix

format:
	cd frontend && npm run format

format-check:
	cd frontend && npm run format:check

# ------------------------------------------------------------------ #
# ビルド
# ------------------------------------------------------------------ #

build-frontend:
	cd frontend && npm run build

build-backend:
	docker build ./backend -t devforge-api

deploy-frontend:
	nix develop --command bash -c "cd frontend && CLOUD_RUN_URL='$(CLOUD_RUN_URL)' npm run build && npm run deploy"

gen-redirects:
	nix develop --command bash -c "cd frontend && CLOUD_RUN_URL='$(CLOUD_RUN_URL)' node scripts/gen-redirects.mjs"

# ------------------------------------------------------------------ #
# マイグレーション
# ------------------------------------------------------------------ #

migrate:
	cd backend && .venv/bin/alembic upgrade head

migrate-create:
	@if [ -z "$(MSG)" ]; then echo "エラー: MSG を指定してください (例: make migrate-create MSG=\"add user table\")"; exit 1; fi
	cd backend && .venv/bin/alembic revision --autogenerate -m "$(MSG)"

# ------------------------------------------------------------------ #
# クリーンアップ
# ------------------------------------------------------------------ #

clean:
	docker-compose down
	rm -rf backend/.pytest_cache backend/.ruff_cache
	find . -type d -name __pycache__ -not -path "./.venv/*" -not -path "./frontend/node_modules/*" | xargs rm -rf
