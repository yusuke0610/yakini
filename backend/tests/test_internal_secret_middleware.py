import pytest
from app.main import InternalSecretMiddleware
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _make_client(secret: str, env: str) -> TestClient:
    """テスト用のミニ FastAPI アプリを構築して TestClient を返す。"""
    mini = FastAPI()

    @mini.get("/api/test")
    def api_test():
        return {"ok": True}

    @mini.get("/auth/test")
    def auth_test():
        return {"ok": True}

    @mini.get("/health")
    def health_check():
        return {"status": "ok"}

    @mini.get("/other")
    def other():
        return {"ok": True}

    mini.add_middleware(InternalSecretMiddleware, secret=secret, env=env)
    return TestClient(mini, raise_server_exceptions=False)


class TestInternalSecretMiddleware:
    """InternalSecretMiddleware のユニットテスト。"""

    def test_valid_secret_passes(self):
        """正しい secret ヘッダーを付与したリクエストは 200 を返す。"""
        client = _make_client(secret="test-secret", env="dev")
        resp = client.get("/api/test", headers={"X-Internal-Secret": "test-secret"})
        assert resp.status_code == 200

    def test_missing_secret_returns_403(self):
        """secret ヘッダーなしのリクエストは 403 を返す。"""
        client = _make_client(secret="test-secret", env="dev")
        resp = client.get("/api/test")
        assert resp.status_code == 403

    def test_wrong_secret_returns_403(self):
        """誤った secret ヘッダーのリクエストは 403 を返す。"""
        client = _make_client(secret="test-secret", env="dev")
        resp = client.get("/api/test", headers={"X-Internal-Secret": "wrong-secret"})
        assert resp.status_code == 403

    def test_local_env_skips_validation(self):
        """ENVIRONMENT=local ではヘッダーなしでも 200 を返す。"""
        client = _make_client(secret="", env="local")
        resp = client.get("/api/test")
        assert resp.status_code == 200

    def test_health_skips_validation(self):
        """/health はヘッダーなしでも 200 を返す。"""
        client = _make_client(secret="test-secret", env="prod")
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_auth_endpoint_blocked_without_secret(self):
        """/auth/* もヘッダーなしでは 403 を返す。"""
        client = _make_client(secret="test-secret", env="dev")
        resp = client.get("/auth/test")
        assert resp.status_code == 403

    def test_auth_endpoint_passes_with_secret(self):
        """/auth/* も正しいヘッダーがあれば 200 を返す。"""
        client = _make_client(secret="test-secret", env="dev")
        resp = client.get("/auth/test", headers={"X-Internal-Secret": "test-secret"})
        assert resp.status_code == 200

    def test_non_skip_path_requires_secret(self):
        """/health 以外の全パスは secret ヘッダーを要求する。"""
        client = _make_client(secret="test-secret", env="dev")
        resp = client.get("/other")
        assert resp.status_code == 403


def test_get_internal_secret_raises_in_non_local_without_secret(monkeypatch):
    """非 local 環境で INTERNAL_SECRET 未設定の場合は RuntimeError を送出する。"""
    monkeypatch.setenv("ENVIRONMENT", "dev")
    monkeypatch.delenv("INTERNAL_SECRET", raising=False)

    # キャッシュを持たない関数なので直接呼び出せる
    from app.core.settings import get_internal_secret

    with pytest.raises(RuntimeError, match="INTERNAL_SECRET"):
        get_internal_secret()


def test_get_internal_secret_returns_value_when_set(monkeypatch):
    """INTERNAL_SECRET が設定されていれば値を返す。"""
    monkeypatch.setenv("ENVIRONMENT", "prod")
    monkeypatch.setenv("INTERNAL_SECRET", "my-secret-value")

    from app.core.settings import get_internal_secret

    assert get_internal_secret() == "my-secret-value"


def test_get_internal_secret_local_env_allows_empty(monkeypatch):
    """local 環境では INTERNAL_SECRET 未設定でも RuntimeError を送出しない。"""
    monkeypatch.setenv("ENVIRONMENT", "local")
    monkeypatch.delenv("INTERNAL_SECRET", raising=False)

    from app.core.settings import get_internal_secret

    assert get_internal_secret() == ""
