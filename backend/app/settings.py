import os
from pathlib import Path


def get_sqlite_db_path() -> Path:
    db_path = os.getenv("SQLITE_DB_PATH", "./local.sqlite").strip()
    return Path(db_path)


def get_database_url() -> str:
    db_path = get_sqlite_db_path()
    return f"sqlite:///{db_path}"


def get_cors_origins() -> list[str]:
    cors_origins = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173"
    )
    return [
        origin.strip()
        for origin in cors_origins.split(",")
        if origin.strip()
    ]


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
