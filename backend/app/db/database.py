from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

from ..core.settings import build_sqlalchemy_database_url

# Turso (libSQL) 接続 URL を構築する。`TURSO_DATABASE_URL` を `sqlite+libsql://` 形式に変換する
_db_url = build_sqlalchemy_database_url()

# libSQL は HTTP/HTTPS 経由のため SQLAlchemy のコネクションプールは保持せず NullPool を使う
# `check_same_thread` は SQLite ドライバ固有の引数で libSQL では不要
engine = create_engine(
    _db_url,
    poolclass=NullPool,
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
