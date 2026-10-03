"""Block detection and reading order.

Blocks are found by dilating the binarized page so nearby glyphs merge, then
taking external contours. Reading order uses a recursive XY-cut: at each step
the block set is split at its single widest whitespace gap, either a vertical
gutter (columns) or a horizontal gap (rows), and each side is ordered in turn.
A plain (y, x) sort interleaves the lines of side-by-side columns; the XY-cut
reads a whole column before moving to the next.

Limits: this is geometry only. It does not read the text, so it cannot link a
footnote marker to its footnote, follow a wire in a schematic, or know that a
table continues across columns. Tables whose column gaps are wider than their
row gaps will be read column by column.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

Box = Tuple[int, int, int, int]  # x, y, w, h


def _odd(n: float, minimum: int) -> int:
    n = max(int(round(n)), minimum)
    return n if n % 2 else n + 1


def binarize(gray: np.ndarray) -> np.ndarray:
    """Ink = 255, paper = 0."""
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    return binary


def detect_blocks(binary: np.ndarray, min_area: Optional[int] = None) -> List[Box]:
    h, w = binary.shape
    kx = _odd(w / 100, 9)
    ky = _odd(h / 400, 3)
    dilated = cv2.dilate(binary, cv2.getStructuringElement(cv2.MORPH_RECT, (kx, ky)))
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if min_area is None:
        min_area = max(16, (h * w) // 200_000)
    boxes = []
    for c in contours:
        x, y, bw, bh = cv2.boundingRect(c)
        if bw > 0 and bh > 0 and bw * bh >= min_area:
            boxes.append((x, y, bw, bh))
    return boxes


def _widest_gap(boxes: List[Box], axis: int) -> Tuple[int, int]:
    """Return (gap_width, cut_position) of the widest empty band along an axis."""
    spans = sorted((b[axis], b[axis] + b[axis + 2]) for b in boxes)
    best = (0, 0)
    reach = spans[0][1]
    for start, end in spans[1:]:
        if start > reach and start - reach > best[0]:
            best = (start - reach, start)
        reach = max(reach, end)
    return best


def xy_cut(boxes: List[Box], min_col_gap: int = 1) -> List[Box]:
    if len(boxes) <= 1:
        return list(boxes)
    x_gap, x_cut = _widest_gap(boxes, 0)
    y_gap, y_cut = _widest_gap(boxes, 1)
    if x_gap < min_col_gap:
        x_gap = 0
    if x_gap == 0 and y_gap == 0:
        return sorted(boxes, key=lambda b: (b[1], b[0]))
    axis, cut = (0, x_cut) if x_gap >= y_gap else (1, y_cut)
    first = [b for b in boxes if b[axis] < cut]
    second = [b for b in boxes if b[axis] >= cut]
    return xy_cut(first, min_col_gap) + xy_cut(second, min_col_gap)


def naive_order(boxes: List[Box]) -> List[Box]:
    """The top-to-bottom, left-to-right sort the original drafts used."""
    return sorted(boxes, key=lambda b: (b[1], b[0]))


def map_layout(gray: np.ndarray) -> List[Dict]:
    binary = binarize(gray)
    boxes = detect_blocks(binary)
    ordered = xy_cut(boxes, min_col_gap=_odd(gray.shape[1] / 100, 9))
    nodes = []
    for i, (x, y, w, h) in enumerate(ordered):
        density = float(np.count_nonzero(binary[y:y + h, x:x + w])) / float(w * h)
        nodes.append({"order": i, "x": x, "y": y, "w": w, "h": h, "density": round(density, 4)})
    return nodes
