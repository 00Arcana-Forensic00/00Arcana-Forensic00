"""Render store screenshots from the real UI and engine (sample page) with Playwright.

    python packaging/screenshots.py [--out store/screenshots] [--chromium PATH]

Mac App Store accepts 1280x800 / 2560x1600; Microsoft Store accepts 1366x768 and up.
Images are rendered at 1280x800 CSS px with device scale 2 (2560x1600 PNG).
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from playwright.sync_api import sync_playwright  # noqa: E402

from arcana_restore.app.api import Api  # noqa: E402
from arcana_restore.app.devserver import serve_in_thread  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "store", "screenshots"))
    ap.add_argument("--chromium")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    srv, url = serve_in_thread(Api())
    with sync_playwright() as p:
        b = p.chromium.launch(**({"executable_path": a.chromium} if a.chromium else {}))
        for scheme in ("dark", "light"):
            ctx = b.new_context(viewport={"width": 1280, "height": 800}, device_scale_factor=2, color_scheme=scheme)
            pg = ctx.new_page()
            pg.goto(url)
            pg.wait_for_selector('body[data-ready="1"]')
            def shot(n):
                pg.evaluate("document.activeElement && document.activeElement.blur(); window.scrollTo(0, 0)")
                pg.screenshot(path=os.path.join(a.out, f"{n}-{scheme}.png"))
            shot("1-start")
            pg.click("#sample-btn")
            pg.wait_for_selector("#findings li")
            pg.evaluate("document.getElementById('toast').classList.remove('show')")
            pg.fill("#split", "48")
            pg.dispatch_event("#split", "input")
            time.sleep(0.3)
            shot("2-compare")
            pg.check("#show-mask")
            time.sleep(0.3)
            shot("3-filled-areas")
            pg.click("#tab-vaults")
            shot("4-vaults")
            ctx.close()
        b.close()
    srv.shutdown()
    print(f"screenshots written to {os.path.abspath(a.out)}")


if __name__ == "__main__":
    main()
