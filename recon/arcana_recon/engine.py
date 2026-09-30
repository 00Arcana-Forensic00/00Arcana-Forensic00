"""End-to-end pipeline: ingest, triage, repair, layout, seal.

For each input the engine writes two files into the output directory and
nothing else (the repaired image never touches disk unencrypted):

* ``<name>.arcv``: the repaired page as PNG, sealed in an ARCN v1 vault blob.
* ``<name>.json``: the report (hashes, triage, filled regions, layout nodes).
  The report is plaintext. It contains the source file name and page geometry
  but no pixel data and no key material.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Dict, Optional, Union

import cv2

from . import __version__, vault
from .ingest import InputRejected, LoadedImage, load_path
from .layout import map_layout
from .repair import repair, triage

REPORT_SCHEMA = "arcana-recon/report/v1"


def reconstruct(image: LoadedImage, passphrase: str, fill_shadow: bool = False) -> Dict:
    """Run the pipeline in memory. Returns the report plus the sealed blob."""
    started = time.perf_counter()
    tri = triage(image.gray)
    fixed = repair(image.gray, tri, fill_shadow=fill_shadow)
    nodes = map_layout(fixed["image"])

    ok, encoded = cv2.imencode(".png", fixed["image"])
    if not ok:
        raise RuntimeError("PNG encoding failed")
    png = encoded.tobytes()
    blob = vault.seal(png, passphrase)

    report = {
        "schema": REPORT_SCHEMA,
        "tool_version": __version__,
        "source": {
            "name": image.name,
            "format": image.format,
            "bytes": image.raw_bytes,
            "sha256": image.raw_sha256,
            "height": int(image.gray.shape[0]),
            "width": int(image.gray.shape[1]),
        },
        "triage": tri.to_dict(),
        "repair": {k: v for k, v in fixed.items() if k != "image"},
        "layout": {"reading_order": "xy-cut", "node_count": len(nodes), "nodes": nodes},
        "output": {
            "plaintext_format": "png",
            "plaintext_sha256": hashlib.sha256(png).hexdigest(),
            "vault_format": f"ARCN v{vault.VERSION}",
            "vault_kdf": vault.KDF_DESCRIPTION,
            "vault_cipher": "AES-256-GCM",
            "vault_sha256": hashlib.sha256(blob).hexdigest(),
        },
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
    }
    return {"report": report, "blob": blob}


def _write_exclusive(path: Path, data: bytes) -> None:
    # O_EXCL: never overwrite an existing vault or report.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(data)


def process_file(source: Union[str, Path], out_dir: Union[str, Path], passphrase: str,
                 output_name: Optional[str] = None, fill_shadow: bool = False) -> Dict:
    """Process one file and write ``<output_name>.arcv`` and ``<output_name>.json``."""
    source = Path(source)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    vault.check_passphrase(passphrase)

    image = load_path(source)
    result = reconstruct(image, passphrase, fill_shadow=fill_shadow)
    stem = output_name or source.name
    vault_path = out_dir / f"{stem}.arcv"
    report_path = out_dir / f"{stem}.json"
    report = result["report"]
    report["output"]["vault_file"] = vault_path.name
    _write_exclusive(vault_path, result["blob"])
    _write_exclusive(report_path, (json.dumps(report, indent=2) + "\n").encode("utf-8"))
    return report


def extract(vault_path: Union[str, Path], passphrase: str, out_path: Union[str, Path],
            report_path: Optional[Union[str, Path]] = None) -> Dict:
    """Unseal a vault blob to a PNG, verifying it against its report when present.

    Works in any process: only the passphrase is needed. The report defaults
    to the ``.json`` sidecar next to the vault.
    """
    vault_path = Path(vault_path)
    plaintext = vault.unseal(vault_path.read_bytes(), passphrase)
    digest = hashlib.sha256(plaintext).hexdigest()

    if report_path is None:
        candidate = vault_path.with_suffix(".json")
        report_path = candidate if candidate.exists() else None
    verified = None
    source_name = None
    if report_path is not None:
        report = json.loads(Path(report_path).read_text())
        expected = report["output"]["plaintext_sha256"]
        if digest != expected:
            raise vault.VaultError(
                f"plaintext hash {digest} does not match the report ({expected})")
        verified = True
        source_name = report["source"]["name"]

    if not plaintext.startswith(b"\x89PNG\r\n\x1a\n"):
        raise vault.VaultError("unsealed payload is not a PNG")
    _write_exclusive(Path(out_path), plaintext)
    return {"out": str(out_path), "sha256": digest, "report_verified": verified,
            "source_name": source_name}


__all__ = ["reconstruct", "process_file", "extract", "InputRejected"]
