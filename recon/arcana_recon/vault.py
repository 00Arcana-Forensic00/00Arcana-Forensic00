"""ARCN v1 vault blobs, byte-compatible with the Rust ``arcana-vault`` crate.

Layout: ``ARCN | version(1) | salt(16) | nonce(12) | ciphertext+tag``.
The key is derived from a passphrase with 100,000 rounds of SHA-256 over
``acc || salt || round_le32``, seeded by ``SHA-256(passphrase || salt || domain)``.
Nothing about the key is ever written to disk or returned to callers; anyone
holding the passphrase can unseal the blob in any process, with either this
module or ``arcana-acquire verify``.
"""
from __future__ import annotations

import hashlib
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC = b"ARCN"
VERSION = 1
SALT_LEN = 16
NONCE_LEN = 12
TAG_LEN = 16
HEADER_LEN = len(MAGIC) + 1 + SALT_LEN + NONCE_LEN
STRETCH_ROUNDS = 100_000
DOMAIN = b"arcana-vault-kdf-v1"
MIN_PASSPHRASE_LEN = 12

KDF_DESCRIPTION = f"sha256-stretch-{STRETCH_ROUNDS}"


class VaultError(Exception):
    """The blob is malformed, the passphrase is wrong, or the data was modified."""


def check_passphrase(passphrase: str) -> bytes:
    # The Rust crate checks byte length (str::len), so compare the UTF-8 length too.
    pw = passphrase.encode("utf-8")
    if len(pw) < MIN_PASSPHRASE_LEN:
        raise VaultError(f"passphrase must be at least {MIN_PASSPHRASE_LEN} characters")
    return pw


def derive_key(passphrase: str, salt: bytes) -> bytes:
    pw = check_passphrase(passphrase)
    if len(salt) != SALT_LEN:
        raise VaultError("salt must be 16 bytes")
    acc = hashlib.sha256(pw + salt + DOMAIN).digest()
    for round_id in range(STRETCH_ROUNDS):
        acc = hashlib.sha256(acc + salt + round_id.to_bytes(4, "little")).digest()
    return acc


def seal(plaintext: bytes, passphrase: str) -> bytes:
    salt = os.urandom(SALT_LEN)
    nonce = os.urandom(NONCE_LEN)
    key = derive_key(passphrase, salt)
    body = AESGCM(key).encrypt(nonce, plaintext, None)
    return MAGIC + bytes([VERSION]) + salt + nonce + body


def unseal(blob: bytes, passphrase: str) -> bytes:
    if len(blob) < HEADER_LEN + TAG_LEN:
        raise VaultError("blob too short")
    if blob[:4] != MAGIC:
        raise VaultError("bad magic: not an ARCN vault blob")
    if blob[4] != VERSION:
        raise VaultError(f"unsupported vault version {blob[4]}")
    salt = blob[5:5 + SALT_LEN]
    nonce = blob[5 + SALT_LEN:HEADER_LEN]
    key = derive_key(passphrase, salt)
    try:
        return AESGCM(key).decrypt(nonce, blob[HEADER_LEN:], None)
    except InvalidTag:
        raise VaultError("authentication failed: wrong passphrase or modified blob") from None
