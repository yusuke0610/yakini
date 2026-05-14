from pathlib import Path


def _alembic_config():
    from alembic.config import Config

    backend_root = Path(__file__).resolve().parents[2]
    alembic_ini = backend_root / "alembic.ini"
    script_location = backend_root / "alembic_migrations"

    config = Config(str(alembic_ini))
    config.set_main_option("script_location", str(script_location))
    # 接続 URL は alembic_migrations/env.py が TURSO_DATABASE_URL から動的に構築する
    return config


def run_migrations() -> None:
    from alembic import command

    command.upgrade(_alembic_config(), "head")
