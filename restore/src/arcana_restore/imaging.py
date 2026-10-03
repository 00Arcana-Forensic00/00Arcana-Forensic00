"""Image decoding and the document recovery engine.

Recovery happens in three steps, in this order:

1. **Illumination flattening.** Divide each channel by a smooth estimate of the
   page background. Shadows and uneven light that *dim* text without clipping it
   still hold the text signal; flattening brings it back. This is the step that
   recovers text a user could not read before.
2. **Glare halo stretch.** Glare adds light, so after flattening the ink in the
   falloff ring around a glare spot is only slightly darker than paper. Inside
   that ring, each neighbourhood's darkest level is stretched back to ink.
3. **Inpainting of clipped glare cores** (Telea). Pixels clipped to pure white
   hold no data; they are filled with a smooth blend of their surroundings so they
   stop reading as structure. This does *not* bring back characters that were
   there, and every filled pixel is recorded in the mask.

Large pure-black regions are reported but left alone unless ``fill_shadow`` is
set, because they are often redaction bars, figures or scanner-lid shadows.

Reading order is a recursive XY-cut over detected blocks: a whole column is read
before the next one starts. It is geometry, not semantic understanding.

The engine was first developed as ``arcana-recon`` (see ``recon/`` on the
``claude/project-thread-oejael`` branch) and is merged here so the shipped app
has one engine.
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
MAX_LISTED_REGIONS = 50
_BACKGROUND_WORK_SIDE = 1200  # background is smooth; estimate it at this size and scale up

_MAGICS = (b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff", b"BM", b"II*\x00", b"MM\x00*")


class ImageError(ValueError):
    """Input rejected before or during decoding."""


@dataclass(frozen=True)
class RepairConfig:
    hi: int = 250              # pixels >= hi are candidate glare
    lo: int = 5                # pixels <= lo are candidate shadow
    inpaint_radius: int = 5
    max_masked_fraction: float = 0.30
    repair: bool = True        # False: triage and report only, pixels untouched
    flatten: bool = True       # divide out uneven lighting (recovers dimmed text)
    fill_shadow: bool = False  # also inpaint clipped-black regions (may be redactions)


def _odd(n: float, minimum: int) -> int:
    n = max(int(round(n)), minimum)
    return n if n % 2 else n + 1


def decode_image(data: bytes) -> np.ndarray:
    """Validate magic bytes and size, decode to 8-bit BGR. Alpha is discarded."""
    if len(data) > MAX_INPUT_BYTES:
        raise ImageError("input exceeds the 100 MiB limit")
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


# ---- triage ----------------------------------------------------------------------

def _regions(mask: np.ndarray) -> list[dict]:
    _, _, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    out = [{"x": int(s[0]), "y": int(s[1]), "w": int(s[2]), "h": int(s[3]), "area": int(s[4])} for s in stats[1:]]
    out.sort(key=lambda r: r["area"], reverse=True)
    return out[:MAX_LISTED_REGIONS]


def damage_masks(img: np.ndarray, cfg: RepairConfig) -> tuple[np.ndarray, np.ndarray, bool]:
    """Clipped glare and shadow *regions* (uint8 0/255), plus whether paper sits at clip level.

    Text strokes are legitimately near 0 and clean paper near 255, so a per-pixel
    threshold would flag the whole page. A morphological opening with a kernel wider
    than a text stroke keeps only blobs large enough to be lighting damage. Glare
    uses the larger kernel: around a glare spot the paper between surviving text
    lines is clipped too, and those strips are not the dead core.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    kg, ks = _odd(min(h, w) / 40, 7), _odd(min(h, w) / 80, 7)
    ell = cv2.MORPH_ELLIPSE
    glare = cv2.morphologyEx((gray >= cfg.hi).astype(np.uint8) * 255, cv2.MORPH_OPEN,
                             cv2.getStructuringElement(ell, (kg, kg)))
    shadow = cv2.morphologyEx((gray <= cfg.lo).astype(np.uint8) * 255, cv2.MORPH_OPEN,
                              cv2.getStructuringElement(ell, (ks, ks)))
    paper_at_clip = float(np.median(gray)) >= cfg.hi
    if paper_at_clip:  # glare is indistinguishable from clean white paper
        glare[:] = 0
    return glare, shadow, paper_at_clip


def triage(img: np.ndarray, cfg: RepairConfig) -> tuple[np.ndarray, dict]:
    """Locate damage. Returns (fill_mask uint8 0/255, report).

    ``fill_mask`` is exactly the set of pixels the repair will synthesize: glare
    cores, plus clipped-black regions only when ``fill_shadow`` is set.
    """
    glare, shadow, paper_at_clip = damage_masks(img, cfg)
    fill = glare.copy()
    if cfg.fill_shadow:
        fill = cv2.bitwise_or(fill, shadow)
    if fill.any():
        # Grow slightly so the fill starts from clean pixels, not the clipped rim.
        fill = cv2.dilate(fill, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    total = glare.size
    report = {
        "width": int(img.shape[1]),
        "height": int(img.shape[0]),
        "white_page_detected": paper_at_clip,
        "glare_pixels": int(np.count_nonzero(glare)),
        "shadow_pixels": int(np.count_nonzero(shadow)),
        "glare_regions": _regions(glare),
        "shadow_regions": _regions(shadow),
        "masked_fraction": round(float(np.count_nonzero(fill)) / total, 6),
        "thresholds": {"hi": cfg.hi, "lo": cfg.lo},
    }
    report["_glare_mask"] = glare  # internal, stripped before the report is serialized
    return fill, report


# ---- recovery --------------------------------------------------------------------

def _background(channel: np.ndarray) -> np.ndarray:
    """Smooth page-background estimate: grayscale closing removes dark strokes, then a median."""
    h, w = channel.shape
    scale = min(1.0, _BACKGROUND_WORK_SIDE / max(h, w))
    small = cv2.resize(channel, (max(1, round(w * scale)), max(1, round(h * scale))),
                       interpolation=cv2.INTER_AREA) if scale < 1 else channel
    k = _odd(min(small.shape) / 25, 15)
    bg = cv2.morphologyEx(small, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    bg = cv2.medianBlur(bg, _odd(k / 2, 5))
    if scale < 1:
        bg = cv2.resize(bg, (w, h), interpolation=cv2.INTER_LINEAR)
    return bg


def flatten_illumination(img: np.ndarray) -> np.ndarray:
    """Divide each channel by its background so paper becomes uniform and dimmed ink returns.

    Dark areas larger than about 4% of the page side (big photos) count as
    background and will be lightened.
    """
    out = np.empty_like(img)
    for c in range(img.shape[2]):
        ch = img[:, :, c]
        bg = np.maximum(_background(ch).astype(np.float32), 1.0)
        out[:, :, c] = np.clip(ch.astype(np.float32) * 255.0 / bg, 0, 255).astype(np.uint8)
    return out


def stretch_glare_halo(img: np.ndarray, glare: np.ndarray, min_contrast: int = 25) -> np.ndarray:
    """Restore contrast in the ring around each glare core.

    Windows with less than ``min_contrast`` of range hold no ink and are left
    alone, so paper noise is not amplified.
    """
    if not glare.any():
        return img
    side = min(img.shape[:2])
    # The ring is every pixel within side/14 of a glare core. A Euclidean distance
    # transform finds it in linear time; dilating with a kernel that large took most
    # of the run time on phone-camera-sized photos.
    radius = _odd(side / 7, 31) // 2
    dist = cv2.distanceTransform(cv2.bitwise_not(glare), cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
    halo = (dist <= radius) & (glare == 0)
    win, blur = _odd(side / 16, 15), _odd(side / 32, 9)
    out = img.copy()
    for c in range(img.shape[2]):
        ch = img[:, :, c]
        low = cv2.blur(cv2.erode(ch, cv2.getStructuringElement(cv2.MORPH_RECT, (win, win))), (blur, blur)).astype(np.float32)
        span = 255.0 - low
        st = np.where(span >= min_contrast, (ch.astype(np.float32) - low) * 255.0 / np.maximum(span, 1.0), ch)
        out[:, :, c] = np.where(halo, np.clip(st, 0, 255).astype(np.uint8), ch)
    return out


def repair(img: np.ndarray, mask: np.ndarray, cfg: RepairConfig, report: dict) -> np.ndarray:
    """Recover the page. Sets ``report['status']`` and ``report['repair']``.

    status: ``stable`` (nothing to do), ``enhanced`` (lighting corrected, nothing
    synthesized), ``repaired`` (lighting corrected and clipped regions filled),
    ``detected_not_repaired`` or ``skipped_damage_too_extensive`` (pixels untouched).
    """
    glare = report.pop("_glare_mask", None)
    if glare is None:
        glare = np.zeros(img.shape[:2], np.uint8)
    steps = {"illumination_flattened": False, "glare_halo_stretched": False,
             "inpainted_pixels": 0, "inpaint_method": None, "shadow_filled": False}
    report["repair"] = steps
    if not cfg.repair:
        report["status"] = "detected_not_repaired" if mask.any() or report.get("shadow_pixels") else "stable"
        return img.copy()
    if report["masked_fraction"] > cfg.max_masked_fraction:
        report["status"] = "skipped_damage_too_extensive"
        return img.copy()
    out = img
    if cfg.flatten:
        out = flatten_illumination(out)
        steps["illumination_flattened"] = True
    if glare.any():
        out = stretch_glare_halo(out, glare)
        steps["glare_halo_stretched"] = True
    if mask.any():
        out = cv2.inpaint(out, mask, cfg.inpaint_radius, cv2.INPAINT_TELEA)
        steps["inpainted_pixels"] = int(np.count_nonzero(mask))
        steps["inpaint_method"] = "telea"
        steps["shadow_filled"] = bool(cfg.fill_shadow and report.get("shadow_pixels"))
    if steps["inpainted_pixels"]:
        report["status"] = "repaired"
    elif not np.array_equal(out, img):
        report["status"] = "enhanced"
    else:
        report["status"] = "stable"
    return out if out is not img else img.copy()


def recover(img: np.ndarray, cfg: RepairConfig | None = None) -> tuple[np.ndarray, np.ndarray, dict]:
    """Triage + repair in one call. Returns (restored, fill_mask, report)."""
    cfg = cfg or RepairConfig()
    mask, report = triage(img, cfg)
    restored = repair(img, mask, cfg, report)
    return restored, mask, report


# ---- reading order ---------------------------------------------------------------

def _binarize(gray: np.ndarray) -> np.ndarray:
    """Ink = 255, paper = 0 (inverts dark-background pages)."""
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    if np.count_nonzero(binary) > binary.size // 2:
        binary = cv2.bitwise_not(binary)
    return binary


def _widest_gap(boxes, axis: int) -> tuple[int, int]:
    spans = sorted((b[axis], b[axis] + b[axis + 2]) for b in boxes)
    best, reach = (0, 0), spans[0][1]
    for start, end in spans[1:]:
        if start > reach and start - reach > best[0]:
            best = (start - reach, start)
        reach = max(reach, end)
    return best


def xy_cut(boxes, min_col_gap: int = 1):
    """Recursive XY-cut (iterative, so thousands of blocks cannot hit the recursion limit).

    At each step a vertical gutter at least ``min_col_gap`` wide that clears every
    block splits the set into columns; otherwise the widest horizontal gap splits
    it into rows. Each side is ordered in turn. Preferring gutters means columns
    whose line spacing is wider than their gutter are still read one at a time;
    the cost is that tables are read column by column.
    """
    out, stack = [], [list(boxes)]
    while stack:
        group = stack.pop()
        if len(group) <= 1:
            out.extend(group)
            continue
        x_gap, x_cut = _widest_gap(group, 0)
        y_gap, y_cut = _widest_gap(group, 1)
        if x_gap >= min_col_gap:      # a gutter that clears every block: finish columns first
            axis, cut = 0, x_cut
        elif y_gap > 0:
            axis, cut = 1, y_cut
        else:
            out.extend(sorted(group, key=lambda b: (b[1], b[0])))
            continue
        stack.append([b for b in group if b[axis] >= cut])  # popped second
        stack.append([b for b in group if b[axis] < cut])
    return out


def reading_order(img: np.ndarray) -> list[dict]:
    """Detect text/figure blocks and order them with XY-cut."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    binary = _binarize(gray)
    h, w = binary.shape
    kern = cv2.getStructuringElement(cv2.MORPH_RECT, (_odd(w / 100, 9), _odd(h / 400, 3)))
    contours, _ = cv2.findContours(cv2.dilate(binary, kern), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_area = max(16, (h * w) // 200_000)
    boxes = [b for b in (cv2.boundingRect(c) for c in contours) if b[2] * b[3] >= min_area]
    boxes = sorted(boxes, key=lambda b: b[2] * b[3], reverse=True)[:MAX_NODES]
    nodes = []
    for i, (x, y, bw, bh) in enumerate(xy_cut(boxes, min_col_gap=_odd(w / 100, 9))):
        density = float(np.count_nonzero(binary[y:y + bh, x:x + bw])) / (bw * bh)
        nodes.append({"order": i, "x": x, "y": y, "w": bw, "h": bh, "density": round(density, 4)})
    return nodes


# ---- presentation helpers (app previews and free-tier exports) --------------------

def fit(img: np.ndarray, max_w: int, max_h: int) -> np.ndarray:
    h, w = img.shape[:2]
    s = min(max_w / w, max_h / h, 1.0)
    return img if s >= 1.0 else cv2.resize(img, (max(1, int(w * s)), max(1, int(h * s))), interpolation=cv2.INTER_AREA)


def mask_overlay(img: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Hatch synthesized pixels in magenta (pattern, not colour alone) so they are easy to see."""
    out = img.copy()
    h, w = mask.shape
    yy, xx = np.mgrid[0:h, 0:w]
    stripe = ((xx + yy) // 4) % 2 == 0
    magenta = np.array([255, 0, 255], np.float32)
    for sel, a in (((mask > 0) & stripe, 0.85), ((mask > 0) & ~stripe, 0.35)):
        out[sel] = ((1 - a) * out[sel] + a * magenta).astype(np.uint8)
    return out


def watermark(img: np.ndarray, text: str) -> np.ndarray:
    """Diagonal repeated text across the image (free-tier exports)."""
    h, w = img.shape[:2]
    layer = np.zeros((h, w), np.uint8)
    scale = max(0.6, min(h, w) / 700)
    thick = max(1, int(scale * 2))
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thick)
    step_x, step_y = tw + int(80 * scale), th + int(140 * scale)
    for row, y in enumerate(range(th, h + step_y, step_y)):
        for x in range(-tw + (row % 2) * step_x // 2, w, step_x):
            cv2.putText(layer, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, 255, thick, cv2.LINE_AA)
    alpha = (layer.astype(np.float32) / 255.0 * 0.35)[:, :, None]
    color = np.array([60, 60, 200], np.float32)
    return (img.astype(np.float32) * (1 - alpha) + color * alpha).astype(np.uint8)
