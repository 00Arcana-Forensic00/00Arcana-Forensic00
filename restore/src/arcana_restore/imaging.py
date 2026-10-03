"""Image decoding, clipped-region triage/repair and reading-order mapping.

Repair is *interpolation* (Telea inpainting), not recovery: filled pixels are plausible,
not original. The pipeline therefore always keeps the untouched original and a mask of
every synthesized pixel alongside the restored image.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

# Must be set before cv2 is imported: caps decoded pixels (decompression-bomb guard).
os.environ.setdefault("OPENCV_IO_MAX_IMAGE_PIXELS", str(100_000_000))

import cv2  # noqa: E402
import numpy as np  # noqa: E402

MAX_INPUT_BYTES = 100 * 1024 * 1024
MAX_PIXELS = 100_000_000
MAX_NODES = 5000

_MAGICS = (b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff", b"BM", b"II*\x00", b"MM\x00*")


class ImageError(ValueError):
    """Input rejected before or during decoding."""


@dataclass(frozen=True)
class RepairConfig:
    hi: int = 250              # pixels >= hi are candidate glare
    lo: int = 5                # pixels <= lo are candidate shadow
    glare_min_area: int = 64
    shadow_min_area: int = 2000  # keeps ordinary black text/lines out of the repair mask
    min_solidity: float = 0.35   # area / bounding box; rejects thin frames and rules
    dilate: int = 2
    inpaint_radius: int = 3
    max_masked_fraction: float = 0.30
    repair: bool = True


def decode_image(data: bytes) -> np.ndarray:
    """Validate magic bytes and size, decode to 8-bit BGR. Alpha is discarded."""
    if len(data) > MAX_INPUT_BYTES:
        raise ImageError("input exceeds the 100 MiB limit")
    if data[4:8] == b"ftyp" and data[8:12] in (b"heic", b"heix", b"heim", b"heis", b"hevc", b"hevx", b"mif1", b"msf1", b"avif", b"avis"):
        raise ImageError("HEIC/AVIF photos are not supported yet. In your photo app, export or share the photo as JPEG and add that.")
    if not data.startswith(_MAGICS):
        raise ImageError("Unsupported file type. Use a photo or screenshot (PNG, JPEG, TIFF, BMP) or a short video (MP4, MOV, AVI, WebM, MKV).")
    img = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ImageError("image could not be decoded (corrupt or truncated)")
    if img.dtype == np.uint16:
        img = (img >> 8).astype(np.uint8)
    elif img.dtype != np.uint8:
        raise ImageError(f"unsupported pixel type {img.dtype}")
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    elif img.shape[2] != 3:
        raise ImageError("unsupported channel count")
    h, w = img.shape[:2]
    if h < 8 or w < 8:
        raise ImageError("image too small")
    if h * w > MAX_PIXELS:
        raise ImageError("image exceeds the 100 megapixel limit")
    return img


def encode_png(img: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".png", img)
    if not ok:
        raise ImageError("PNG encoding failed")
    return buf.tobytes()


def _blobs(mask: np.ndarray, min_area: int, min_solidity: float) -> np.ndarray:
    """Keep only compact connected components of at least ``min_area`` pixels."""
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), connectivity=8)
    area = stats[:, cv2.CC_STAT_AREA]
    box = stats[:, cv2.CC_STAT_WIDTH].astype(np.int64) * stats[:, cv2.CC_STAT_HEIGHT]
    keep = (area >= min_area) & (area >= min_solidity * box)
    keep[0] = False
    return keep[labels]


def triage(img: np.ndarray, cfg: RepairConfig) -> tuple[np.ndarray, dict]:
    """Locate glare and shadow regions. Returns (repair_mask uint8 0/255, report)."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    white_page = float(np.median(gray)) >= cfg.hi  # paper is legitimately "clipped"
    glare = np.zeros(gray.shape, bool) if white_page else _blobs(gray >= cfg.hi, cfg.glare_min_area, cfg.min_solidity)
    shadow = _blobs(gray <= cfg.lo, cfg.shadow_min_area, cfg.min_solidity)
    mask = (glare | shadow).astype(np.uint8) * 255
    if cfg.dilate > 0 and mask.any():
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * cfg.dilate + 1,) * 2)
        mask = cv2.dilate(mask, k)
    total = gray.size
    report = {
        "width": int(gray.shape[1]),
        "height": int(gray.shape[0]),
        "white_page_detected": white_page,
        "glare_pixels": int(glare.sum()),
        "shadow_pixels": int(shadow.sum()),
        "masked_fraction": round(float(np.count_nonzero(mask)) / total, 6),
        "thresholds": {"hi": cfg.hi, "lo": cfg.lo},
    }
    return mask, report


def repair(img: np.ndarray, mask: np.ndarray, cfg: RepairConfig, report: dict) -> np.ndarray:
    """Inpaint the mask if repair is enabled and the damage is small enough to trust."""
    if not mask.any():
        report["status"] = "stable"
        return img.copy()
    if not cfg.repair:
        report["status"] = "detected_not_repaired"
        return img.copy()
    if report["masked_fraction"] > cfg.max_masked_fraction:
        report["status"] = "skipped_damage_too_extensive"
        return img.copy()
    report["status"] = "repaired"
    return cv2.inpaint(img, mask, cfg.inpaint_radius, cv2.INPAINT_TELEA)


def reading_order(img: np.ndarray) -> list[dict]:
    """Group text/figure blocks and order them: columns left to right, top to bottom.

    Full-width blocks (headings, wide tables) split the page into bands; within a band
    blocks are clustered into columns by horizontal overlap. This is a geometric
    heuristic, not semantic understanding.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    if np.count_nonzero(binary) > binary.size // 2:  # dark background: ink is the minority
        binary = cv2.bitwise_not(binary)
    h, w = binary.shape
    kern = cv2.getStructuringElement(cv2.MORPH_RECT, (max(3, w // 60), max(3, h // 200)))
    contours, _ = cv2.findContours(cv2.dilate(binary, kern), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    nodes = []
    for c in contours:
        x, y, bw, bh = cv2.boundingRect(c)
        area = bw * bh
        if area < 20:
            continue
        density = float(np.count_nonzero(binary[y : y + bh, x : x + bw])) / area
        nodes.append({"x": x, "y": y, "w": bw, "h": bh, "density": round(density, 4)})
    nodes.sort(key=lambda n: n["y"] * 1_000_000 + n["x"])
    nodes = nodes[:MAX_NODES]

    ordered, band = [], []

    def flush():
        cols: list[dict] = []
        for n in sorted(band, key=lambda n: n["x"]):
            for col in cols:
                overlap = min(n["x"] + n["w"], col["x1"]) - max(n["x"], col["x0"])
                if overlap > 0.5 * min(n["w"], col["x1"] - col["x0"]):
                    col["items"].append(n)
                    col["x0"], col["x1"] = min(col["x0"], n["x"]), max(col["x1"], n["x"] + n["w"])
                    break
            else:
                cols.append({"x0": n["x"], "x1": n["x"] + n["w"], "items": [n]})
        for col in sorted(cols, key=lambda c: c["x0"]):
            ordered.extend(sorted(col["items"], key=lambda n: n["y"]))
        band.clear()

    for n in nodes:
        if n["w"] >= 0.7 * w:
            flush()
            ordered.append(n)
        else:
            band.append(n)
    flush()
    for i, n in enumerate(ordered):
        n["order"] = i
    return ordered
