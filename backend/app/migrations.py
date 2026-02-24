from pathlib import Path

from .settings import get_database_url


def _alembic_config():
    from alembic.config import Config

    backend_root = Path(__file__).resolve().parents[1]
    alembic_ini = backend_root / "alembic.ini"
    script_location = backend_root / "alembic_migrations"

    config = Config(str(alembic_ini))
    config.set_main_option("script_location", str(script_location))
    config.set_main_option("sqlalchemy.url", get_database_url())
    return config


def run_migrations() -> None:
    from alembic import command

    command.upgrade(_alembic_config(), "head")
