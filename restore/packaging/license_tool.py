"""Vendor-side license tool. Never ship this or the private key with the app.

    python packaging/license_tool.py keygen --out ~/arcalume-signing.key
        Creates an Ed25519 signing key (PKCS#8, base64) outside the repository and
        prints the public key to paste into ``licensing.PUBLIC_KEYS`` and the value
        to store as the license worker's LICENSE_SIGNING_KEY secret.

    python packaging/license_tool.py issue --key ~/arcalume-signing.key \\
            --email buyer@example.com --name "Jane Examiner" [--expires 2027-10-31] [--seats 1]
        Issues a key by hand (manual sales, press copies, replacements).

    python packaging/license_tool.py verify ARC1.xxx.yyy [--public-key BASE64]
"""

from __future__ import annotations

import argparse
import base64
import os
import secrets
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from cryptography.hazmat.primitives import serialization  # noqa: E402
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey  # noqa: E402

from arcana_restore import licensing  # noqa: E402


def public_b64(priv: Ed25519PrivateKey) -> str:
    raw = priv.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return base64.b64encode(raw).decode()


def load_private(path: str) -> Ed25519PrivateKey:
    with open(path, "rb") as fh:
        der = base64.b64decode(fh.read().strip())
    key = serialization.load_der_private_key(der, password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise SystemExit("not an Ed25519 key")
    return key


def issue(priv: Ed25519PrivateKey, email: str, name: str = "", expires: str | None = None,
          seats: int = 1, plan: str = "pro", order: str = "manual") -> str:
    payload = {
        "v": 1,
        "product": licensing.PRODUCT,
        "id": "lic_" + secrets.token_hex(8),
        "plan": plan,
        "email": email,
        "name": name,
        "seats": seats,
        "issued": datetime.now(timezone.utc).date().isoformat(),
        "expires": expires,
        "order": order,
    }
    return licensing.encode_key(payload, priv.sign(licensing.canonical(payload)))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    k = sub.add_parser("keygen")
    k.add_argument("--out", required=True)
    i = sub.add_parser("issue")
    i.add_argument("--key", required=True)
    i.add_argument("--email", required=True)
    i.add_argument("--name", default="")
    i.add_argument("--expires")
    i.add_argument("--seats", type=int, default=1)
    v = sub.add_parser("verify")
    v.add_argument("license")
    v.add_argument("--public-key", action="append")
    a = ap.parse_args(argv)

    if a.cmd == "keygen":
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        if os.path.abspath(a.out).startswith(repo + os.sep):
            raise SystemExit("refusing to write the private key inside the repository")
        priv = Ed25519PrivateKey.generate()
        der = priv.private_bytes(serialization.Encoding.DER, serialization.PrivateFormat.PKCS8,
                                 serialization.NoEncryption())
        fd = os.open(a.out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as fh:
            fh.write(base64.b64encode(der) + b"\n")
        print(f"private key written to {a.out} (keep it offline; back it up)")
        print(f"public key (paste into licensing.PUBLIC_KEYS): {public_b64(priv)}")
        print(f"worker secret LICENSE_SIGNING_KEY: the single line in {a.out}")
    elif a.cmd == "issue":
        print(issue(load_private(a.key), a.email, a.name, a.expires, a.seats))
    else:
        try:
            payload = licensing.verify_key(a.license, a.public_key)
        except licensing.LicenseError as exc:
            print(f"INVALID: {exc}")
            return 1
        print(f"VALID: {payload}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
