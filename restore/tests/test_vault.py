import os
import struct
import pytest
from conftest import FAST_KDF, PW
from arcana_restore import vault


def test_roundtrip_new_process_independent():
    blob = vault.seal({"manifest": b"{}", "original": b"abc"}, PW, FAST_KDF)
    assert vault.unseal(blob, PW) == {"manifest": b"{}", "original": b"abc"}


def test_wrong_passphrase():
    blob = vault.seal({"manifest": b"{}"}, PW, FAST_KDF)
    with pytest.raises(vault.AuthError):
        vault.unseal(blob, "another long passphrase")


def test_short_passphrase_rejected():
    with pytest.raises(vault.VaultError):
        vault.seal({"manifest": b"{}"}, "short", FAST_KDF)


@pytest.mark.parametrize("idx", [0, 4, 9, 40, -1, -20])
def test_any_flipped_byte_is_rejected(idx):
    blob = bytearray(vault.seal({"manifest": b"{}", "original": b"x" * 50}, PW, FAST_KDF))
    blob[idx] ^= 0x01
    with pytest.raises(vault.VaultError):
        vault.unseal(bytes(blob), PW)


def test_kdf_params_are_authenticated_and_bounded():
    blob = vault.seal({"manifest": b"{}"}, PW, FAST_KDF)
    _, _, off = vault.parse_header(blob)
    hdr = blob[9:off].replace(b'"p":1', b'"p":9')
    forged = blob[:5] + struct.pack(">I", len(hdr)) + hdr + blob[off:]
    with pytest.raises(vault.VaultError):
        vault.unseal(forged, PW)
    huge = blob[9:off].replace(b'"m_kib":16384', b'"m_kib":99999999')
    forged = blob[:5] + struct.pack(">I", len(huge)) + huge + blob[off:]
    with pytest.raises(vault.VaultError, match="invalid vault header"):
        vault.unseal(forged, PW)  # rejected before any expensive KDF work


def test_truncation_and_garbage():
    blob = vault.seal({"manifest": b"{}"}, PW, FAST_KDF)
    for bad in (blob[:-1], blob[:20], b"", b"ARCR", os.urandom(200)):
        with pytest.raises(vault.VaultError):
            vault.unseal(bad, PW)


def test_unique_salt_and_nonce_per_seal():
    a = vault.seal({"manifest": b"{}"}, PW, FAST_KDF)
    b = vault.seal({"manifest": b"{}"}, PW, FAST_KDF)
    assert a != b


def test_no_plaintext_metadata_in_header():
    blob = vault.seal({"manifest": b'{"source_name":"secret-name.png"}'}, PW, FAST_KDF)
    assert b"secret-name" not in blob
