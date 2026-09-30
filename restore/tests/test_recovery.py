"""Recovery quality on a synthetic page with known ground truth (ported from arcana-recon).

These tests pin the product's core claims and their honest limits.
"""
import numpy as np
import pytest

from arcana_restore import imaging, synth


def _bin(gray):
    import cv2
    _, b = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return b


def _f1(pred, truth, box):
    x0, y0, x1, y1 = box
    a, b = pred[y0:y1, x0:x1] > 0, truth[y0:y1, x0:x1] > 0
    return 2 * np.count_nonzero(a & b) / (np.count_nonzero(a) + np.count_nonzero(b))


@pytest.fixture(scope="module")
def page():
    return synth.make_page()


@pytest.fixture(scope="module")
def recovered(page):
    import cv2
    img = cv2.cvtColor(page.damaged, cv2.COLOR_GRAY2BGR)
    fixed, mask, rep = imaging.recover(img)
    return cv2.cvtColor(fixed, cv2.COLOR_BGR2GRAY), mask, rep


def test_clean_page_is_stable(page):
    import cv2
    _, mask, rep = imaging.recover(cv2.cvtColor(page.clean, cv2.COLOR_GRAY2BGR))
    assert not mask.any() and rep["glare_pixels"] == 0 and rep["shadow_pixels"] == 0


def test_triage_finds_glare_and_edge_shadow(recovered):
    _, _, rep = recovered
    cx, cy = synth.GLARE_CENTER
    big = rep["glare_regions"][0]
    assert big["x"] <= cx <= big["x"] + big["w"] and big["y"] <= cy <= big["y"] + big["h"]
    edge = rep["shadow_regions"][0]
    assert edge["x"] == synth.EDGE_SHADOW_X and edge["h"] == synth.HEIGHT


def test_soft_shadow_text_is_recovered(page, recovered):
    box = (40, 900, 480, 1280)  # lower-left, dimmed to ~35% but never clipped
    before = _f1(_bin(page.damaged), page.ink, box)
    after = _f1(_bin(recovered[0]), page.ink, box)
    assert before < 0.5 and after > 0.95


def test_text_in_glare_falloff_ring_survives(page, recovered):
    cx, cy = synth.GLARE_CENTER
    r0, r1 = page.glare_core_radius + 10, page.glare_core_radius + 60
    yy, xx = np.mgrid[0:synth.HEIGHT, 0:synth.WIDTH]
    d = np.hypot(xx - cx, yy - cy)
    ink = (page.ink > 0) & (d > r0) & (d < r1)
    assert np.count_nonzero((_bin(recovered[0]) > 0) & ink) / np.count_nonzero(ink) > 0.6


def test_text_under_clipped_glare_is_not_invented(page, recovered):
    """The honest limit: filling clipped pixels cannot bring the text back, and does not pretend to."""
    cx, cy = synth.GLARE_CENTER
    yy, xx = np.mgrid[0:synth.HEIGHT, 0:synth.WIDTH]
    core = (np.hypot(xx - cx, yy - cy) < page.glare_core_radius - 10) & (page.ink > 0)
    assert np.count_nonzero(core) > 500
    assert np.count_nonzero((_bin(recovered[0]) > 0) & core) < 0.05 * np.count_nonzero(core)
    assert recovered[1][cy, cx]  # and the mask says those pixels were synthesized


def test_edge_shadow_strip_left_alone(recovered):
    fixed, _, rep = recovered
    assert fixed[:, synth.EDGE_SHADOW_X + 5:].max() <= 5 and not rep["repair"]["shadow_filled"]


def test_reading_order_left_column_then_right(page):
    import cv2
    nodes = imaging.reading_order(cv2.cvtColor(page.clean, cv2.COLOR_GRAY2BGR))
    assert abs(len(nodes) - len(page.lines)) <= 3
    cols = ["title" if n["y"] < 110 else ("left" if n["x"] + n["w"] / 2 < 500 else "right") for n in nodes]
    body = [c for c in cols if c != "title"]
    k = body.index("right")
    assert all(c == "left" for c in body[:k]) and all(c == "right" for c in body[k:])


def test_large_photo_is_fast_enough():
    import time
    rng = np.random.default_rng(0)
    img = np.full((3000, 4000, 3), 200, np.uint8)
    img[rng.integers(0, 3000, 20000), rng.integers(0, 4000, 20000)] = 30
    t = time.perf_counter()
    imaging.recover(img)
    assert time.perf_counter() - t < 20
