#!/usr/bin/env python
"""Generate an RSA key pair for Snowflake key-pair auth (MFA-proof, for dbt).

Writes an unencrypted PKCS8 private key next to this file (rsa_key.p8, gitignored)
and prints the ALTER USER statement to register the public key in Snowsight.

    uv run --with cryptography python gen_keypair.py
"""
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

priv_path = Path(__file__).parent / "rsa_key.p8"
priv_path.write_bytes(
    key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
)

pub_pem = key.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
).decode()
pub_body = (
    pub_pem.replace("-----BEGIN PUBLIC KEY-----", "")
    .replace("-----END PUBLIC KEY-----", "")
    .replace("\n", "")
    .strip()
)

print(f"Private key written to: {priv_path}")
print()
print("Run this ONCE in a Snowsight worksheet:")
print()
print(f"ALTER USER YASERSELVAM SET RSA_PUBLIC_KEY='{pub_body}';")
