import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.models import (  # noqa: F401 — ensure models registered
    BasicInfo,
    BlogAccount,
    BlogArticle,
    MPrefecture,
    MQualification,
    MTechnologyStack,
    Resume,
    Rirekisho,
    User,
)
from app.main import app, limiter

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("SQLITE_DB_PATH", ":memory:")
os.environ.setdefault("APP_BOOTSTRAPPED", "1")
os.environ.setdefault("GITHUB_CLIENT_ID", "test-github-client-id")
os.environ.setdefault("GITHUB_CLIENT_SECRET", "test-github-client-secret")
os.environ.setdefault("FIELD_ENCRYPTION_KEY", "pVo6M_raAWEpAv25F4p4RziywsjfPENokI10DZbNO7E=")


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


def auth_header(client, username: str = "testuser") -> dict:
    """テスト用の認証 Cookie をセットするヘルパー。空の dict を返す（Cookie は自動送信される）。"""
    client.post(
        "/auth/register",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "SecurePass123",
        },
    )
    client.post(
        "/auth/login",
        json={
            "email": f"{username}@example.com",
            "password": "SecurePass123",
        },
    )
    return {}
