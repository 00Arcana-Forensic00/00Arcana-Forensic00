import json
import os
import subprocess
import sys
import cv2
import numpy as np
import pytest
from conftest import FAST_KDF, PW, make_page
from arcana_restore import pipeline, vault
from arcana_restore.ledger import Ledger


def run(evidence, tmp_path, **kw):
    vd = str(tmp_path / "vault")
    return vd, pipeline.process_batch([str(evidence)], vd, PW, 2, kdf=FAST_KDF, **kw)


def test_seal_extract_original_is_byte_identical(evidence, tmp_path):
    vd, (r,) = run(evidence, tmp_path)
    assert r.ok and r.report["status"] == "repaired"
    out = pipeline.extract(r.vault_path, PW, str(tmp_path / "out"))
    orig = [p for p in out if ".original." in p][0]
    assert open(orig, "rb").read() == evidence.read_bytes()
    restored = cv2.imread([p for p in out if ".restored." in p][0])
    assert restored is not None and restored.shape[:2] == (600, 800)
    manifest = json.load(open([p for p in out if p.endswith(".manifest.json")][0]))
    assert manifest["entries"]["original"]["sha256"] == pipeline.sha256(evidence.read_bytes())
    assert (os.stat(r.vault_path).st_mode & 0o777) == 0o600


def test_extract_in_a_fresh_process(evidence, tmp_path):
    vd, (r,) = run(evidence, tmp_path)
    pw = tmp_path / "pw"; pw.write_text(PW)
    src = os.path.join(os.path.dirname(__file__), "..", "src")
    env = {**os.environ, "PYTHONPATH": src}
    p = subprocess.run([sys.executable, "-m", "arcana_restore", "extract", r.vault_path, "-o", str(tmp_path / "o2"),
                        "--passphrase-file", str(pw)], capture_output=True, text=True, env=env)
    assert p.returncode == 0, p.stderr
    (tmp_path / "pw2").write_text("definitely the wrong one")
    bad = subprocess.run([sys.executable, "-m", "arcana_restore", "extract", r.vault_path, "-o", str(tmp_path / "o4"),
                          "--passphrase-file", str(tmp_path / "pw2")], capture_output=True, text=True, env=env)
    assert bad.returncode == 2 and "authentication failed" in bad.stderr


def test_ledger_records_and_verifies(evidence, tmp_path):
    vd, (r,) = run(evidence, tmp_path)
    ok, n, _, _ = Ledger(os.path.join(vd, pipeline.LEDGER_NAME)).verify()
    assert ok and n == 1
    entry = json.loads(open(os.path.join(vd, pipeline.LEDGER_NAME)).readline())
    assert entry["data"]["source_sha256"] == pipeline.sha256(evidence.read_bytes())
    assert entry["data"]["vault_sha256"] == pipeline.sha256(open(r.vault_path, "rb").read())


def test_refuses_to_overwrite_existing_vault(evidence, tmp_path):
    vd, (r,) = run(evidence, tmp_path)
    (r2,) = pipeline.process_batch([str(evidence)], vd, "another long passphrase", 1, kdf=FAST_KDF)
    assert not r2.ok and "already exists" in r2.error
    assert pipeline.extract(r.vault_path, PW, str(tmp_path / "o"))  # first vault intact


def test_rejects_symlink_nonimage_and_logs_it(tmp_path):
    real = tmp_path / "real.png"; real.write_bytes(cv2.imencode(".png", make_page())[1].tobytes())
    link = tmp_path / "link.png"; link.symlink_to(real)
    junk = tmp_path / "junk.png"; junk.write_bytes(b"MZ" + os.urandom(64))
    vd = str(tmp_path / "v")
    res = pipeline.process_batch([str(link), str(junk)], vd, PW, 2, kdf=FAST_KDF)
    assert not any(r.ok for r in res)
    ok, n, _, _ = Ledger(os.path.join(vd, pipeline.LEDGER_NAME)).verify()
    assert ok and n == 2


def test_extract_refuses_overwrite_and_uses_safe_names(evidence, tmp_path):
    vd, (r,) = run(evidence, tmp_path)
    pipeline.extract(r.vault_path, PW, str(tmp_path / "o"))
    with pytest.raises(FileExistsError):
        pipeline.extract(r.vault_path, PW, str(tmp_path / "o"))
    assert pipeline.safe_name("../../etc/passwd") == "passwd"
    assert "/" not in pipeline.safe_name("a/b\\c:d.png")


def test_tampered_vault_never_yields_output(evidence, tmp_path):
    vd, (r,) = run(evidence, tmp_path)
    b = bytearray(open(r.vault_path, "rb").read()); b[-30] ^= 1
    open(r.vault_path, "wb").write(b)
    with pytest.raises(vault.AuthError):
        pipeline.extract(r.vault_path, PW, str(tmp_path / "o"))
    assert not (tmp_path / "o").exists() or not os.listdir(tmp_path / "o")


def test_batch_directory_parallel(tmp_path):
    d = tmp_path / "batch"; d.mkdir()
    for i in range(6):
        (d / f"p{i}.png").write_bytes(cv2.imencode(".png", make_page(glare=bool(i % 2)))[1].tobytes())
    files = pipeline.collect([str(d)])
    res = pipeline.process_batch(files, str(tmp_path / "v"), PW, 4, kdf=FAST_KDF)
    assert all(r.ok for r in res)
    assert Ledger(str(tmp_path / "v" / pipeline.LEDGER_NAME)).verify()[1] == 6
