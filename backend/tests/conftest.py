import os

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
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


def _generate_test_rsa_keys() -> tuple[str, str]:
    """テスト用 RSA 鍵ペアを生成して (秘密鍵PEM, 公開鍵PEM) を返す。"""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem_private = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    pem_public = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return pem_private, pem_public


# テスト用 RSA 鍵ペアをモジュール起動時に一度だけ生成する
_test_private_key, _test_public_key = _generate_test_rsa_keys()

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_PRIVATE_KEY", _test_private_key)
os.environ.setdefault("JWT_PUBLIC_KEY", _test_public_key)
os.environ.setdefault("SQLITE_DB_PATH", ":memory:")
os.environ.setdefault("APP_BOOTSTRAPPED", "1")
os.environ.setdefault("GITHUB_CLIENT_ID", "test-github-client-id")
os.environ.setdefault("GITHUB_CLIENT_SECRET", "test-github-client-secret")
os.environ.setdefault("FIELD_ENCRYPTION_KEY", "pVo6M_raAWEpAv25F4p4RziywsjfPENokI10DZbNO7E=")

from app.main import app, limiter  # noqa: E402


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
    """テスト用の認証 Cookie をセットするヘルパー。CSRF トークンをヘッダーに含む dict を返す。"""
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
    csrf_token = client.cookies.get("csrf_token", "")
    return {"X-CSRF-Token": csrf_token}
