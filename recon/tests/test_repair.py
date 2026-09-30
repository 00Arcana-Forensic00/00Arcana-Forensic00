import numpy as np

from arcana_recon import repair, synth
from arcana_recon.layout import binarize


def _f1(pred, truth, box):
    x0, y0, x1, y1 = box
    a, b = pred[y0:y1, x0:x1] > 0, truth[y0:y1, x0:x1] > 0
    return 2 * np.count_nonzero(a & b) / (np.count_nonzero(a) + np.count_nonzero(b))


def test_clean_page_has_no_damage_regions(page):
    t = repair.triage(page.clean)
    assert t.to_dict()["status"] == "stable"


def test_text_strokes_and_white_paper_are_not_flagged():
    img = np.full((400, 400), 255, np.uint8)
    img[100:102, 50:350] = 0  # a thin black rule, like a text stroke
    t = repair.triage(img)
    assert t.paper_at_clip_level
    assert np.count_nonzero(t.glare_mask) == 0 and np.count_nonzero(t.shadow_mask) == 0


def test_triage_finds_glare_and_edge_shadow(page):
    t = repair.triage(page.damaged)
    cx, cy = synth.GLARE_CENTER
    big = t.glare_regions[0]
    assert big["x"] <= cx <= big["x"] + big["w"] and big["y"] <= cy <= big["y"] + big["h"]
    edge = t.shadow_regions[0]
    assert edge["x"] == synth.EDGE_SHADOW_X and edge["h"] == synth.HEIGHT


def test_soft_shadow_text_is_recovered(page):
    shadow_box = (40, 900, 480, 1280)  # lower-left, dimmed to ~35% but not clipped
    fixed = repair.repair(page.damaged, repair.triage(page.damaged))["image"]
    before = _f1(binarize(page.damaged), page.ink, shadow_box)
    after = _f1(binarize(fixed), page.ink, shadow_box)
    assert before < 0.5
    assert after > 0.95


def test_text_in_glare_falloff_ring_survives(page):
    cx, cy = synth.GLARE_CENTER
    r0, r1 = page.glare_core_radius + 10, page.glare_core_radius + 60
    yy, xx = np.mgrid[0:synth.HEIGHT, 0:synth.WIDTH]
    ring = (np.hypot(xx - cx, yy - cy) > r0) & (np.hypot(xx - cx, yy - cy) < r1)
    fixed = repair.repair(page.damaged, repair.triage(page.damaged))["image"]
    ink = (page.ink > 0) & ring
    recovered = (binarize(fixed) > 0) & ink
    assert np.count_nonzero(recovered) / np.count_nonzero(ink) > 0.6


def test_text_under_clipped_glare_is_not_recovered(page):
    """The honest limit: inpainting fills clipped pixels, it cannot bring text back."""
    cx, cy = synth.GLARE_CENTER
    r = page.glare_core_radius - 10
    yy, xx = np.mgrid[0:synth.HEIGHT, 0:synth.WIDTH]
    core = np.hypot(xx - cx, yy - cy) < r
    assert np.count_nonzero((page.ink > 0) & core) > 500  # there was text there
    fixed = repair.repair(page.damaged, repair.triage(page.damaged))["image"]
    assert np.count_nonzero((binarize(fixed) > 0) & core & (page.ink > 0)) < 0.05 * np.count_nonzero((page.ink > 0) & core)


def test_clipped_shadow_is_left_alone_unless_asked(page):
    t = repair.triage(page.damaged)
    kept = repair.repair(page.damaged, t)
    filled = repair.repair(page.damaged, t, fill_shadow=True)
    strip = (slice(None), slice(synth.EDGE_SHADOW_X + 5, None))
    assert kept["image"][strip].max() <= 5 and not kept["shadow_regions_filled"]
    assert filled["image"][strip].mean() > 100 and filled["shadow_regions_filled"]
