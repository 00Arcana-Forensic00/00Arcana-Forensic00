"""Short-video input: remove glare by combining aligned frames.

Glare moves across a page as the camera moves, so a pixel blown out in one frame is usually
clean in others. We pick sharp frames, align them to a reference with a homography, and take
a per-pixel median that excludes clipped samples. Unlike inpainting this uses *real* pixels
from other frames. Anything still unrecoverable is left for the normal image repair.

The decoder (FFmpeg inside OpenCV) parses untrusted media: see docs/SECURITY.md.
"""

from __future__ import annotations

import os
import tempfile
import warnings
from dataclasses import dataclass

import cv2
import numpy as np

from .imaging import MAX_PIXELS, ImageError, RepairConfig

MAX_VIDEO_BYTES = 250 * 1024 * 1024
MAX_FRAMES_READ = 900        # stop decoding after this many frames
MAX_KEPT = 14                # frames kept for alignment
MAX_SIDE = 1920              # longest side after downscaling
MIN_USED = 3                 # frames (incl. reference) needed to composite
STRIP_ROWS = 64

VIDEO_EXTS = (".mp4", ".m4v", ".mov", ".avi", ".webm", ".mkv")


@dataclass(frozen=True)
class VideoConfig:
    max_kept: int = MAX_KEPT
    min_inliers: int = 25
    min_inlier_ratio: float = 0.4


def video_kind(data: bytes) -> str | None:
    """Return a file suffix for a recognised container, else None (magic bytes, not names)."""
    if data[:4] == b"\x1a\x45\xdf\xa3":
        return ".webm"                                   # WebM / Matroska
    if data[4:8] == b"ftyp":
        return ".mp4"                                    # MP4 / MOV / M4V
    if data[:4] == b"RIFF" and data[8:12] == b"AVI ":
        return ".avi"
    return None


def read_frames(data: bytes, cfg: VideoConfig) -> tuple[list[np.ndarray], int]:
    """Decode up to ``cfg.max_kept`` evenly spaced frames, downscaled. Returns (frames, total_read)."""
    kind = video_kind(data)
    if kind is None:
        raise ImageError("not a recognised video container")
    if len(data) > MAX_VIDEO_BYTES:
        raise ImageError("video exceeds the 250 MiB limit")
    # OpenCV decodes from a path only. The copy lives in a private (0700) temp dir, holds exactly
    # the bytes we hashed, and is removed before returning.
    with tempfile.TemporaryDirectory(prefix="arcana-") as tmp:
        path = os.path.join(tmp, "input" + kind)
        with open(path, "wb") as fh:
            fh.write(data)
        cap = cv2.VideoCapture(path)
        try:
            if not cap.isOpened():
                raise ImageError("video could not be opened (corrupt or unsupported codec)")
            count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            stride = max(1, count // cfg.max_kept) if count > 0 else 4
            kept, read = [], 0
            while read < MAX_FRAMES_READ and len(kept) < cfg.max_kept:
                ok, frame = cap.read()
                if not ok:
                    break
                if read % stride == 0:
                    h, w = frame.shape[:2]
                    if h * w > MAX_PIXELS * 4 or h < 16 or w < 16:
                        raise ImageError("video frame size is not supported")
                    scale = min(1.0, MAX_SIDE / max(h, w))
                    if scale < 1.0:
                        frame = cv2.resize(frame, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
                    kept.append(frame)
                read += 1
        finally:
            cap.release()
    if not kept:
        raise ImageError("no frames could be decoded from the video")
    return kept, read


def _sharpness(frame: np.ndarray) -> float:
    return float(cv2.Laplacian(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())


def _align(ref_gray, frame, cfg: VideoConfig, orb, matcher):
    """Homography taking ``frame`` onto the reference, or None if unreliable."""
    g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    k1, d1 = orb.detectAndCompute(ref_gray, None)
    k2, d2 = orb.detectAndCompute(g, None)
    if d1 is None or d2 is None or len(k1) < 40 or len(k2) < 40:
        return None
    pairs = matcher.knnMatch(d2, d1, k=2)
    good = [m for p in pairs if len(p) == 2 for m, n in [p] if m.distance < 0.75 * n.distance]
    if len(good) < cfg.min_inliers:
        return None
    src = np.float32([k2[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst = np.float32([k1[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    H, inl = cv2.findHomography(src, dst, cv2.RANSAC, 3.0)
    if H is None or inl is None:
        return None
    n_in = int(inl.sum())
    if n_in < cfg.min_inliers or n_in / len(good) < cfg.min_inlier_ratio:
        return None
    # Reject implausible warps (huge scale change, reflection, strong perspective).
    det = float(np.linalg.det(H[:2, :2]))
    if not (0.6 < det < 1.6) or abs(H[2, 0]) > 5e-3 or abs(H[2, 1]) > 5e-3:
        return None
    return H


def composite(frames: list[np.ndarray], rcfg: RepairConfig, cfg: VideoConfig):
    """Return (image, replaced_mask uint8 0/255, report) built from aligned frames."""
    sharp = [_sharpness(f) for f in frames]
    ref_i = int(np.argmax(sharp))
    ref = frames[ref_i]
    h, w = ref.shape[:2]
    ref_gray = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)
    orb = cv2.ORB_create(2000)
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING)

    warped, valid = [ref], [np.full((h, w), True)]
    for i, f in enumerate(frames):
        if i == ref_i:
            continue
        if f.shape[:2] != (h, w):
            f = cv2.resize(f, (w, h), interpolation=cv2.INTER_AREA)
        H = _align(ref_gray, f, cfg, orb, matcher)
        if H is None:
            continue
        wf = cv2.warpPerspective(f, H, (w, h), flags=cv2.INTER_LINEAR)
        ones = cv2.warpPerspective(np.full((h, w), 255, np.uint8), H, (w, h), flags=cv2.INTER_NEAREST)
        ones = cv2.erode(ones, np.ones((5, 5), np.uint8))   # drop interpolated borders
        warped.append(wf)
        valid.append(ones > 0)

    report = {
        "source_kind": "video",
        "frames_sampled": len(frames),
        "frames_used": len(warped),
        "reference_frame": ref_i,
    }
    if len(warped) < MIN_USED:
        report["video_fallback"] = "frames could not be aligned; used the sharpest single frame"
        return ref.copy(), np.zeros((h, w), np.uint8), report

    out = np.empty_like(ref)
    replaced = np.zeros((h, w), np.uint8)
    n = len(warped)
    for y0 in range(0, h, STRIP_ROWS):
        y1 = min(h, y0 + STRIP_ROWS)
        stack = np.stack([wf[y0:y1] for wf in warped]).astype(np.float32)       # n,rows,w,3
        vmask = np.stack([v[y0:y1] for v in valid])                              # n,rows,w
        gray = stack.mean(axis=3)
        clipped = ((gray >= rcfg.hi) | (gray <= rcfg.lo)) & vmask
        nvalid = vmask.sum(axis=0)
        frac = clipped.sum(axis=0) / np.maximum(nvalid, 1)
        # Drop clipped samples only where some frames disagree; a pixel clipped in every frame
        # (white paper) is legitimate and stays.
        drop = clipped & (frac < 1.0)[None]
        use = vmask & ~drop
        stack[~use] = np.nan
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)   # all-NaN pixels are handled just below
            med = np.nanmedian(stack, axis=0)
        none = ~use.any(axis=0)
        fix = drop[0] & ~none                                  # reference pixels that were clipped and have other data
        # Keep every clean reference pixel exactly as captured (no blur from small alignment errors);
        # replace only the clipped ones, which is also exactly what the mask records.
        out[y0:y1] = np.where(fix[..., None], np.clip(np.rint(med), 0, 255), ref[y0:y1]).astype(np.uint8)
        replaced[y0:y1] = fix.astype(np.uint8) * 255                              # warped[0] is the reference frame
    report["composite_replaced_fraction"] = round(float(np.count_nonzero(replaced)) / (h * w), 6)
    return out, replaced, report
