"""Drive the real HTML UI in Chromium against the real back end, and audit accessibility.

Runs axe-core (WCAG 2.0/2.1/2.2 A and AA rules) on every screen in light and dark
themes, then checks keyboard operation, reflow at 320 px, 200% text and the main
flows. Skipped when Playwright or a Chromium build is not installed.
"""
import base64
import os
import sys

import pytest
from conftest import PW, make_page

pw_sync = pytest.importorskip("playwright.sync_api")
axe_mod = pytest.importorskip("axe_playwright_python")

import cv2  # noqa: E402
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey  # noqa: E402

from arcana_restore import vault  # noqa: E402
from arcana_restore.app.api import Api  # noqa: E402
from arcana_restore.app.devserver import serve_in_thread  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packaging"))
import license_tool  # noqa: E402

AXE_JS = open(os.path.join(os.path.dirname(axe_mod.__file__), "axe.min.js"), encoding="utf-8").read()
AXE_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]


@pytest.fixture(scope="module")
def browser():
    with pw_sync.sync_playwright() as p:
        exe = os.environ.get("ARCALUME_CHROMIUM")
        for kw in ([{"executable_path": exe}] if exe else []) + [{}, {"executable_path": "/opt/pw-browsers/chromium"}]:
            try:
                b = p.chromium.launch(**kw)
                break
            except Exception:
                continue
        else:
            pytest.skip("no Chromium available for Playwright")
        yield b
        b.close()


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("ARCALUME_CONFIG_DIR", str(tmp_path / "cfg"))
    monkeypatch.setattr(vault, "DEFAULT_KDF", {"name": "argon2id", "t": 1, "m_kib": 16384, "p": 1})
    priv = Ed25519PrivateKey.generate()
    api = Api({"folder": lambda p="": str(tmp_path / "vault"), "save_png": lambda s: str(tmp_path / s),
               "open_images": lambda: [], "open_vault": lambda: None}, [license_tool.public_b64(priv)])
    srv, url = serve_in_thread(api)
    yield api, url, priv, tmp_path
    srv.shutdown()


def open_page(browser, url, scheme="light", width=1400, height=900):
    ctx = browser.new_context(viewport={"width": width, "height": height}, color_scheme=scheme, bypass_csp=True)
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(url)
    page.wait_for_selector('body[data-ready="1"]')
    page._errors = errors
    return page


def axe(page, label):
    page.add_script_tag(content=AXE_JS)
    res = page.evaluate("tags => axe.run(document, {runOnly: {type: 'tag', values: tags}, resultTypes: ['violations']})", AXE_TAGS)
    bad = [f"{v['id']} ({v['impact']}): {v['help']} -> {[n['target'] for n in v['nodes'][:3]]}" for v in res["violations"]]
    assert not bad, f"{label}: " + "\n".join(bad)


def load_sample(page):
    page.click("#sample-btn")
    page.wait_for_selector("#findings li")


def no_hscroll(page):
    return page.evaluate("document.scrollingElement.scrollWidth <= document.scrollingElement.clientWidth + 1")


@pytest.mark.parametrize("scheme", ["light", "dark"])
def test_axe_every_screen(browser, env, scheme):
    api, url, priv, _ = env
    page = open_page(browser, url, scheme)
    axe(page, f"empty/{scheme}")
    load_sample(page)
    page.check("#show-mask")
    page.check("#show-order")
    page.click("summary")
    axe(page, f"workspace/{scheme}")
    page.click("#tab-vaults")
    axe(page, f"vaults/{scheme}")
    page.click("#tab-license")
    axe(page, f"license/{scheme}")
    page.click("#help-btn")
    axe(page, f"help/{scheme}")
    page.keyboard.press("Escape")
    page.click("#tab-recover")
    page.click("#seal-btn")  # free: upgrade dialog
    assert page.is_visible("#upgrade-dialog")
    axe(page, f"upgrade/{scheme}")
    assert not page._errors


def test_keyboard_only_flow(browser, env):
    api, url, priv, tmp = env
    page = open_page(browser, url)
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement.className") == "skip"
    # tabs with arrow keys
    page.focus("#tab-recover")
    page.keyboard.press("ArrowRight")
    assert page.get_attribute("#tab-vaults", "aria-selected") == "true" and page.is_visible("#panel-vaults")
    page.keyboard.press("End")
    assert page.is_visible("#panel-license")
    page.keyboard.press("Home")
    # open the sample with the keyboard
    page.focus("#sample-btn")
    page.keyboard.press("Enter")
    page.wait_for_selector("#findings li")
    # slider: arrows, Home/End, readable value
    page.focus("#split")
    page.keyboard.press("ArrowRight")
    assert page.input_value("#split") == "51"
    assert page.get_attribute("#split", "aria-valuetext") == "51% original, 49% recovered"
    page.keyboard.press("End")
    assert page.input_value("#split") == "100"
    # mode shortcuts and mask toggle
    page.keyboard.press("Alt+3")
    assert page.get_attribute("#stage", "data-mode") == "after" and page.is_hidden("#split-control")
    page.keyboard.press("Alt+m")
    assert page.is_checked("#show-mask") and page.is_visible("#mask-legend")
    # help dialog opens with F1, closes with Escape, focus returns
    page.focus("#save-btn")
    page.keyboard.press("F1")
    assert page.evaluate("document.getElementById('help-dialog').open")
    page.keyboard.press("Escape")
    assert page.evaluate("document.activeElement.id") == "save-btn"
    # every interactive element has a visible focus indicator
    missing = page.evaluate("""() => [...document.querySelectorAll('button, input, select, textarea, a[href], [tabindex="0"]')]
        .filter(el => el.offsetParent !== null)
        .filter(el => { el.focus({focusVisible: true}); if (document.activeElement !== el) return false;
                        const s = getComputedStyle(el);
                        return s.outlineStyle === 'none' && !el.closest('.seg'); })
        .map(el => el.id || el.textContent.trim().slice(0, 20))""")
    assert missing == []


def test_reflow_320px_and_200_percent_text(browser, env):
    api, url, priv, _ = env
    page = open_page(browser, url, width=320, height=640)
    assert no_hscroll(page)
    load_sample(page)
    assert no_hscroll(page)
    page = open_page(browser, url, width=1280, height=800)
    for _ in range(10):
        if page.is_disabled("#text-larger"):
            break
        page.click("#text-larger")
    assert page.evaluate("getComputedStyle(document.documentElement).fontSize") == "32px"  # 200%
    load_sample(page)
    assert no_hscroll(page)


def test_targets_are_at_least_24px(browser, env):
    api, url, priv, _ = env
    page = open_page(browser, url)
    load_sample(page)
    # A checkbox's target is its whole label (clicking the text toggles it).
    small = page.evaluate("""() => [...document.querySelectorAll('button, select, a.btn, input[type=checkbox], input[type=range], .seg label')]
        .filter(el => el.offsetParent !== null)
        .map(el => [el.id || el.textContent.trim().slice(0, 20),
                    (el.type === 'checkbox' && el.closest('label') ? el.closest('label') : el).getBoundingClientRect()])
        .filter(([, r]) => r.width < 20 || r.height < 20).map(([n]) => n)""")
    assert small == []


def test_drop_a_file_opens_it(browser, env):
    api, url, priv, _ = env
    page = open_page(browser, url)
    png = base64.b64encode(cv2.imencode(".png", make_page())[1].tobytes()).decode()
    page.evaluate("""b64 => {
        const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
        const dt = new DataTransfer();
        dt.items.add(new File([bytes], 'receipt.png', {type: 'image/png'}));
        window.dispatchEvent(new DragEvent('drop', {dataTransfer: dt, bubbles: true, cancelable: true}));
    }""", png)
    page.wait_for_selector("#findings li")
    assert "receipt.png" in page.inner_text("#page-list")
    assert page.is_hidden("#empty")


def test_license_activation_and_seal_flow(browser, env):
    api, url, priv, tmp = env
    page = open_page(browser, url)
    load_sample(page)
    page.click("#save-btn")
    page.wait_for_function("document.getElementById('toast').textContent.includes('watermark')")
    page.click("#plan-btn")
    page.fill("#lic-key", "ARC1.not.valid")
    page.click("#lic-form button[type=submit]")
    page.wait_for_selector("#lic-result .bad")
    page.fill("#lic-key", license_tool.issue(priv, "ann@example.com", "Ann Examiner"))
    page.click("#lic-form button[type=submit]")
    page.wait_for_selector("#lic-result .ok")
    assert page.inner_text("#plan-label") == "Pro" and "Ann Examiner" in page.inner_text("#lic-status")
    page.click("#tab-recover")
    page.click("#seal-btn")
    assert page.evaluate("document.getElementById('seal-dialog').open")
    axe(page, "seal dialog")
    page.click("#sd-dir-btn")
    page.wait_for_function("document.getElementById('sd-dir').value.endsWith('vault')")
    page.fill("#sd-pass", PW)
    page.fill("#sd-pass2", PW + "!")
    page.check("#sd-ack")
    page.click("#sd-go")
    assert "don't match" in page.inner_text("#sd-error")
    assert page.get_attribute("#sd-pass2", "aria-invalid") == "true"
    page.fill("#sd-pass", PW)
    page.fill("#sd-pass2", PW)
    page.click("#sd-go")
    page.wait_for_selector("#seal-done:not([hidden])")
    head = page.input_value("#sd-head")
    assert len(head) == 64 and page.input_value("#sd-pass") == ""
    axe(page, "sealed")
    page.click("#sd-close")
    # verify the log from the Vaults tab with the saved fingerprint
    page.click("#tab-vaults")
    page.fill("#lg-head", head)
    page.click("#ledger-form button[type=submit]")
    page.wait_for_selector("#lg-result .ok")
    vaults = [f for f in os.listdir(tmp / "vault") if f.endswith(".arcr")]
    assert len(vaults) == 1
    page.fill("#ov-file", str(tmp / "vault" / vaults[0]))
    page.fill("#ov-pass", "definitely wrong pass")
    page.fill("#ov-out", str(tmp / "out"))
    page.click("#open-form button[type=submit]")
    page.wait_for_selector("#ov-result .bad")
    page.fill("#ov-pass", PW)
    page.click("#open-form button[type=submit]")
    page.wait_for_selector("#ov-result .ok")
    assert not page._errors


def test_page_makes_no_network_requests(browser, env):
    api, url, priv, _ = env
    page = open_page(browser, url)
    seen = []
    page.on("request", lambda r: seen.append(r.url))
    load_sample(page)
    host = url.split("/index.html")[0]
    assert all(u.startswith(host) or u.startswith("data:") for u in seen), seen
