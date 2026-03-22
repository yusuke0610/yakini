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


def get_sqlite_db_path() -> Path:
    db_path = os.getenv("SQLITE_DB_PATH", "./local.sqlite").strip()
    return Path(db_path)


def get_database_url() -> str:
    db_path = get_sqlite_db_path()
    return f"sqlite:///{db_path}"


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


def get_secret_key() -> str:
    key = os.getenv("SECRET_KEY", "").strip()
    if not key:
        raise RuntimeError("SECRET_KEY is not configured")
    return key


def get_github_client_id() -> str:
    return os.getenv("GITHUB_CLIENT_ID", "").strip()


def get_github_client_secret() -> str:
    return os.getenv("GITHUB_CLIENT_SECRET", "").strip()


def get_llm_provider() -> str:
    return os.environ.get("LLM_PROVIDER", "ollama")


def get_vertex_project_id() -> str:
    return os.environ.get("VERTEX_PROJECT_ID", "")


def get_vertex_location() -> str:
    return os.environ.get("VERTEX_LOCATION", "asia-northeast1")
