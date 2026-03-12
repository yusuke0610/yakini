import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("SQLITE_DB_PATH", ":memory:")
os.environ.setdefault("APP_BOOTSTRAPPED", "1")
os.environ.setdefault("FIELD_ENCRYPTION_KEY", "pVo6M_raAWEpAv25F4p4RziywsjfPENokI10DZbNO7E=")

from app.database import Base, get_db
from app.models import BasicInfo, Resume, Rirekisho, User  # noqa: F401 — ensure models registered
from app.main import app, limiter


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    limiter.reset()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
