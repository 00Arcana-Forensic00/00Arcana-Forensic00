import base64
import json
import os

import cv2
import pytest
from conftest import PW, make_page
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from arcana_restore import licensing, pipeline
from arcana_restore.app import api as app_api
from arcana_restore.app.main import page_html

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packaging"))
import license_tool  # noqa: E402


@pytest.fixture
def keys(tmp_path, monkeypatch):
    monkeypatch.setenv("ARCALUME_CONFIG_DIR", str(tmp_path / "cfg"))
    priv = Ed25519PrivateKey.generate()
    return priv, [license_tool.public_b64(priv)]


@pytest.fixture
def api(keys, tmp_path, evidence):
    saved = tmp_path / "saved.png"
    dialogs = {"open_images": lambda: [str(evidence)], "save_png": lambda s: str(saved),
               "folder": lambda p="": str(tmp_path / "vault"), "open_vault": lambda: None}
    return app_api.Api(dialogs, keys[1])


def fast_kdf(monkeypatch):
    from arcana_restore import vault
    monkeypatch.setattr(vault, "DEFAULT_KDF", {"name": "argon2id", "t": 1, "m_kib": 16384, "p": 1})


def test_info_is_free_by_default(api):
    info = api.app_info()
    assert info["name"] == "Arcalume" and info["license"]["plan"] == "free"
    json.dumps(info)


def test_open_recover_findings_and_json_safe(api):
    res = api.pick_images()
    assert len(res["docs"]) == 1 and res["docs"][0]["thumb"].startswith("data:image/jpeg;base64,")
    r = api.recover(res["docs"][0]["id"])
    json.dumps(r)  # everything crosses the bridge as JSON
    assert r["status"] == "repaired" and r["after"].startswith("data:image/")
    texts = " ".join(f["text"] for f in r["findings"])
    assert "glare" in texts and "cannot be recovered" in texts and "left untouched" in texts
    r2 = api.recover(res["docs"][0]["id"], {"fill_shadow": True})
    assert "filled, as you asked" in " ".join(f["text"] for f in r2["findings"])


def test_open_bytes_rejects_junk_and_sample_loads(api):
    bad = api.open_bytes("x.png", base64.b64encode(b"not an image").decode())
    assert not bad["docs"] and bad["errors"]
    assert api.open_bytes("x.png", "***")["errors"]
    s = api.load_sample()
    assert s["docs"][0]["width"] == 1000
    assert api.recover(s["docs"][0]["id"])["stats"]["blocks"] > 40


def test_free_export_is_watermarked_pro_is_clean(api, keys, tmp_path):
    d = api.pick_images()["docs"][0]["id"]
    r = api.export(d)
    assert r["ok"] and r["watermarked"]
    free_img = cv2.imread(r["path"])
    assert api.activate_license(license_tool.issue(keys[0], "a@example.com"))["ok"]
    r2 = api.export(d, str(tmp_path / "clean.png"))
    assert r2["ok"] and not r2["watermarked"]
    clean = cv2.imread(r2["path"])
    assert free_img.shape == clean.shape and (free_img != clean).any()
    assert (cv2.imread(r2["path"]) == api._docs[d].restored).all()


def test_seal_requires_pro_then_works_and_opens(api, keys, tmp_path, evidence, monkeypatch):
    fast_kdf(monkeypatch)
    d = api.pick_images()["docs"][0]["id"]
    api.recover(d)
    vd = str(tmp_path / "vault")
    assert api.seal([d], vd, PW, PW)["upgrade"]
    assert not api.activate_license("ARC1.nope.nope")["ok"]
    assert api.activate_license(license_tool.issue(keys[0], "a@example.com"))["ok"]
    assert "match" in api.seal([d], vd, PW, PW + "x")["error"]
    assert "at least" in api.seal([d], vd, "short", "short")["error"]
    r = api.seal([d], vd, PW, PW)
    assert r["ok"] and r["ledger_ok"] and r["ledger_entries"] == 1 and len(r["ledger_head"]) == 64
    vf = r["results"][0]["vault"]
    assert api.open_vault(vf, "wrong passphrase!!", str(tmp_path / "o"))["error"].startswith("Wrong passphrase")
    o = api.open_vault(vf, PW, str(tmp_path / "o"))
    assert o["ok"]
    orig = [p for p in o["written"] if ".original." in p][0]
    assert open(orig, "rb").read() == evidence.read_bytes()
    assert api.open_vault(vf, PW, str(tmp_path / "o"))["error"].startswith("Files from this vault")
    v = api.verify_ledger(vd, r["ledger_head"])
    assert v["ok"] and v["entries"] == 1
    assert not api.verify_ledger(vd, "0" * 64)["ok"]
    assert not api.verify_ledger(str(tmp_path / "nowhere"))["ok"]


def test_vault_opening_is_free(api, keys, tmp_path, evidence, monkeypatch):
    fast_kdf(monkeypatch)
    ledger = pipeline.Ledger(str(tmp_path / "l.jsonl"))
    r = pipeline.process_bytes("receipt.png", evidence.read_bytes(), str(tmp_path / "v"), PW, ledger)
    assert r.ok and api.app_info()["license"]["plan"] == "free"
    assert api.open_vault(r.vault_path, PW, str(tmp_path / "o"))["ok"]


def test_bridge_dispatch_blocks_private_methods(api):
    assert "__error__" in app_api.call(api, "_doc", ["x"])
    assert "__error__" in app_api.call(api, "nope", [])
    assert app_api.call(api, "recover", ["missing"])["__error__"] == "That page is no longer open."


def test_inlined_page_has_no_external_references():
    html = page_html()
    assert "<script src" not in html and 'rel="stylesheet"' not in html
    assert "Content-Security-Policy" in html and "connect-src 'self'" in html
    for scheme in ("http://", "https://"):
        assert scheme not in html.replace("http-equiv", "")
