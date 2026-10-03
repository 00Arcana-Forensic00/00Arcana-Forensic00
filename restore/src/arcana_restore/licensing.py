"""Offline license keys and feature tiers.

A license key is ``ARC1.<payload>.<signature>`` (both base64url, no padding). The
payload is canonical JSON; the signature is Ed25519 over the payload bytes, made by
the vendor's private key (the license worker or ``packaging/license_tool.py``).
The app only holds public keys, so it can verify a key but never mint one, and it
never contacts a server: activation is fully offline.

Tiers
-----
* **Free**: recover and compare pages, export restored copies with a watermark,
  open any vault and verify any ledger. Opening and verifying are always free: a
  customer's own evidence is never held behind a paywall.
* **Pro**: clean exports, sealing into encrypted vaults with a custody ledger,
  batch processing, and the ``process`` command line.

Like any client-side check, this can be bypassed by someone who edits the app.
It keeps honest customers honest; it is not DRM.
"""

from __future__ import annotations

import base64
import json
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime, timezone

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from . import edition

PREFIX = "ARC1"
PRODUCT = "arcalume"
MAX_KEY_CHARS = 4096

# Raw 32-byte Ed25519 public keys, base64. Generate with
# ``python packaging/license_tool.py keygen`` and paste the printed public key here.
# Several keys may be listed to allow rotation. Empty = no key can validate yet.
PUBLIC_KEYS: list[str] = []


class LicenseError(ValueError):
    """The key is malformed, forged, for another product, or expired."""


@dataclass(frozen=True)
class Entitlements:
    plan: str                 # "free" | "pro"
    source: str               # "none" | "key" | "store"
    licensee: str = ""
    expires: str | None = None
    clean_export: bool = False
    seal: bool = False
    batch: bool = False

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


FREE = Entitlements("free", "none")


def _pro(source: str, licensee: str = "", expires: str | None = None) -> Entitlements:
    return Entitlements("pro", source, licensee, expires, clean_export=True, seal=True, batch=True)


def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def _b64e(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def canonical(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def encode_key(payload: dict, signature: bytes) -> str:
    return f"{PREFIX}.{_b64e(canonical(payload))}.{_b64e(signature)}"


def verify_key(key: str, public_keys: list[str] | None = None, today: date | None = None) -> dict:
    """Return the payload of a valid key, or raise LicenseError."""
    key = "".join((key or "").split())  # tolerate line breaks from email clients
    if not key or len(key) > MAX_KEY_CHARS:
        raise LicenseError("That doesn't look like a license key.")
    parts = key.split(".")
    if len(parts) != 3 or parts[0] != PREFIX:
        raise LicenseError("That doesn't look like a license key.")
    try:
        raw, sig = _b64d(parts[1]), _b64d(parts[2])
        payload = json.loads(raw)
    except (ValueError, json.JSONDecodeError):
        raise LicenseError("The license key is damaged. Copy it again from your receipt.") from None
    keys = PUBLIC_KEYS if public_keys is None else public_keys
    if not keys:
        raise LicenseError("This build cannot validate license keys yet.")
    for pk in keys:
        try:
            Ed25519PublicKey.from_public_bytes(base64.b64decode(pk)).verify(sig, raw)
            break
        except (InvalidSignature, ValueError):
            continue
    else:
        raise LicenseError("This license key is not valid.")
    if not isinstance(payload, dict) or payload.get("v") != 1 or payload.get("product") != PRODUCT:
        raise LicenseError("This license key is for a different product.")
    exp = payload.get("expires")
    if exp:
        try:
            expires = date.fromisoformat(exp)
        except (TypeError, ValueError):
            raise LicenseError("The license key has an invalid expiry date.") from None
        if expires < (today or datetime.now(timezone.utc).date()):
            raise LicenseError(f"This license expired on {exp}.")
    return payload


# ---- storage ---------------------------------------------------------------------

def config_dir() -> str:
    override = os.environ.get("ARCALUME_CONFIG_DIR")
    if override:
        return override
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "Arcalume")


def _key_path() -> str:
    return os.path.join(config_dir(), "license.key")


def activate(key: str, public_keys: list[str] | None = None) -> Entitlements:
    """Verify and store a key. Raises LicenseError without storing anything if invalid."""
    payload = verify_key(key, public_keys)
    os.makedirs(config_dir(), mode=0o700, exist_ok=True)
    tmp = _key_path() + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="ascii") as fh:
        fh.write("".join(key.split()) + "\n")
    os.replace(tmp, _key_path())
    return _pro("key", payload.get("name") or payload.get("email") or "", payload.get("expires"))


def deactivate() -> None:
    try:
        os.remove(_key_path())
    except FileNotFoundError:
        pass


def current(public_keys: list[str] | None = None) -> Entitlements:
    """What this installation may do right now."""
    if edition.EDITION == "store":
        return _pro("store")
    try:
        with open(_key_path(), "r", encoding="ascii") as fh:
            key = fh.read(MAX_KEY_CHARS + 2)
    except (FileNotFoundError, UnicodeDecodeError, OSError):
        return FREE
    try:
        payload = verify_key(key, public_keys)
    except LicenseError:
        return FREE
    return _pro("key", payload.get("name") or payload.get("email") or "", payload.get("expires"))
