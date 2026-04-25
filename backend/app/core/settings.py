import os
from pathlib import Path
from urllib.parse import urlparse


def _parse_bool_env(name: str) -> bool | None:
    value = os.getenv(name)
    if value is None:
        return None

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError(f"{name} must be a boolean value")


def _is_loopback_origin(origin: str) -> bool:
    parsed = urlparse(origin)
    return parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1"}


def get_database_url() -> str:
    """DATABASE_URL 環境変数からデータベース接続URLを取得する。

    未設定の場合は SQLITE_DB_PATH から SQLite URL を組み立てる（後方互換）。
    PostgreSQL 移行時は DATABASE_URL を postgresql+psycopg2://... に変更するだけでよい。
    """
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        return url
    # 後方互換: SQLITE_DB_PATH からURLを組み立てる
    db_path = get_sqlite_db_path()
    return f"sqlite:///{db_path}"


def get_sqlite_db_path() -> Path:
    """SQLite ファイルのパスを取得する。GCS バックアップ等の物理パス操作に使用。"""
    db_path = os.getenv("SQLITE_DB_PATH", "./local.sqlite").strip()
    return Path(db_path)


def get_cors_origins() -> list[str]:
    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    return [origin.strip() for origin in cors_origins.split(",") if origin.strip()]


def get_cookie_secure() -> bool:
    configured = _parse_bool_env("COOKIE_SECURE")
    if configured is not None:
        return configured

    origins = get_cors_origins()
    if origins and all(_is_loopback_origin(origin) for origin in origins):
        return False
    return True


def get_cookie_samesite() -> str:
    default = "lax"
    origins = get_cors_origins()
    if origins and not all(_is_loopback_origin(origin) for origin in origins):
        default = "none"

    value = os.getenv("COOKIE_SAMESITE", default).strip().lower()
    if value not in {"lax", "strict", "none"}:
        raise RuntimeError("COOKIE_SAMESITE must be one of: lax, strict, none")
    return value


def get_gcs_bucket_name() -> str:
    return os.getenv("GCS_BUCKET_NAME", "").strip()


def get_gcs_db_object() -> str:
    return os.getenv("GCS_DB_OBJECT", "").strip()


def get_admin_token() -> str:
    return os.getenv("ADMIN_TOKEN", "").strip()


def get_jwt_private_key() -> str:
    """RS256署名用秘密鍵（PEM形式）を取得する。"""
    key = os.getenv("JWT_PRIVATE_KEY", "").replace("\\n", "\n").strip()
    if not key:
        raise RuntimeError("JWT_PRIVATE_KEY is not configured")
    return key


def get_jwt_public_key() -> str:
    """RS256検証用公開鍵（PEM形式）を取得する。"""
    key = os.getenv("JWT_PUBLIC_KEY", "").replace("\\n", "\n").strip()
    if not key:
        raise RuntimeError("JWT_PUBLIC_KEY is not configured")
    return key


def get_github_client_id() -> str:
    return os.getenv("GITHUB_CLIENT_ID", "").strip()


def get_github_client_secret() -> str:
    return os.getenv("GITHUB_CLIENT_SECRET", "").strip()


def get_app_version() -> str:
    """アプリケーションバージョンを取得する（Git タグから CI で注入）。"""
    return os.getenv("APP_VERSION", "dev").strip()


def get_environment() -> str:
    """実行環境を取得する（local / dev / stg / prod）。"""
    return os.getenv("ENVIRONMENT", "local").strip()


def get_llm_provider() -> str:
    return os.environ.get("LLM_PROVIDER", "ollama")


def get_vertex_project_id() -> str:
    return os.environ.get("VERTEX_PROJECT_ID", "")


def get_vertex_location() -> str:
    return os.environ.get("VERTEX_LOCATION", "asia-northeast1")


def get_vertex_model(default: str) -> str:
    """Vertex AI のモデル名を取得する。default は呼び出し元（Vertex クライアント）の既定値を渡す。"""
    return os.environ.get("VERTEX_MODEL", default)


def get_log_format() -> str:
    """ログフォーマット指定（json / text / 空）を小文字で取得する。"""
    return os.getenv("LOG_FORMAT", "").strip().lower()


def get_log_level() -> str:
    """ログレベル名（DEBUG / INFO / WARNING / ERROR / CRITICAL）を大文字で取得する。"""
    return os.getenv("LOG_LEVEL", "INFO").strip().upper()
