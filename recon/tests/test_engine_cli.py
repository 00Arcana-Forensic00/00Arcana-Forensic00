import json

import cv2
import numpy as np
import pytest

from arcana_recon import cli, engine, vault

from conftest import PASSPHRASE


@pytest.fixture
def damaged_png(tmp_path, page):
    p = tmp_path / "in" / "exhibit.png"
    p.parent.mkdir()
    cv2.imwrite(str(p), page.damaged)
    return p


def test_process_writes_only_sealed_output_and_report(tmp_path, damaged_png):
    out = tmp_path / "vault"
    rep = engine.process_file(damaged_png, out, PASSPHRASE)
    assert sorted(p.name for p in out.iterdir()) == ["exhibit.png.arcv", "exhibit.png.json"]
    blob = (out / "exhibit.png.arcv").read_bytes()
    assert blob[:4] == b"ARCN" and b"IHDR" not in blob
    text = (out / "exhibit.png.json").read_text()
    assert PASSPHRASE not in text and "key" not in json.loads(text)["output"]
    assert rep["source"]["name"] == "exhibit.png"
    assert rep["triage"]["status"] == "degraded" and rep["layout"]["node_count"] > 40


def test_extract_in_a_fresh_call_verifies_report(tmp_path, damaged_png):
    out = tmp_path / "vault"
    rep = engine.process_file(damaged_png, out, PASSPHRASE)
    res = engine.extract(out / "exhibit.png.arcv", PASSPHRASE, tmp_path / "back.png")
    assert res["report_verified"] and res["source_name"] == "exhibit.png"
    assert res["sha256"] == rep["output"]["plaintext_sha256"]
    assert cv2.imread(str(tmp_path / "back.png"), cv2.IMREAD_GRAYSCALE).shape == (1300, 1000)


def test_extract_detects_report_mismatch(tmp_path, damaged_png):
    out = tmp_path / "vault"
    engine.process_file(damaged_png, out, PASSPHRASE)
    report = out / "exhibit.png.json"
    data = json.loads(report.read_text())
    data["output"]["plaintext_sha256"] = "0" * 64
    report.write_text(json.dumps(data))
    with pytest.raises(vault.VaultError, match="does not match"):
        engine.extract(out / "exhibit.png.arcv", PASSPHRASE, tmp_path / "back.png")


def test_never_overwrites_existing_output(tmp_path, damaged_png):
    out = tmp_path / "vault"
    engine.process_file(damaged_png, out, PASSPHRASE)
    with pytest.raises(FileExistsError):
        engine.process_file(damaged_png, out, PASSPHRASE)


def test_cli_batch_with_bad_file_and_name_collisions(tmp_path, damaged_png, monkeypatch, capsys):
    monkeypatch.setenv("ARCANA_VAULT_PASSWORD", PASSPHRASE)
    src = damaged_png.parent
    cv2.imwrite(str(src / "second.jpg"), np.full((200, 300), 200, np.uint8))
    (src / "fake.png").write_bytes(b"not an image at all")
    other = tmp_path / "other"
    other.mkdir()
    cv2.imwrite(str(other / "exhibit.png"), np.full((100, 100), 180, np.uint8))
    out = tmp_path / "vault"

    code = cli.main(["process", str(src), str(other), "--out", str(out), "--workers", "3"])
    assert code == 2  # one rejected input
    names = sorted(p.name for p in out.iterdir())
    assert names == ["exhibit.png-1.arcv", "exhibit.png-1.json", "exhibit.png.arcv", "exhibit.png.json",
                     "second.jpg.arcv", "second.jpg.json"]
    err = capsys.readouterr().err
    assert "REJECTED" in err and "fake.png" in err

    assert cli.main(["extract", str(out / "second.jpg.arcv")]) == 0
    assert (out / "second.jpg.recovered.png").exists()


def test_cli_rejects_short_passphrase(tmp_path, damaged_png, monkeypatch):
    monkeypatch.setenv("ARCANA_VAULT_PASSWORD", "short")
    with pytest.raises(SystemExit):
        cli.main(["process", str(damaged_png), "--out", str(tmp_path / "v")])


def test_cli_synth(tmp_path):
    assert cli.main(["synth", str(tmp_path / "s")]) == 0
    assert (tmp_path / "s" / "synthetic_damaged.png").exists()
