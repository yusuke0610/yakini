import os
import secrets
from unittest.mock import AsyncMock

import app.routers.internal as _internal_router
import app.services.tasks.local as _tasks_local
import app.services.tasks.worker as _worker
import pytest
from app.core.security.auth import create_access_token, create_refresh_token
from app.db import Base, get_db
from app.models import (  # noqa: F401 — ensure models registered
    BlogAccount,
    BlogArticle,
    BlogSummaryCache,
    CareerAnalysis,
    GitHubAnalysisCache,
    MQualification,
    MTechnologyStack,
    Resume,
    User,
)
from app.repositories import UserRepository
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


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
def db_session(tmp_path):
    """一時ファイル SQLite を使うことで複数接続（worker の SessionLocal 等）を可能にする。"""
    engine = create_engine(
        f"sqlite:///{tmp_path}/test.db",
        connect_args={"check_same_thread": False},
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

    # execute_task をノーオペレーションに差し替える。
    # テスト用のインメモリDBとLLMを持たない環境でバックグラウンドタスクが
    # 実際に実行されると例外が発生し TestClient が伝播させてしまうため。
    # バックグラウンドタスクの動作を検証したいテストはワーカー関数を直接呼ぶこと。
    #
    # ``from ... import execute_task`` で各モジュールに束縛されたシンボルは
    # 元モジュール (_worker) への再代入では差し変わらないため、
    # 参照を保持している全モジュールを同じ AsyncMock に揃える。
    mock_execute_task = AsyncMock(return_value=None)
    originals = {
        module: module.execute_task
        for module in (_worker, _internal_router, _tasks_local)
    }
    for module in originals:
        module.execute_task = mock_execute_task

    limiter.reset()
    with TestClient(app) as c:
        c._db_session = db_session  # auth_header から参照するためセッションを保持
        yield c
    app.dependency_overrides.clear()
    for module, original in originals.items():
        module.execute_task = original


def auth_header(client, username: str = "testuser") -> dict:
    """テスト用の認証 Cookie をセットするヘルパー。CSRF トークンをヘッダーに含む dict を返す。

    DB にユーザーを直接作成し、JWT Cookie をセットする。
    /auth/register や /auth/login エンドポイントには依存しない。
    """
    db = client._db_session
    repo = UserRepository(db)
    if not repo.get_by_username(username):
        repo.create(username, hashed_password=None, email=f"{username}@example.com")

    access_token = create_access_token(username)
    refresh_token, jti = create_refresh_token(username)
    csrf_token = secrets.token_urlsafe(32)

    # refresh_jti を DB に保存（/auth/refresh の jti 照合テストで必要）
    user = repo.get_by_username(username)
    if user:
        user.refresh_jti = jti
        db.commit()

    client.cookies.set("access_token", access_token)
    client.cookies.set("refresh_token", refresh_token)
    client.cookies.set("csrf_token", csrf_token)

    return {"X-CSRF-Token": csrf_token}
