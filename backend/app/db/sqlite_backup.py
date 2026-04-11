import logging
import sqlite3
import tempfile
import uuid
from pathlib import Path

from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError

from ..core.logging_utils import log_event
from ..core.settings import get_gcs_bucket_name, get_gcs_db_object, get_sqlite_db_path


def _get_storage_client() -> storage.Client:
    return storage.Client()


def _snapshot_sqlite(source_db_path: Path) -> Path:
    with tempfile.NamedTemporaryFile(
        prefix="devforge-db-", suffix=".sqlite", delete=False
    ) as tmp_file:
        snapshot_path = Path(tmp_file.name)

    with sqlite3.connect(source_db_path) as source_conn:
        with sqlite3.connect(snapshot_path) as dest_conn:
            source_conn.backup(dest_conn)

    return snapshot_path


def restore_sqlite_from_gcs_if_configured() -> bool:
    bucket_name = get_gcs_bucket_name()
    db_object = get_gcs_db_object()
    db_path = get_sqlite_db_path()

    if not bucket_name or not db_object:
        log_event(
            logging.INFO,
            "sqlite_restore_skipped",
            reason="gcs_config_missing",
            sqlite_db_path=str(db_path),
        )
        return False

    db_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        client = _get_storage_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(db_object)

        if not blob.exists(client):
            log_event(
                logging.INFO,
                "sqlite_restore_skipped",
                reason="object_not_found",
                bucket=bucket_name,
                object=db_object,
                sqlite_db_path=str(db_path),
            )
            return False

        blob.download_to_filename(str(db_path))
        log_event(
            logging.INFO,
            "sqlite_restore_succeeded",
            bucket=bucket_name,
            object=db_object,
            sqlite_db_path=str(db_path),
        )
        return True
    except GoogleCloudError as error:
        log_event(
            logging.WARNING,
            "sqlite_restore_failed",
            bucket=bucket_name,
            object=db_object,
            sqlite_db_path=str(db_path),
            error=str(error),
            fallback="continue_with_empty_db",
        )
        return False
    except Exception as error:  # pragma: no cover - defensive fallback
        log_event(
            logging.WARNING,
            "sqlite_restore_failed",
            bucket=bucket_name,
            object=db_object,
            sqlite_db_path=str(db_path),
            error=str(error),
            fallback="continue_with_empty_db",
        )
        return False


def backup_sqlite_to_gcs() -> dict[str, str]:
    bucket_name = get_gcs_bucket_name()
    db_object = get_gcs_db_object()
    db_path = get_sqlite_db_path()

    if not bucket_name or not db_object:
        raise RuntimeError("GCS_BUCKET_NAME and GCS_DB_OBJECT are required for backup")

    if not db_path.exists():
        raise RuntimeError(f"SQLite DB file does not exist: {db_path}")

    snapshot_path: Path | None = None
    tmp_object = f"{db_object}.tmp-{uuid.uuid4().hex}"

    try:
        snapshot_path = _snapshot_sqlite(db_path)

        client = _get_storage_client()
        bucket = client.bucket(bucket_name)

        tmp_blob = bucket.blob(tmp_object)
        tmp_blob.upload_from_filename(str(snapshot_path))

        final_blob = bucket.blob(db_object)
        final_blob.rewrite(tmp_blob)
        tmp_blob.delete()

        result = {
            "bucket": bucket_name,
            "object": db_object,
            "sqlite_db_path": str(db_path),
            "temporary_object": tmp_object,
        }
        log_event(logging.INFO, "sqlite_backup_succeeded", **result)
        return result
    except Exception as error:
        log_event(
            logging.ERROR,
            "sqlite_backup_failed",
            bucket=bucket_name,
            object=db_object,
            sqlite_db_path=str(db_path),
            temporary_object=tmp_object,
            error=str(error),
        )
        raise
    finally:
        if snapshot_path and snapshot_path.exists():
            snapshot_path.unlink()
