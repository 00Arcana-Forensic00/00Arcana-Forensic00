"""Passphrase-sealed vault container (ARCR v1).

Layout::

    "ARCR" | version(1) | header_len(4, BE) | header(JSON) | nonce(12) | ciphertext+tag

* Key = Argon2id(passphrase, per-file random salt). The KDF parameters live in the header.
* The whole prefix (magic, version, length, header) is the AES-256-GCM associated data,
  so altering any header byte, including KDF parameters, fails authentication.
* The header carries only what is needed to decrypt: KDF parameters and entry roles/sizes.
  File names, hashes and the repair report are inside the encrypted ``manifest`` entry.
* Nothing is derived from process state: a vault opens in any process with the passphrase.
"""

from __future__ import annotations

import json
import os
import struct
import threading
import unicodedata

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id

MAGIC = b"ARCR"
VERSION = 1
NONCE_LEN = 12
SALT_LEN = 16
MIN_PASSPHRASE_CHARS = 12
MAX_HEADER_BYTES = 64 * 1024
MAX_PLAINTEXT_BYTES = 512 * 1024 * 1024
ROLES = ("manifest", "original", "restored", "mask")

DEFAULT_KDF = {"name": "argon2id", "t": 3, "m_kib": 65536, "p": 4}
# Bounds applied to attacker-controlled headers so a crafted file cannot exhaust memory/CPU.
_KDF_BOUNDS = {"t": (1, 10), "m_kib": (16384, 1048576), "p": (1, 16)}


class VaultError(Exception):
    """Malformed, unsupported or unsafe vault."""


class AuthError(VaultError):
    """Authentication failed: wrong passphrase or the file was modified."""


def _passphrase_bytes(passphrase: str) -> bytes:
    if len(passphrase) < MIN_PASSPHRASE_CHARS:
        raise VaultError(f"passphrase must be at least {MIN_PASSPHRASE_CHARS} characters")
    return unicodedata.normalize("NFC", passphrase).encode("utf-8")


# Argon2id with several lanes uses its own worker threads inside OpenSSL; concurrent derivations
# from different Python threads can deadlock there (seen when sealing a folder with the default
# parameters). One derivation at a time is also easier on memory (64 MiB each).
_KDF_LOCK = threading.Lock()


def _derive(passphrase: str, salt: bytes, kdf: dict) -> bytes:
    with _KDF_LOCK:
        return _argon2(passphrase, salt, kdf)


def _argon2(passphrase: str, salt: bytes, kdf: dict) -> bytes:
    return Argon2id(
        salt=salt,
        length=32,
        iterations=kdf["t"],
        lanes=kdf["p"],
        memory_cost=kdf["m_kib"],
    ).derive(_passphrase_bytes(passphrase))


def _canonical(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def seal(entries: dict[str, bytes], passphrase: str, kdf: dict | None = None) -> bytes:
    """Encrypt ``entries`` (role -> bytes; must include ``manifest``) into one vault blob."""
    if "manifest" not in entries:
        raise VaultError("entries must include a manifest")
    for role in entries:
        if role not in ROLES:
            raise VaultError(f"unknown entry role: {role}")
    plaintext = b"".join(entries.values())
    if len(plaintext) > MAX_PLAINTEXT_BYTES:
        raise VaultError("payload too large")

    params = dict(kdf or DEFAULT_KDF)
    salt = os.urandom(SALT_LEN)
    header = {
        "kdf": {**params, "salt": salt.hex()},
        "entries": [{"role": r, "size": len(b)} for r, b in entries.items()],
    }
    header_bytes = _canonical(header)
    prefix = MAGIC + bytes([VERSION]) + struct.pack(">I", len(header_bytes)) + header_bytes
    nonce = os.urandom(NONCE_LEN)
    key = _derive(passphrase, salt, params)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, prefix)
    return prefix + nonce + ciphertext


def parse_header(blob: bytes) -> tuple[dict, bytes, int]:
    """Validate and return (header, prefix_bytes, ciphertext_offset). Needs no passphrase."""
    if len(blob) < 9 or blob[:4] != MAGIC:
        raise VaultError("not an Arcana vault (bad magic)")
    if blob[4] != VERSION:
        raise VaultError(f"unsupported vault version {blob[4]}")
    (hlen,) = struct.unpack(">I", blob[5:9])
    if hlen == 0 or hlen > MAX_HEADER_BYTES or len(blob) < 9 + hlen + NONCE_LEN + 16:
        raise VaultError("vault header is truncated or oversized")
    try:
        header = json.loads(blob[9 : 9 + hlen])
        kdf = header["kdf"]
        salt = bytes.fromhex(kdf["salt"])
        entries = header["entries"]
        if kdf.get("name") != "argon2id" or len(salt) != SALT_LEN:
            raise ValueError("kdf")
        for key, (lo, hi) in _KDF_BOUNDS.items():
            if not (isinstance(kdf[key], int) and lo <= kdf[key] <= hi):
                raise ValueError(key)
        if not entries or entries[0]["role"] != "manifest":
            raise ValueError("entries")
        seen = set()
        for e in entries:
            if e["role"] not in ROLES or e["role"] in seen or not isinstance(e["size"], int) or e["size"] < 0:
                raise ValueError("entries")
            seen.add(e["role"])
        if sum(e["size"] for e in entries) > MAX_PLAINTEXT_BYTES:
            raise ValueError("size")
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise VaultError(f"invalid vault header ({exc})") from None
    return header, blob[: 9 + hlen], 9 + hlen


def unseal(blob: bytes, passphrase: str) -> dict[str, bytes]:
    """Decrypt and authenticate a vault; returns role -> bytes."""
    header, prefix, off = parse_header(blob)
    kdf = header["kdf"]
    nonce = blob[off : off + NONCE_LEN]
    ciphertext = blob[off + NONCE_LEN :]
    key = _derive(passphrase, bytes.fromhex(kdf["salt"]), kdf)
    try:
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, prefix)
    except InvalidTag:
        raise AuthError("authentication failed: wrong passphrase or the vault was modified") from None
    if len(plaintext) != sum(e["size"] for e in header["entries"]):
        raise VaultError("entry sizes do not match payload")
    out, pos = {}, 0
    for e in header["entries"]:
        out[e["role"]] = plaintext[pos : pos + e["size"]]
        pos += e["size"]
    return out
