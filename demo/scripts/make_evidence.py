#!/usr/bin/env python3
"""Recreate magic-byte sample files for the demo packs."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]

def write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    print(path.relative_to(ROOT), len(data))

def main() -> None:
    oss = ROOT / "demo/opensource/01-acquire/evidence"
    write(oss / "images/badge.png", bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]) + b"synthetic-oss-png-demo")
    write(oss / "archives/bundle.zip", b"PK\x03\x04" + b"\x14\x00" * 2 + b"synthetic-oss-zip-demo")
    trial = ROOT / "demo/trial/01-acquire-limited/evidence"
    write(trial / "inbox/shot.jpg", bytes([0xFF, 0xD8, 0xFF, 0xE0]) + b"synthetic-jpeg-trial")
    write(trial / "disk/payload.bin", bytes([0x7F, 0x45, 0x4C, 0x46]) + b"synthetic-elf-hint-not-a-real-binary")

if __name__ == "__main__":
    main()
