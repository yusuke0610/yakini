from logging.config import fileConfig

from alembic import context

# モデルのメタデータを登録するため import が必要
from app import models  # noqa: F401
from app.core.settings import build_sqlalchemy_database_url
from app.db import Base
from sqlalchemy import create_engine, pool

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """オフラインモード（DB 接続なし）でマイグレーションを実行する。"""
    url = build_sqlalchemy_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """オンラインモードで TURSO_DATABASE_URL を使って Turso (libSQL) に接続する。

    HTTP/HTTPS 経由の libSQL ではコネクションを保持しないため NullPool を使う。
    """
    connectable = create_engine(build_sqlalchemy_database_url(), poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
