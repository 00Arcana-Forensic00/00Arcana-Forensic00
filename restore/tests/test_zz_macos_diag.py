"""TEMPORARY diagnostic (macOS video GUI hang). Not for merging."""
import sys
import threading
import time

import pytest
from conftest import PW

tk = pytest.importorskip("tkinter")
from arcana_restore import gui  # noqa: E402


def log(msg):
    print(f"[diag {time.strftime('%H:%M:%S')}] {msg}", file=sys.__stderr__, flush=True)


def test_diag_video_window(tmp_path, monkeypatch):
    from test_video import make_video
    root = tk.Tk()
    root.withdraw()
    app = gui.App(root)
    errors = []
    monkeypatch.setattr(gui.messagebox, "showerror", lambda *a, **k: errors.append(a))
    monkeypatch.setattr(gui.messagebox, "showwarning", lambda *a, **k: errors.append(("WARN",) + a))
    vid = str(tmp_path / "clip.avi")
    log("making video")
    make_video(vid, n=10)
    log("video made")
    app._add_paths([vid])
    log(f"files listed: {app.files.size()}")
    app.vault_dir.set(str(tmp_path / "vault"))
    app.pw1.set(PW); app.pw2.set(PW); app.ack.set(True)
    app._seal()
    log(f"_seal returned busy={app.busy} warnings={errors}")
    for i in range(40):  # 20 s without touching Tk
        time.sleep(0.5)
        evs = [(k, (str(p)[:120] if k in ('log', 'error') else '')) for k, p in list(app.events.queue)]
        log(f"i={i} threads={[t.name for t in threading.enumerate()]} busy={app.busy} events={evs}")
        if any(k == 'done' for k, _ in evs):
            break
    log("calling update_idletasks()")
    root.update_idletasks()
    log("update_idletasks returned; calling update()")
    root.update()
    log("update returned")
    log(f"log text: {app.log.get('1.0', 'end')!r}")
