"""Triage and repair of lighting damage, using classical image processing.

What this can and cannot do:

* Uneven lighting that dims or brightens text without clipping it (soft
  shadows, the falloff around a glare spot) still holds the text signal.
  Dividing by an estimate of the page background ("flattening") recovers it,
  and a local contrast stretch around each glare spot recovers the washed-out
  ink in its falloff ring.
* Pixels clipped to pure white or pure black hold no information. Telea
  inpainting fills those regions with a smooth blend of their surroundings so
  they stop reading as structure, but it does not and cannot restore the
  characters that were there. Every filled region is listed in the report so
  the output is never mistaken for an unaltered capture.
* Large pure-black regions are often redaction bars, figures or scan borders,
  so they are reported but only filled when explicitly asked.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

import cv2
import numpy as np

GLARE_LEVEL = 250
SHADOW_LEVEL = 5
MAX_LISTED_REGIONS = 50


def _odd(n: float, minimum: int) -> int:
    n = max(int(round(n)), minimum)
    return n if n % 2 else n + 1


@dataclass
class Triage:
    clipped_glare_pixels: int
    clipped_shadow_pixels: int
    glare_mask: np.ndarray
    shadow_mask: np.ndarray
    paper_at_clip_level: bool
    glare_regions: List[Dict] = field(default_factory=list)
    shadow_regions: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        total = int(self.glare_mask.size)
        glare_area = int(np.count_nonzero(self.glare_mask))
        shadow_area = int(np.count_nonzero(self.shadow_mask))
        return {
            "total_pixels": total,
            "clipped_glare_pixels": self.clipped_glare_pixels,
            "clipped_shadow_pixels": self.clipped_shadow_pixels,
            "glare_region_pixels": glare_area,
            "shadow_region_pixels": shadow_area,
            "paper_at_clip_level": self.paper_at_clip_level,
            "glare_regions": self.glare_regions,
            "shadow_regions": self.shadow_regions,
            "status": "degraded" if glare_area or shadow_area else "stable",
        }


def _regions(mask: np.ndarray) -> List[Dict]:
    n, _, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    out = [
        {"x": int(s[0]), "y": int(s[1]), "w": int(s[2]), "h": int(s[3]), "area": int(s[4])}
        for s in stats[1:]
    ]
    out.sort(key=lambda r: r["area"], reverse=True)
    return out[:MAX_LISTED_REGIONS]


def triage(gray: np.ndarray) -> Triage:
    """Find clipped *regions*, not just clipped pixels.

    Dark text strokes are legitimately near 0 and clean white paper is
    legitimately near 255, so a per-pixel threshold flags the whole page.
    A morphological opening with a kernel wider than a text stroke keeps only
    blobs large enough to be lighting damage.
    """
    h, w = gray.shape
    raw_glare = (gray >= GLARE_LEVEL).astype(np.uint8) * 255
    raw_shadow = (gray <= SHADOW_LEVEL).astype(np.uint8) * 255
    # Glare needs the larger kernel: around a glare spot the paper between
    # surviving text lines is clipped too, and those strips must not be
    # mistaken for the dead core.
    kg = _odd(min(h, w) / 40, 7)
    ks = _odd(min(h, w) / 80, 7)
    glare = cv2.morphologyEx(raw_glare, cv2.MORPH_OPEN,
                             cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kg, kg)))
    shadow = cv2.morphologyEx(raw_shadow, cv2.MORPH_OPEN,
                              cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ks, ks)))

    # If the paper itself is at clip level, glare is indistinguishable from
    # clean paper and there is nothing to repair.
    paper_at_clip = float(np.median(gray)) >= GLARE_LEVEL
    if paper_at_clip:
        glare = np.zeros_like(glare)

    return Triage(
        clipped_glare_pixels=int(np.count_nonzero(raw_glare)),
        clipped_shadow_pixels=int(np.count_nonzero(raw_shadow)),
        glare_mask=glare,
        shadow_mask=shadow,
        paper_at_clip_level=paper_at_clip,
        glare_regions=_regions(glare),
        shadow_regions=_regions(shadow),
    )


def flatten_illumination(gray: np.ndarray) -> np.ndarray:
    """Divide out a smooth background estimate so paper becomes uniform white.

    The background is a grayscale closing (removes dark strokes narrower than
    the kernel) followed by a median blur. Dark areas larger than the kernel,
    such as big photos, are treated as background and will be washed out.
    """
    h, w = gray.shape
    k = _odd(min(h, w) / 25, 15)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    background = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
    background = cv2.medianBlur(background, _odd(k / 2, 5))
    bg = np.maximum(background.astype(np.float32), 1.0)
    flat = gray.astype(np.float32) * 255.0 / bg
    return np.clip(flat, 0, 255).astype(np.uint8)


def stretch_glare_halo(flat: np.ndarray, glare_mask: np.ndarray, min_contrast: int = 25) -> np.ndarray:
    """Restore contrast in the falloff ring around a glare spot.

    Glare adds light rather than scaling it, so after flattening the paper is
    white but the ink next to the spot is only slightly darker (e.g. 200 vs
    255). Inside a band around each glare core, stretch each neighbourhood's
    darkest level to black. Windows with less than ``min_contrast`` of range
    hold no ink and are left untouched, so paper noise is not amplified.
    """
    if not np.count_nonzero(glare_mask):
        return flat
    h, w = flat.shape
    side = min(h, w)
    halo_k = _odd(side / 7, 31)
    halo = cv2.dilate(glare_mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (halo_k, halo_k)))
    halo = cv2.bitwise_and(halo, cv2.bitwise_not(glare_mask))
    win = _odd(side / 16, 15)
    low = cv2.erode(flat, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (win, win)))
    blur = _odd(side / 32, 9)
    low = cv2.blur(low, (blur, blur)).astype(np.float32)
    span = 255.0 - low
    stretched = np.where(span >= min_contrast,
                         (flat.astype(np.float32) - low) * 255.0 / np.maximum(span, 1.0),
                         flat)
    stretched = np.clip(stretched, 0, 255).astype(np.uint8)
    return np.where(halo > 0, stretched, flat).astype(np.uint8)


def repair(gray: np.ndarray, report: Triage, fill_shadow: bool = False,
           inpaint_radius: int = 5) -> Dict:
    flat = stretch_glare_halo(flatten_illumination(gray), report.glare_mask)
    mask = report.glare_mask.copy()
    if fill_shadow:
        mask = cv2.bitwise_or(mask, report.shadow_mask)
    if np.count_nonzero(mask):
        # Grow the mask slightly so the fill starts from clean pixels, not the
        # anti-aliased rim of the clipped blob.
        mask = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
        repaired = cv2.inpaint(flat, mask, inpaint_radius, cv2.INPAINT_TELEA)
    else:
        repaired = flat
    return {
        "image": repaired,
        "inpainted_pixels": int(np.count_nonzero(mask)),
        "inpaint_method": "telea" if np.count_nonzero(mask) else None,
        "illumination_flattened": True,
        "glare_halo_stretched": bool(np.count_nonzero(report.glare_mask)),
        "shadow_regions_filled": bool(fill_shadow),
    }
