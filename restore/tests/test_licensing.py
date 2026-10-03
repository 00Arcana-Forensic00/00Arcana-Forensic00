import base64
import json
import os
import subprocess
import sys

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from arcana_restore import edition, licensing

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packaging"))
import license_tool  # noqa: E402


@pytest.fixture
def signer(tmp_path, monkeypatch):
    monkeypatch.setenv("ARCALUME_CONFIG_DIR", str(tmp_path / "cfg"))
    priv = Ed25519PrivateKey.generate()
    return priv, license_tool.public_b64(priv)


def test_valid_key_round_trip(signer):
    priv, pub = signer
    key = license_tool.issue(priv, "a@example.com", "Ann Examiner")
    p = licensing.verify_key(key, [pub])
    assert p["email"] == "a@example.com" and p["product"] == "arcalume"
    # email clients wrap long lines
    wrapped = "\n".join(key[i:i + 60] for i in range(0, len(key), 60))
    assert licensing.verify_key(wrapped, [pub])["id"] == p["id"]


def test_forged_tampered_and_foreign_keys_rejected(signer):
    priv, pub = signer
    key = license_tool.issue(priv, "a@example.com")
    other = license_tool.issue(Ed25519PrivateKey.generate(), "a@example.com")
    with pytest.raises(licensing.LicenseError, match="not valid"):
        licensing.verify_key(other, [pub])
    prefix, payload, sig = key.split(".")
    doc = json.loads(base64.urlsafe_b64decode(payload + "=="))
    doc["seats"] = 999
    forged = ".".join([prefix, base64.urlsafe_b64encode(licensing.canonical(doc)).rstrip(b"=").decode(), sig])
    with pytest.raises(licensing.LicenseError, match="not valid"):
        licensing.verify_key(forged, [pub])
    for junk in ("", "hello", "ARC1.x", "ARC1.!!.!!", "X" * 5000):
        with pytest.raises(licensing.LicenseError):
            licensing.verify_key(junk, [pub])
    wrong = {"v": 1, "product": "something-else", "id": "x"}
    with pytest.raises(licensing.LicenseError, match="different product"):
        licensing.verify_key(licensing.encode_key(wrong, priv.sign(licensing.canonical(wrong))), [pub])


def test_expiry_and_key_rotation(signer):
    priv, pub = signer
    old = license_tool.issue(priv, "a@example.com", expires="2020-01-01")
    with pytest.raises(licensing.LicenseError, match="expired on 2020-01-01"):
        licensing.verify_key(old, [pub])
    newer = Ed25519PrivateKey.generate()
    k2 = license_tool.issue(newer, "b@example.com")
    assert licensing.verify_key(k2, [pub, license_tool.public_b64(newer)])


def test_no_public_keys_means_nothing_validates(signer):
    priv, _ = signer
    with pytest.raises(licensing.LicenseError, match="cannot validate"):
        licensing.verify_key(license_tool.issue(priv, "a@example.com"), [])


def test_activate_store_current_and_remove(signer, tmp_path):
    priv, pub = signer
    assert licensing.current([pub]) == licensing.FREE
    with pytest.raises(licensing.LicenseError):
        licensing.activate("ARC1.bad.key", [pub])
    assert not os.path.exists(tmp_path / "cfg" / "license.key")      # nothing stored on failure
    ent = licensing.activate(license_tool.issue(priv, "a@example.com", "Ann"), [pub])
    assert ent.plan == "pro" and ent.seal and ent.clean_export and ent.licensee == "Ann"
    if os.name == "posix":
        assert (os.stat(tmp_path / "cfg" / "license.key").st_mode & 0o777) == 0o600
    assert licensing.current([pub]).plan == "pro"
    assert licensing.current([]).plan == "free"                      # key no longer trusted -> free
    licensing.deactivate()
    assert licensing.current([pub]) == licensing.FREE


def test_store_edition_is_pro(monkeypatch, signer):
    monkeypatch.setattr(edition, "EDITION", "store")
    ent = licensing.current([])
    assert ent.plan == "pro" and ent.source == "store"


def test_keygen_refuses_repo_path_and_cli_verify(tmp_path):
    tool = os.path.join(os.path.dirname(__file__), "..", "packaging", "license_tool.py")
    inside = os.path.join(os.path.dirname(__file__), "leak.key")
    r = subprocess.run([sys.executable, tool, "keygen", "--out", inside], capture_output=True, text=True)
    assert r.returncode != 0 and not os.path.exists(inside)
    out = tmp_path / "k.key"
    r = subprocess.run([sys.executable, tool, "keygen", "--out", str(out)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    pub = r.stdout.split("PUBLIC_KEYS): ")[1].split()[0]
    key = subprocess.run([sys.executable, tool, "issue", "--key", str(out), "--email", "x@example.com"],
                         capture_output=True, text=True).stdout.strip()
    v = subprocess.run([sys.executable, tool, "verify", key, "--public-key", pub], capture_output=True, text=True)
    assert v.returncode == 0 and "VALID" in v.stdout
    der = base64.b64decode(out.read_bytes())
    assert isinstance(serialization.load_der_private_key(der, None), Ed25519PrivateKey)
