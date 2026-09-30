import cv2
import numpy as np
import pytest

FAST_KDF = {"name": "argon2id", "t": 1, "m_kib": 16384, "p": 1}
PW = "correct horse battery staple"


def make_page(glare=True, columns=2, size=(600, 800)):
    """Grey paper with dark text-like bars; optional 255 glare blob and 0 shadow blob."""
    h, w = size
    img = np.full((h, w, 3), 200, np.uint8)
    rng = np.random.default_rng(1)
    col_w = (w - 100) // columns
    for c in range(columns):
        x0 = 40 + c * (col_w + 20)
        for row in range(12):
            y = 120 + row * 40
            cv2.rectangle(img, (x0, y), (x0 + col_w - int(rng.integers(0, 30)), y + 14), (40, 40, 40), -1)
    cv2.rectangle(img, (40, 30), (w - 40, 70), (30, 30, 30), -1)  # full-width heading
    if glare:
        cv2.ellipse(img, (w // 2, 300), (60, 45), 0, 0, 360, (255, 255, 255), -1)
        cv2.rectangle(img, (w - 140, h - 140), (w - 40, h - 40), (0, 0, 0), -1)
    return img


@pytest.fixture
def png_bytes():
    return cv2.imencode(".png", make_page())[1].tobytes()


@pytest.fixture
def evidence(tmp_path):
    p = tmp_path / "in" / "receipt.png"
    p.parent.mkdir()
    p.write_bytes(cv2.imencode(".png", make_page())[1].tobytes())
    return p
