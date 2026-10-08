import os
import time

import pytest
from conftest import FAST_KDF, PW

tk = pytest.importorskip("tkinter")
from arcana_restore import gui  # noqa: E402


def test_passphrase_rules():
    assert gui.check_passphrase("short") is not None
    assert gui.check_passphrase(PW, "different passphrase here") is not None
    assert gui.check_passphrase(PW, PW) is None


def test_seal_open_verify_logic(evidence, tmp_path):
    seen = []
    res = gui.seal_files([str(evidence)], str(tmp_path / "v"), PW, True, seen.append, FAST_KDF)
    assert res[0].ok and len(seen) == 1
    out = gui.open_vault(res[0].vault_path, PW, str(tmp_path / "o"))
    assert any(p.endswith(".original.png") for p in out)
    ok, n, head, _ = gui.check_ledger(str(tmp_path / "v"))
    assert ok and n == 1
    assert not gui.check_ledger(str(tmp_path / "v"), "0" * 64)[0]


def test_no_images_is_a_clear_error(tmp_path):
    (tmp_path / "x.txt").write_text("hi")
    with pytest.raises(ValueError, match="No supported files"):
        gui.seal_files([str(tmp_path)], str(tmp_path / "v"), PW)


@pytest.fixture(scope="module")
def tk_root():
    """One Tk window for the whole module.

    Creating and destroying a fresh tk.Tk() per test leaves the macOS Tk event loop in a state where
    update() eventually stops returning (seen on the macOS release runner). The shipped app has a single
    window for its whole life, so share one here and give each test a fresh App on it.
    """
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("no display available (run under xvfb-run)")
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def app(tk_root):
    a = gui.App(tk_root)
    yield a
    a.close()
    for w in tk_root.winfo_children():
        w.destroy()


def pump(app, timeout=30):
    end = time.time() + timeout
    time.sleep(0.05)
    while time.time() < end:
        app.root.update()
        if not app.busy:
            return
        time.sleep(0.02)
    raise AssertionError("operation did not finish")


def test_window_seal_then_open_flow(app, evidence, tmp_path, monkeypatch):
    monkeypatch.setattr(gui.messagebox, "showwarning", lambda *a, **k: (_ for _ in ()).throw(AssertionError(a)))
    monkeypatch.setattr(gui.messagebox, "showerror", lambda *a, **k: (_ for _ in ()).throw(AssertionError(a)))
    app._add_paths([str(evidence)])
    app.vault_dir.set(str(tmp_path / "vault"))
    app.pw1.set(PW); app.pw2.set(PW); app.ack.set(True)
    app._seal()
    pump(app)
    assert app.pw1.get() == "" and app.pw2.get() == ""          # secrets cleared
    vaults = [f for f in os.listdir(tmp_path / "vault") if f.endswith(".arcr")]
    assert len(vaults) == 1
    assert app.reveal_path == str(tmp_path / "vault")

    app.vfile.set(str(tmp_path / "vault" / vaults[0]))
    app.opw.set(PW); app.outdir.set(str(tmp_path / "out"))
    app._open()
    pump(app)
    assert app.opw.get() == ""
    assert open(tmp_path / "out" / "receipt.original.png", "rb").read() == evidence.read_bytes()


def test_window_blocks_bad_input(app, evidence, tmp_path, monkeypatch):
    msgs = []
    monkeypatch.setattr(gui.messagebox, "showwarning", lambda t, m: msgs.append(m))
    app._seal()                                        # no files
    app._add_paths([str(evidence)])
    app.pw1.set("short"); app.pw2.set("short"); app._seal()
    app.pw1.set(PW); app.pw2.set(PW); app.ack.set(False); app._seal()
    assert len(msgs) == 3 and not app.busy


def test_wrong_passphrase_reported(app, evidence, tmp_path, monkeypatch):
    res = gui.seal_files([str(evidence)], str(tmp_path / "v"), PW, True, None, FAST_KDF)
    errs = []
    monkeypatch.setattr(gui.messagebox, "showerror", lambda t, m: errs.append(m))
    app.vfile.set(res[0].vault_path); app.opw.set("definitely not the passphrase"); app.outdir.set(str(tmp_path / "o"))
    app._open()
    pump(app)
    assert errs and "Wrong passphrase" in errs[0]
    assert not (tmp_path / "o").exists() or not os.listdir(tmp_path / "o")


def test_window_seals_a_video_and_reports_the_repair(app, tmp_path, monkeypatch):
    from test_video import make_video
    monkeypatch.setattr(gui.messagebox, "showerror", lambda *a, **k: (_ for _ in ()).throw(AssertionError(a)))
    vid = str(tmp_path / "clip.avi")
    make_video(vid, n=10)
    app._add_paths([vid])
    app.vault_dir.set(str(tmp_path / "vault"))
    app.pw1.set(PW); app.pw2.set(PW); app.ack.set(True)
    app._seal()
    pump(app, timeout=90)
    log = app.log.get("1.0", "end")
    assert "1/1 sealed" in log and "(repaired)" in log, log


def test_a_failing_error_dialog_does_not_leave_the_window_busy(app, tmp_path, monkeypatch):
    """If the error dialog itself raises (or a platform dialog misbehaves) the window must still recover."""
    def boom(*a, **k):
        raise RuntimeError("dialog failed")
    monkeypatch.setattr(gui.messagebox, "showerror", boom)
    f = tmp_path / "notes.pdf"; f.write_bytes(b"%PDF-1.7 hello")
    app._add_paths([str(f)])
    app.vault_dir.set(str(tmp_path / "vault"))
    app.pw1.set(PW); app.pw2.set(PW); app.ack.set(True)
    app._run(lambda: (_ for _ in ()).throw(ValueError("worker failed")))
    pump(app, timeout=10)
    assert not app.busy
    assert "ERROR: worker failed" in app.log.get("1.0", "end")


def test_window_shows_a_clear_message_for_an_unsupported_file(app, tmp_path, monkeypatch):
    f = tmp_path / "notes.pdf"; f.write_bytes(b"%PDF-1.7 hello")
    app._add_paths([str(f)])
    app.vault_dir.set(str(tmp_path / "vault"))
    app.pw1.set(PW); app.pw2.set(PW); app.ack.set(True)
    errors = []
    monkeypatch.setattr(gui.messagebox, "showerror", lambda t, m: errors.append(m))
    app._seal()
    pump(app)
    log = app.log.get("1.0", "end")
    assert "Unsupported file type" in log and "0/1 sealed" in log


def test_window_verify_flags_a_wrong_folder(app, tmp_path):
    app.lvault.set(str(tmp_path / "typo"))
    app._verify()
    pump(app)
    assert "FAILED" in app.log.get("1.0", "end")
