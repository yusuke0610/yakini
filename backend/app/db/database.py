# PostgreSQL 移行時の手順:
# 1. DATABASE_URL を postgresql+psycopg2://... に変更
# 2. _connect_args() は sqlite 以外で空 dict を返すため変更不要
# 3. PRAGMA イベントリスナーは sqlite チェックで自動スキップ
# 4. pip install psycopg2-binary を requirements に追加
# 5. Alembic で新規マイグレーション生成・適用

from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from ..core.settings import get_database_url

DATABASE_URL = get_database_url()


def _connect_args(url: str) -> dict:
    """SQLite のみ check_same_thread=False が必要。"""
    if url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


engine = create_engine(
    DATABASE_URL,
    connect_args=_connect_args(DATABASE_URL),
    pool_pre_ping=True,
)

# SQLite 限定: WAL モードと busy_timeout を有効化
if DATABASE_URL.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        """WAL モードと busy_timeout を有効化し、バックグラウンドタスクとの同時アクセスに対応する。"""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
