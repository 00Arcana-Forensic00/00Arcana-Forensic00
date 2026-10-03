"""Write the desktop engine's outputs as fixtures for the Android core's JUnit tests.

    python android/tools/make_fixtures.py

The Kotlin tests then prove the phone app reads what the desktop app writes (vaults,
ledgers, license keys) and that the ported engine finds the same damage and makes the
same repair. The reverse direction (desktop reads what the phone writes) is
restore/tests/test_android_interop.py.

The Ed25519 key here is derived from a fixed, public test seed. It signs test keys
only; it is never listed in any shipped build.
"""
from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "restore" / "src"))
sys.path.insert(0, str(ROOT / "restore" / "tests"))

import cv2  # noqa: E402
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey  # noqa: E402
from cryptography.hazmat.primitives import serialization  # noqa: E402

from arcana_restore import imaging, licensing, synth, vault  # noqa: E402
from arcana_restore.ledger import Ledger  # noqa: E402
from conftest import make_page  # noqa: E402

OUT = ROOT / "android" / "core" / "src" / "test" / "resources" / "fixtures"
PW = "correct horse battery staple"
FAST_KDF = {"name": "argon2id", "t": 1, "m_kib": 16384, "p": 1}
TEST_SEED = bytes(range(32))  # public test seed: never a production key


def write_json(name: str, obj) -> None:
    (OUT / name).write_text(json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def engine_case(name: str, img, cfg: imaging.RepairConfig) -> dict:
    cv2.imwrite(str(OUT / f"{name}.input.png"), img)
    restored, mask, report = imaging.recover(img, cfg)
    nodes = imaging.reading_order(restored)
    cv2.imwrite(str(OUT / f"{name}.restored.png"), restored)
    cv2.imwrite(str(OUT / f"{name}.mask.png"), mask)
    return {"name": name, "settings": {"flatten": cfg.flatten, "fill_shadow": cfg.fill_shadow, "repair": cfg.repair},
            "report": report, "reading_order": nodes}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    # ---- vault sealed by the desktop app
    manifest = {"tool": "arcana-restore fixture", "source_name": "Übersicht.png", "entries": {}}
    entries = {"manifest": json.dumps(manifest, sort_keys=True).encode(), "original": b"\x89PNG fake original",
               "restored": b"restored bytes", "mask": b""}
    (OUT / "desktop.arcr").write_bytes(vault.seal(entries, PW, FAST_KDF))

    # ---- ledger written by the desktop app (floats, non-ASCII, nulls, nesting)
    led = OUT / "desktop_ledger.jsonl"
    if led.exists():
        led.unlink()
    lg = Ledger(str(led))
    lg.append("evidence_sealed", {"source_name": "Übersicht – März.png", "masked_fraction": 0.012345, "status": "repaired"})
    lg.append("rejected", {"source_name": "x\u0007y.jpg", "source_sha256": None, "reason": "tiny 5e-05 \"quoted\""})
    lg.append("note", {"list": [1, 2.5, 1e-07, True, None], "nested": {"b": 1, "a": "é中\U0001F600"}})
    ok, n, head, _ = lg.verify()
    assert ok

    # ---- license keys
    priv = Ed25519PrivateKey.from_private_bytes(TEST_SEED)
    pub = base64.b64encode(priv.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)).decode()

    def key(**over):
        payload = {"v": 1, "product": "arcalume", "id": "lic_fixture", "plan": "pro", "email": "ann@example.com",
                   "name": "Ann Examiner", "seats": 1, "issued": "2026-09-30", "expires": None, "order": "fixture"}
        payload.update(over)
        return licensing.encode_key(payload, priv.sign(licensing.canonical(payload)))

    other = Ed25519PrivateKey.from_private_bytes(bytes(range(1, 33)))
    forged_payload = {"v": 1, "product": "arcalume", "email": "x@example.com"}
    write_json("desktop.json", {
        "passphrase": PW,
        "ledger_head": head, "ledger_entries": n,
        "public_key": pub,
        "keys": {
            "valid": key(),
            "valid_until_2030": key(expires="2030-01-01"),
            "expired": key(expires="2020-01-01"),
            "bad_expiry": key(expires="soon"),
            "other_product": key(product="arcana-recon"),
            "forged": licensing.encode_key(forged_payload, other.sign(licensing.canonical(forged_payload))),
        },
        "canonical": [
            {"value": {"b": [1, 2.5, None, True], "a": "é\u007f\u001f\"\\/"}},
            {"value": {"x": 0.1, "y": 1e-05, "z": 1234567.0, "neg": -0.000123}},
        ],
    })
    data = json.loads((OUT / "desktop.json").read_text(encoding="utf-8"))
    for c in data["canonical"]:
        c["bytes"] = json.dumps(c["value"], sort_keys=True, separators=(",", ":"))
    write_json("desktop.json", data)

    # ---- engine cases
    cases = [
        engine_case("synth_page", cv2.cvtColor(synth.make_page(7).damaged, cv2.COLOR_GRAY2BGR), imaging.RepairConfig()),
        engine_case("bars_page", make_page(), imaging.RepairConfig()),
        engine_case("bars_fill_shadow", make_page(), imaging.RepairConfig(fill_shadow=True)),
        engine_case("bars_report_only", make_page(), imaging.RepairConfig(repair=False)),
        engine_case("clean_page", make_page(glare=False), imaging.RepairConfig()),
    ]
    write_json("engine.json", {"opencv": cv2.__version__, "cases": cases})
    print(f"wrote fixtures to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
