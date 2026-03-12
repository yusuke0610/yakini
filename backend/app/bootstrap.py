import logging

from .logging_utils import log_event
from .migrations import run_migrations
from .services.sqlite_backup import restore_sqlite_from_gcs_if_configured


def bootstrap() -> None:
    restored = restore_sqlite_from_gcs_if_configured()
    log_event(
        logging.INFO,
        "sqlite_bootstrap_restore_result",
        restored=restored,
    )
    run_migrations()
    log_event(logging.INFO, "sqlite_bootstrap_migration_succeeded")


if __name__ == "__main__":
    bootstrap()
