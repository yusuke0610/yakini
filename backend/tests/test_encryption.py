"""暗号化ユーティリティのユニットテスト。"""

import pytest

from app.core.encryption import decrypt_field, encrypt_field


def test_encrypt_decrypt_roundtrip() -> None:
    """暗号化→復号で元の値に戻ること。"""
    original = "test@example.com"
    encrypted = encrypt_field(original)
    assert decrypt_field(encrypted) == original


def test_encrypt_produces_different_ciphertext() -> None:
    """同じ値でも毎回異なる暗号文が生成されること（Fernet の IV によるランダム性）。"""
    value = "secret-value"
    cipher1 = encrypt_field(value)
    cipher2 = encrypt_field(value)
    assert cipher1 != cipher2
    # どちらも復号すると同じ値に戻る
    assert decrypt_field(cipher1) == value
    assert decrypt_field(cipher2) == value


def test_decrypt_invalid_token() -> None:
    """不正な暗号文を復号しようとすると例外が発生すること。"""
    with pytest.raises(Exception):
        decrypt_field("this-is-not-a-valid-fernet-token")
