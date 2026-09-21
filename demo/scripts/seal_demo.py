#!/usr/bin/env python3
"""Seal demo plaintext with the same vault layout as arcana-vault."""
from __future__ import annotations
import hashlib, os, sys
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
MAGIC = b"ARCN"
VERSION = 1
STRETCH_ROUNDS = 100_000
DOMAIN = b"arcana-vault-kdf-v1"

def derive(passphrase: str, salt: bytes) -> bytes:
    if len(passphrase) < 12:
        raise SystemExit("passphrase must be at least 12 characters")
    acc = hashlib.sha256(passphrase.encode("utf-8") + salt + DOMAIN).digest()
    for round_id in range(STRETCH_ROUNDS):
        acc = hashlib.sha256(acc + salt + round_id.to_bytes(4, "little")).digest()
    return acc

def seal(plaintext: bytes, passphrase: str) -> bytes:
    salt = os.urandom(16)
    nonce = os.urandom(12)
    key = derive(passphrase, salt)
    body = AESGCM(key).encrypt(nonce, plaintext, None)
    return MAGIC + bytes([VERSION]) + salt + nonce + body

def main() -> None:
    if len(sys.argv) != 4:
        print("usage: seal_demo.py <plaintext> <out.arcv> <passphrase>", file=sys.stderr)
        raise SystemExit(2)
    src, dest, password = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(seal(src.read_bytes(), password))
    print(f"sealed {src} -> {dest} ({dest.stat().st_size} bytes)")

if __name__ == "__main__":
    main()
