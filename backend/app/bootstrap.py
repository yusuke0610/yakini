import logging

from .logging_utils import log_event
from .migrations import run_migrations
from .services.sqlite_backup import restore_sqlite_from_gcs_if_configured


def _seed_initial_user() -> None:
    from .auth import hash_password
    from .database import SessionLocal
    from .repositories import UserRepository
    from .settings import get_initial_password, get_initial_username

    username = get_initial_username()
    password = get_initial_password()

    if not username or not password:
        log_event(
            logging.WARNING,
            "initial_user_seed_skipped",
            reason="INITIAL_USERNAME or INITIAL_PASSWORD not set",
        )
        return

    db = SessionLocal()
    try:
        repo = UserRepository(db)
        if repo.count() == 0:
            repo.create(username, hash_password(password))
            log_event(
                logging.INFO,
                "initial_user_created",
                username=username,
            )
        else:
            log_event(
                logging.INFO,
                "initial_user_seed_skipped",
                reason="users table not empty",
            )
    finally:
        db.close()


def bootstrap() -> None:
    restored = restore_sqlite_from_gcs_if_configured()
    log_event(
        logging.INFO,
        "sqlite_bootstrap_restore_result",
        restored=restored,
    )
    run_migrations()
    log_event(logging.INFO, "sqlite_bootstrap_migration_succeeded")
    _seed_initial_user()


if __name__ == "__main__":
    bootstrap()
