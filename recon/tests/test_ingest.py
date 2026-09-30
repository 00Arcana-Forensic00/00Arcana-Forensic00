import cv2
import numpy as np
import pytest

from arcana_recon.ingest import InputRejected, load_bytes, load_path


def _png(img):
    return cv2.imencode(".png", img)[1].tobytes()


def test_accepts_png_and_records_hash():
    img = load_bytes(_png(np.full((20, 30), 128, np.uint8)), "a.png")
    assert img.format == "png" and img.gray.shape == (20, 30) and len(img.raw_sha256) == 64


@pytest.mark.parametrize("ext,fmt", [(".jpg", "jpeg"), (".tiff", "tiff"), (".bmp", "bmp"), (".webp", "webp")])
def test_accepts_other_formats(ext, fmt):
    data = cv2.imencode(ext, np.full((16, 16, 3), 90, np.uint8))[1].tobytes()
    img = load_bytes(data, "x" + ext)
    assert img.format == fmt and img.gray.ndim == 2


def test_converts_color_alpha_and_16bit():
    bgra = np.zeros((8, 8, 4), np.uint8)
    assert load_bytes(_png(bgra), "a.png").gray.shape == (8, 8)
    deep = np.full((8, 8), 65535, np.uint16)
    assert load_bytes(_png(deep), "d.png").gray.max() == 255


def test_rejects_non_image_with_image_extension(tmp_path):
    p = tmp_path / "invoice.png"
    p.write_bytes(b"MZ\x90\x00 this is not an image")
    with pytest.raises(InputRejected, match="magic"):
        load_path(p)


def test_rejects_truncated_image():
    data = _png(np.random.default_rng(0).integers(0, 255, (64, 64), dtype=np.uint8))
    with pytest.raises(InputRejected, match="decoded"):
        load_bytes(data[: len(data) // 2], "cut.png")


def test_rejects_oversize_file():
    with pytest.raises(InputRejected, match="limit"):
        load_bytes(_png(np.zeros((10, 10), np.uint8)), "a.png", max_bytes=10)


def test_rejects_pixel_bomb_before_decoding():
    header = bytearray(_png(np.zeros((4, 4), np.uint8)))
    header[16:24] = (100_000).to_bytes(4, "big") * 2  # claim 100000 x 100000
    with pytest.raises(InputRejected, match="pixel limit"):
        load_bytes(bytes(header), "bomb.png")


def test_rejects_symlink(tmp_path):
    real = tmp_path / "real.png"
    real.write_bytes(_png(np.zeros((4, 4), np.uint8)))
    link = tmp_path / "link.png"
    link.symlink_to(real)
    with pytest.raises(InputRejected, match="regular file"):
        load_path(link)
