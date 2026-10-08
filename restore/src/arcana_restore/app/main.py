"""Launch the Arcalume window (pywebview: WebView2 on Windows, WKWebView on macOS, WebKitGTK/Qt on Linux).

The page is handed to the web view as one inlined HTML string, so no local web
server is started and no port is opened. Its Content-Security-Policy forbids any
network request, so the UI cannot phone home even by accident.
"""

from __future__ import annotations

import os
import sys

from .. import brand
from .api import Api

WEB = os.path.join(os.path.dirname(__file__), "web")


def page_html() -> str:
    def read(name):
        with open(os.path.join(WEB, name), "r", encoding="utf-8") as fh:
            return fh.read()
    html = read("index.html")
    html = html.replace('<link rel="stylesheet" href="app.css">', f"<style>\n{read('app.css')}\n</style>")
    html = html.replace('<script src="app.js"></script>', f"<script>\n{read('app.js')}\n</script>")
    return html


def _dialogs(window):
    import webview

    try:
        FileDialog = webview.FileDialog
        OPEN, FOLDER, SAVE = FileDialog.OPEN, FileDialog.FOLDER, FileDialog.SAVE
    except AttributeError:  # pywebview < 5.4
        OPEN, FOLDER, SAVE = webview.OPEN_DIALOG, webview.FOLDER_DIALOG, webview.SAVE_DIALOG
    home = os.path.expanduser("~")

    def first(x):
        if not x:
            return None
        return x[0] if isinstance(x, (list, tuple)) else x

    return {
        "open_images": lambda: list(window.create_file_dialog(
            OPEN, directory=home, allow_multiple=True,
            file_types=("Images (*.png;*.jpg;*.jpeg;*.tif;*.tiff;*.bmp)", "All files (*.*)")) or []),
        "folder": lambda purpose="": first(window.create_file_dialog(FOLDER, directory=home)),
        "open_vault": lambda: first(window.create_file_dialog(
            OPEN, directory=home, file_types=("Arcana vault (*.arcr)", "All files (*.*)"))),
        "save_png": lambda suggested: first(window.create_file_dialog(
            SAVE, directory=home, save_filename=suggested)),
    }


def main() -> int:
    try:
        import webview
    except ImportError:
        print("The app window needs pywebview: pip install 'arcana-restore[app]'", file=sys.stderr)
        return 2
    api = Api()
    window = webview.create_window(brand.APP_NAME, html=page_html(), js_api=api,
                                   width=1320, height=880, min_size=(420, 560),
                                   background_color="#0b0f14", text_select=True)
    api._dialogs = _dialogs(window)
    if "--smoke" in sys.argv[1:]:
        return _smoke(webview, window)
    webview.start(private_mode=False, debug=bool(os.environ.get("ARCALUME_DEBUG")))
    return 0


def _smoke(webview, window) -> int:
    """CI check for a built app: the window opens, the page loads and reaches the back end."""
    import time

    outcome = {"code": 1}

    def probe() -> str:
        """What the page looks like right now (shown when the check fails, so CI says why)."""
        bits = []
        for label, js in (("readyState", "document.readyState"),
                          ("bridge", "typeof window.pywebview"),
                          ("ready", "document.body && document.body.dataset.ready"),
                          ("href", "location.href.slice(0, 60)")):
            try:
                bits.append(f"{label}={window.evaluate_js(js)!r}")
            except Exception as exc:  # noqa: BLE001
                bits.append(f"{label}!{type(exc).__name__}: {str(exc)[:80]}")
        return ", ".join(bits)

    def check():
        start = time.time()
        deadline = start + 60
        last_exc = None
        next_report = start + 10
        while time.time() < deadline:
            try:
                if window.evaluate_js("document.body.dataset.ready") == "1":
                    name = window.evaluate_js("document.getElementById('app-name').textContent")
                    print(f"smoke: window ready, app name {name!r}")
                    outcome["code"] = 0 if name == brand.APP_NAME else 1
                    break
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
            if time.time() >= next_report:
                print(f"smoke: waiting ({int(time.time() - start)} s): {probe()}", file=sys.stderr, flush=True)
                next_report += 10
            time.sleep(0.5)
        else:
            print("smoke: page did not become ready", file=sys.stderr)
            print(f"smoke: last state: {probe()}", file=sys.stderr)
            if last_exc is not None:
                print(f"smoke: last error: {type(last_exc).__name__}: {last_exc}", file=sys.stderr)
        window.destroy()

    webview.start(check)
    return outcome["code"]


if __name__ == "__main__":
    raise SystemExit(main())
