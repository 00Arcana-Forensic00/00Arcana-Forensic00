import cv2
import numpy as np
import pytest
from conftest import make_page
from arcana_restore import imaging


def test_glare_and_shadow_detected_and_repaired():
    img = make_page()
    cfg = imaging.RepairConfig()
    mask, rep = imaging.triage(img, cfg)
    assert rep["glare_pixels"] > 5000 and rep["shadow_pixels"] > 5000
    fixed = imaging.repair(img, mask, cfg, rep)
    assert rep["status"] == "repaired"
    g = cv2.cvtColor(fixed, cv2.COLOR_BGR2GRAY)
    assert g[300, 400] < 250            # glare centre no longer clipped
    assert (g[300, 400] > 150)          # filled with paper-like tone, not black
    assert (img[500, 100] == fixed[500, 100]).all()  # untouched pixels are identical


def test_ordinary_black_text_on_white_page_is_not_destroyed():
    img = np.full((400, 600, 3), 255, np.uint8)
    for y in range(40, 360, 30):
        cv2.putText(img, "EVIDENCE TEXT", (30, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    mask, rep = imaging.triage(img, imaging.RepairConfig())
    assert rep["white_page_detected"] and not mask.any()
    assert (imaging.repair(img, mask, imaging.RepairConfig(), rep) == img).all()


def test_extensive_damage_is_not_inpainted():
    img = np.full((400, 400, 3), 120, np.uint8)
    img[:, :200] = 255
    cfg = imaging.RepairConfig()
    mask, rep = imaging.triage(img, cfg)
    out = imaging.repair(img, mask, cfg, rep)
    assert rep["status"] == "skipped_damage_too_extensive" and (out == img).all()


def test_no_repair_flag_leaves_pixels():
    img = make_page()
    cfg = imaging.RepairConfig(repair=False)
    mask, rep = imaging.triage(img, cfg)
    assert (imaging.repair(img, mask, cfg, rep) == img).all() and rep["status"] == "detected_not_repaired"


def test_two_column_reading_order():
    nodes = imaging.reading_order(make_page(glare=False))
    assert nodes[0]["w"] > 400                       # heading first
    body = nodes[1:]
    left = [n for n in body if n["x"] < 300]
    right = [n for n in body if n["x"] >= 300]
    assert left and right
    assert max(n["order"] for n in left) < min(n["order"] for n in right)


@pytest.mark.parametrize("bad", [b"", b"MZ\x90\x00" + b"0" * 100, b"\x89PNG\r\n\x1a\n" + b"junk"])
def test_bad_inputs_rejected(bad):
    with pytest.raises(imaging.ImageError):
        imaging.decode_image(bad)


def test_oversize_and_pixel_bomb_rejected():
    with pytest.raises(imaging.ImageError):
        imaging.decode_image(b"\x89PNG\r\n\x1a\n" + b"0" * (imaging.MAX_INPUT_BYTES + 1))
    bomb = cv2.imencode(".png", np.zeros((12000, 12000), np.uint8))[1].tobytes()
    with pytest.raises(imaging.ImageError):
        imaging.decode_image(bomb)


def test_alpha_and_16bit_normalised():
    rgba = np.dstack([make_page()[:, :, :3], np.full((600, 800), 255, np.uint8)])
    assert imaging.decode_image(cv2.imencode(".png", rgba)[1].tobytes()).shape[2] == 3
    g16 = (np.random.default_rng(0).integers(0, 65535, (64, 64))).astype(np.uint16)
    assert imaging.decode_image(cv2.imencode(".png", g16)[1].tobytes()).dtype == np.uint8
