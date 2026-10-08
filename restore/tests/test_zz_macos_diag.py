"""TEMPORARY diagnostic (macOS video GUI hang). Not for merging."""
import faulthandler
import os
import subprocess
import sys
import threading
import time

import pytest
from conftest import PW

tk = pytest.importorskip("tkinter")
from arcana_restore import gui  # noqa: E402


def log(msg):
    print(f"[diag {time.strftime('%H:%M:%S')}] {msg}", file=sys.__stderr__, flush=True)


def test_diag_video_window_with_updates(tmp_path, monkeypatch):
    from test_video import make_video
    root = tk.Tk()
    root.withdraw()
    app = gui.App(root)
    errors = []
    monkeypatch.setattr(gui.messagebox, "showerror", lambda *a, **k: errors.append(a))
    monkeypatch.setattr(gui.messagebox, "showwarning", lambda *a, **k: errors.append(("WARN",) + a))
    vid = str(tmp_path / "clip.avi")
    make_video(vid, n=10)
    app._add_paths([vid])
    app.vault_dir.set(str(tmp_path / "vault"))
    app.pw1.set(PW); app.pw2.set(PW); app.ack.set(True)

    state = {"calls": 0, "in_update": False, "t_enter": 0.0}

    def watchdog():
        while True:
            time.sleep(1)
            if state["in_update"] and time.time() - state["t_enter"] > 20:
                log(f"WATCHDOG: update() #{state['calls']} blocked > 20 s; threads={[t.name for t in threading.enumerate()]}")
                faulthandler.dump_traceback(file=sys.__stderr__, all_threads=True)
                try:
                    out = subprocess.run(["sample", str(os.getpid()), "3"], capture_output=True, text=True, timeout=60).stdout
                    # keep the call graphs only; trim for the log
                    log("SAMPLE:\n" + "\n".join(out.splitlines()[:260]))
                except Exception as exc:  # noqa: BLE001
                    log(f"sample failed: {exc!r}")
                os._exit(3)

    threading.Thread(target=watchdog, daemon=True).start()

    app._seal()
    log("_seal returned; polling with update()")
    end = time.time() + 60
    while time.time() < end:
        state["calls"] += 1
        state["t_enter"] = time.time(); state["in_update"] = True
        if state["calls"] <= 3:
            log(f"update() #{state['calls']} start (threads={[t.name for t in threading.enumerate()]})")
        root.update()
        state["in_update"] = False
        if state["calls"] <= 3:
            log(f"update() #{state['calls']} returned")
        if not app.busy:
            break
        time.sleep(0.02)
    log(f"loop done after {state['calls']} updates, busy={app.busy}")
    assert not app.busy, app.log.get("1.0", "end")
