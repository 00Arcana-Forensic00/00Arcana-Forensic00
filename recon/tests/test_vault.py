import importlib.util
from pathlib import Path

import pytest

from arcana_recon import vault

from conftest import PASSPHRASE

# Same vectors as the Rust tests in crates/arcana-vault/src/lib.rs.
KDF_VECTOR = "af8f2e7bf7f40bde9c81e87d042524a09521cb74dafddad97d5f6e8ba628301b"
INTEROP_BLOB = (
    "4152434e01e78798961be15be292a5015c03be1f69ef8f27bb0e8eb1a13b5d6b7c613fbd69c17f04"
    "42ba547e8346e23fd099b9fde0aa49cb356bd47d5dca502d72841313a52adf98e8ad51c2"
)


def test_kdf_matches_rust_vector():
    assert vault.derive_key(PASSPHRASE, bytes(range(16))).hex() == KDF_VECTOR


def test_unseals_shared_interop_blob():
    assert vault.unseal(bytes.fromhex(INTEROP_BLOB), PASSPHRASE) == b"arcana-recon interop vector"


def test_roundtrip_and_layout():
    blob = vault.seal(b"payload", PASSPHRASE)
    assert blob[:4] == b"ARCN" and blob[4] == 1
    assert len(blob) == vault.HEADER_LEN + len(b"payload") + vault.TAG_LEN
    assert vault.unseal(blob, PASSPHRASE) == b"payload"


def test_each_seal_uses_fresh_salt_and_nonce():
    a, b = vault.seal(b"x", PASSPHRASE), vault.seal(b"x", PASSPHRASE)
    assert a[5:vault.HEADER_LEN] != b[5:vault.HEADER_LEN]


def test_wrong_passphrase_fails():
    blob = vault.seal(b"x", PASSPHRASE)
    with pytest.raises(vault.VaultError, match="authentication"):
        vault.unseal(blob, "wrong passphrase entirely")


def test_tampered_blob_fails():
    blob = bytearray(vault.seal(b"evidence page", PASSPHRASE))
    blob[-20] ^= 0x01
    with pytest.raises(vault.VaultError):
        vault.unseal(bytes(blob), PASSPHRASE)


@pytest.mark.parametrize("blob,msg", [
    (b"ARCN\x01" + b"\x00" * 10, "too short"),
    (b"NOPE\x01" + b"\x00" * 60, "bad magic"),
    (b"ARCN\x02" + b"\x00" * 60, "unsupported"),
])
def test_malformed_blobs(blob, msg):
    with pytest.raises(vault.VaultError, match=msg):
        vault.unseal(blob, PASSPHRASE)


def test_short_passphrase_rejected():
    with pytest.raises(vault.VaultError, match="at least 12"):
        vault.seal(b"x", "short")


def test_compatible_with_demo_seal_script():
    script = Path(__file__).resolve().parents[2] / "demo" / "scripts" / "seal_demo.py"
    spec = importlib.util.spec_from_file_location("seal_demo", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert vault.unseal(mod.seal(b"from demo script", PASSPHRASE), PASSPHRASE) == b"from demo script"
