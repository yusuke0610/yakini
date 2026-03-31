from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from ..core.settings import get_database_url

DATABASE_URL = get_database_url()

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
)


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
