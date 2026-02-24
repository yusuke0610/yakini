from .services.sqlite_backup import backup_sqlite_to_gcs


def main() -> None:
    backup_sqlite_to_gcs()


if __name__ == "__main__":
    main()
