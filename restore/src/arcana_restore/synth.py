"""Synthetic damaged documents with known ground truth, for tests, demos and the in-app sample.

The page has a full-width title over two text columns. Damage applied:

* a soft shadow over the lower-left that dims but never clips (recoverable),
* a specular glare spot on the right column whose core clips to 255
  (text in the core is gone; text in its falloff ring is still there),
* a clipped-black strip down the right edge, like a scanner lid shadow.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import numpy as np

WIDTH, HEIGHT = 1000, 1300
PAPER, INK = 225, 35
LEFT_COL = (60, 470)
RIGHT_COL = (530, 900)
GLARE_CENTER = (715, 520)
GLARE_SIGMA = 60.0
GLARE_AMPLITUDE = 400.0
EDGE_SHADOW_X = 950

WORDS = (
    "ledger custody sealed exhibit invoice amount total account balance "
    "transfer ref date signed witness page section clause receipt serial "
    "batch report audit value net gross tax item unit rate"
).split()


@dataclass
class SynthPage:
    clean: np.ndarray      # undamaged page
    damaged: np.ndarray    # page with lighting damage
    ink: np.ndarray        # ground-truth ink mask (255 = ink) for the clean page
    lines: List[Dict]      # text lines in true reading order: {"column", "box"}
    glare_core_radius: float


def _line_text(rng: np.random.Generator, width_px: int, scale: float) -> str:
    words: List[str] = []
    while True:
        candidate = " ".join(words + [str(rng.choice(WORDS))])
        (w, _), _ = cv2.getTextSize(candidate, cv2.FONT_HERSHEY_SIMPLEX, scale, 1)
        if w > width_px:
            return " ".join(words) if words else candidate
        words = candidate.split(" ")


def _put(img: np.ndarray, text: str, org: Tuple[int, int], scale: float, thick: int) -> Tuple[int, int, int, int]:
    cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, scale, INK, thick, cv2.LINE_AA)
    (w, h), base = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thick)
    return (org[0], org[1] - h, w, h + base)


def make_page(seed: int = 7) -> SynthPage:
    rng = np.random.default_rng(seed)
    clean = np.full((HEIGHT, WIDTH), PAPER, np.uint8)
    lines: List[Dict] = []

    lines.append({"column": "title",
                  "box": _put(clean, "EXHIBIT 14 - RECONCILED LEDGER EXTRACT", (60, 80), 1.1, 2)})

    scale, line_h = 0.6, 30
    for column, (x0, x1) in (("left", LEFT_COL), ("right", RIGHT_COL)):
        y = 150
        # Different paragraph lengths per column so the columns' rows do not
        # line up perfectly, as in real two-column pages.
        paragraphs = [9, 7, 11, 6, 8] if column == "left" else [6, 10, 8, 9, 7]
        for n in paragraphs:
            for _ in range(n):
                if y > HEIGHT - 60:
                    break
                text = _line_text(rng, x1 - x0, scale)
                lines.append({"column": column, "box": _put(clean, text, (x0, y), scale, 1)})
                y += line_h
            y += 22

    ink = (clean < (PAPER + INK) // 2).astype(np.uint8) * 255

    yy, xx = np.mgrid[0:HEIGHT, 0:WIDTH].astype(np.float32)
    page = clean.astype(np.float32)

    # Soft shadow: multiplicative falloff to 35% in the lower-left, never clipping.
    d = np.clip(((HEIGHT - yy) / HEIGHT) * 1.6 + (xx / WIDTH) * 1.2 - 0.3, 0, 1)
    page *= 0.35 + 0.65 * d

    # Specular glare: additive Gaussian, clipped at 255 by the sensor.
    r2 = (xx - GLARE_CENTER[0]) ** 2 + (yy - GLARE_CENTER[1]) ** 2
    page += GLARE_AMPLITUDE * np.exp(-r2 / (2 * GLARE_SIGMA ** 2))

    # Hard shadow strip down the right edge, clipped to 0.
    page[:, EDGE_SHADOW_X:] = 0

    damaged = np.clip(page, 0, 255).astype(np.uint8)
    # Radius inside which even ink is pushed to 255 by the glare.
    core = GLARE_SIGMA * float(np.sqrt(2 * np.log(GLARE_AMPLITUDE / (255 - INK))))
    return SynthPage(clean=clean, damaged=damaged, ink=ink, lines=lines, glare_core_radius=core)


def write_samples(out_dir: Path, seed: int = 7) -> List[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    page = make_page(seed)
    paths = []
    for name, img in (("clean", page.clean), ("damaged", page.damaged), ("ink_truth", page.ink)):
        p = out_dir / f"synthetic_{name}.png"
        cv2.imwrite(str(p), img)
        paths.append(p)
    return paths
