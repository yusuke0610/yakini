"""RS256 用の RSA 鍵ペアを生成するスクリプト。

使用例:
    python backend/scripts/generate_keys.py

生成された秘密鍵を JWT_PRIVATE_KEY、公開鍵を JWT_PUBLIC_KEY 環境変数に設定する。
Cloud Run など改行を含めにくい環境では \\n でエスケープして設定すること。
"""
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)

# 秘密鍵（PKCS8 PEM 形式）
pem_private = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)

# 公開鍵（SubjectPublicKeyInfo PEM 形式）
pem_public = private_key.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
)

print("=== Private Key (JWT_PRIVATE_KEY) ===")
print(pem_private.decode())
print("=== Public Key (JWT_PUBLIC_KEY) ===")
print(pem_public.decode())
