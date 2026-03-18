import pytest
from jose import jwt

from app.auth import create_access_token, hash_password, verify_password


def test_hash_and_verify_password() -> None:
    hashed = hash_password("secret123")

    assert verify_password("secret123", hashed)


def test_verify_wrong_password() -> None:
    hashed = hash_password("secret123")

    assert not verify_password("wrong", hashed)


def test_create_access_token_contains_username(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SECRET_KEY", "testsecret")

    token = create_access_token("alice")
    payload = jwt.decode(token, "testsecret", algorithms=["HS256"])

    assert payload["sub"] == "alice"


def test_create_access_token_has_expiry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SECRET_KEY", "testsecret")

    token = create_access_token("alice")
    payload = jwt.decode(token, "testsecret", algorithms=["HS256"])

    assert "exp" in payload
