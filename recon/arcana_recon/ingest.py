"""Input validation and decoding.

Files are read once into memory, checked against a size ceiling and a real
magic-number allow-list, then decoded from that buffer (never re-opened by
path), so the bytes that are hashed are the bytes that are processed.
"""
from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

MAX_FILE_BYTES = 50 * 1024 * 1024
MAX_PIXELS = 100_000_000

SUPPORTED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp")


class InputRejected(Exception):
    """The input is not a supported, well-formed image within limits."""


@dataclass
class LoadedImage:
    name: str
    raw_sha256: str
    raw_bytes: int
    format: str
    gray: np.ndarray  # uint8, 2-D


def sniff_format(data: bytes) -> Optional[str]:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if data[:4] in (b"II*\x00", b"MM\x00*"):
        return "tiff"
    if data.startswith(b"BM") and len(data) >= 26:
        return "bmp"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def _png_dimensions(data: bytes) -> Optional[tuple]:
    # IHDR is always the first chunk: 8-byte signature, 4 length, 4 type, then w, h.
    if len(data) >= 24 and data[12:16] == b"IHDR":
        return struct.unpack(">II", data[16:24])
    return None


def to_gray8(img: np.ndarray) -> np.ndarray:
    if img.dtype == np.uint16:
        img = (img >> 8).astype(np.uint8)
    elif img.dtype != np.uint8:
        img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    if img.ndim == 2:
        return img.copy()
    channels = img.shape[2]
    if channels == 1:
        return img[:, :, 0].copy()
    if channels == 4:
        return cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def load_bytes(data: bytes, name: str, max_bytes: int = MAX_FILE_BYTES,
               max_pixels: int = MAX_PIXELS) -> LoadedImage:
    if len(data) > max_bytes:
        raise InputRejected(f"{len(data)} bytes exceeds the {max_bytes}-byte limit")
    fmt = sniff_format(data)
    if fmt is None:
        raise InputRejected("not a PNG, JPEG, TIFF, BMP or WebP file (magic bytes do not match)")
    if fmt == "png":
        dims = _png_dimensions(data)
        if dims is None:
            raise InputRejected("PNG header is missing its IHDR chunk")
        if dims[0] * dims[1] > max_pixels:
            raise InputRejected(f"{dims[0]}x{dims[1]} exceeds the {max_pixels}-pixel limit")
    decoded = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if decoded is None or decoded.size == 0:
        raise InputRejected(f"{fmt} data could not be decoded (truncated or corrupt)")
    if decoded.shape[0] * decoded.shape[1] > max_pixels:
        raise InputRejected("decoded image exceeds the pixel limit")
    return LoadedImage(
        name=name,
        raw_sha256=hashlib.sha256(data).hexdigest(),
        raw_bytes=len(data),
        format=fmt,
        gray=to_gray8(decoded),
    )


def load_path(path: Path, max_bytes: int = MAX_FILE_BYTES) -> LoadedImage:
    path = Path(path)
    if not path.is_file() or path.is_symlink():
        raise InputRejected(f"{path} is not a regular file")
    if path.stat().st_size > max_bytes:
        raise InputRejected(f"{path.stat().st_size} bytes exceeds the {max_bytes}-byte limit")
    return load_bytes(path.read_bytes(), path.name, max_bytes=max_bytes)
