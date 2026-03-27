import logging

from ..core.logging_utils import log_event
from .migrations import run_migrations
from .sqlite_backup import restore_sqlite_from_gcs_if_configured


def bootstrap() -> None:
    restored = restore_sqlite_from_gcs_if_configured()
    log_event(
        logging.INFO,
        "sqlite_bootstrap_restore_result",
        restored=restored,
    )
    run_migrations()
    log_event(logging.INFO, "sqlite_bootstrap_migration_succeeded")

    from .database import SessionLocal
    from .seed import seed_master_data

    db = SessionLocal()
    try:
        seed_master_data(db)
        log_event(logging.INFO, "sqlite_bootstrap_seed_succeeded")
    finally:
        db.close()


if __name__ == "__main__":
    bootstrap()
