import json
import os
import subprocess
import sys
import cv2
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
    if os.name != "nt":  # Windows has no POSIX mode bits; it inherits the folder ACL
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


def test_same_file_sealed_twice_makes_two_independent_vaults(evidence, tmp_path):
    vd, (r,) = run(evidence, tmp_path)
    (r2,) = pipeline.process_batch([str(evidence)], vd, "another long passphrase", 1, kdf=FAST_KDF)
    assert r.ok and r2.ok and r.vault_path != r2.vault_path          # nothing is ever overwritten
    assert pipeline.extract(r.vault_path, PW, str(tmp_path / "o1"))
    assert pipeline.extract(r2.vault_path, "another long passphrase", str(tmp_path / "o2"))
    with pytest.raises(vault.AuthError):
        pipeline.extract(r.vault_path, "another long passphrase", str(tmp_path / "o3"))


def test_existing_vault_path_is_never_replaced(tmp_path):
    p = tmp_path / "v.arcr"; p.write_bytes(b"precious")
    with pytest.raises(FileExistsError):
        pipeline._write_new(str(p), b"new")
    assert p.read_bytes() == b"precious"


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


def test_extract_refuses_symlinked_vault_and_symlinked_output(evidence, tmp_path):
    vd, (r,) = run(evidence, tmp_path)
    link = tmp_path / "vault_link.arcr"; link.symlink_to(r.vault_path)
    with pytest.raises(vault.VaultError, match="symbolic link"):
        pipeline.extract(str(link), PW, str(tmp_path / "o"))
    out = tmp_path / "o2"; out.mkdir()
    target = tmp_path / "victim.txt"; target.write_text("keep me")
    (out / "receipt.original.png").symlink_to(target)
    with pytest.raises(Exception):
        pipeline.extract(r.vault_path, PW, str(out), force=True)
    assert target.read_text() == "keep me"


def test_source_name_not_in_vault_filename_or_ledger(evidence, tmp_path):
    vd, (r,) = run(evidence, tmp_path)
    assert "receipt" not in os.path.basename(r.vault_path)
    assert b"receipt" not in open(os.path.join(vd, pipeline.LEDGER_NAME), "rb").read()
    assert b"receipt" not in open(r.vault_path, "rb").read()          # only inside the encrypted manifest
    out = pipeline.extract(r.vault_path, PW, str(tmp_path / "o"))
    assert any("receipt.original" in p for p in out)                  # ...and restored on extraction


def test_seal_works_on_filesystems_without_hard_links(evidence, tmp_path, monkeypatch):
    def no_link(*a, **k):
        raise OSError(95, "Operation not supported")
    monkeypatch.setattr(os, "link", no_link)
    vd, (r,) = run(evidence, tmp_path)
    assert r.ok
    p = tmp_path / "v.arcr"; p.write_bytes(b"precious")
    with pytest.raises(FileExistsError):
        pipeline._write_new(str(p), b"new")                          # fallback path still never overwrites
    assert p.read_bytes() == b"precious"
    assert pipeline.extract(r.vault_path, PW, str(tmp_path / "o"))


def test_extract_writes_nothing_if_any_destination_exists(evidence, tmp_path):
    vd, (r,) = run(evidence, tmp_path)
    out = tmp_path / "o"; out.mkdir()
    (out / "receipt.mask.png").write_bytes(b"mine")
    with pytest.raises(FileExistsError):
        pipeline.extract(r.vault_path, PW, str(out))
    assert sorted(os.listdir(out)) == ["receipt.mask.png"]            # no partial output


def test_concurrent_sealing_with_default_kdf_does_not_deadlock(evidence, tmp_path):
    """Regression: Argon2id (4 lanes) from several threads used to hang forever. Run in a subprocess so a
    regression fails the test by timeout instead of hanging the suite."""
    import subprocess, sys, textwrap
    src = os.path.join(os.path.dirname(__file__), "..", "src")
    code = textwrap.dedent(f"""
        import shutil, sys
        sys.path.insert(0, {src!r})
        from arcana_restore import pipeline
        files = []
        for i in range(6):
            shutil.copy({str(evidence)!r}, {str(tmp_path)!r} + f"/f{{i}}.png"); files.append({str(tmp_path)!r} + f"/f{{i}}.png")
        res = pipeline.process_batch(files, {str(tmp_path / 'cv')!r}, "a long passphrase here", workers=4)
        sys.exit(0 if all(r.ok for r in res) else 1)
    """)
    p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=120)
    assert p.returncode == 0, p.stderr
