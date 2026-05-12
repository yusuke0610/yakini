from pathlib import Path

from ..core.settings import get_sqlite_db_path


def _alembic_config():
    from alembic.config import Config

    backend_root = Path(__file__).resolve().parents[2]
    alembic_ini = backend_root / "alembic.ini"
    script_location = backend_root / "alembic_migrations"

    config = Config(str(alembic_ini))
    config.set_main_option("script_location", str(script_location))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{get_sqlite_db_path()}")
    return config


def run_migrations() -> None:
    from alembic import command

    command.upgrade(_alembic_config(), "head")
