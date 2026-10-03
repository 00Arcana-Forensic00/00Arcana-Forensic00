"""Acquire -> triage -> repair -> seal -> record, for one file or a batch."""

from __future__ import annotations

import hashlib

import cv2
import json
import os
import re
import stat
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone

from . import __version__, imaging, vault, video
from .ledger import Ledger

LEDGER_NAME = "ledger.jsonl"
_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass
class Result:
    source: str
    ok: bool
    vault_path: str | None = None
    error: str | None = None
    report: dict = field(default_factory=dict)
    ms: float = 0.0


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_name(name: str) -> str:
    base = _SAFE.sub("_", os.path.basename(name)).strip("._") or "evidence"
    return base[:80]


def _refuse_link(path: str) -> None:
    """Reject symlinks and junctions explicitly. O_NOFOLLOW does not exist on Windows,
    so this check (not the open flag) is what protects there. A small check-then-open
    window remains; run on directories only trusted users can write to."""
    try:
        st = os.lstat(path)
    except OSError:
        return  # missing: the open below reports it
    is_junction = getattr(os.path, "isjunction", lambda p: False)(path)
    if stat.S_ISLNK(st.st_mode) or is_junction:
        raise imaging.ImageError("refusing to follow a symbolic link or junction")


def read_regular_file(path: str) -> bytes:
    """Read a regular file without following symlinks; size-capped."""
    _refuse_link(path)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise imaging.ImageError(f"cannot open (missing, unreadable or a symlink): {exc.strerror}") from None
    with os.fdopen(fd, "rb") as fh:
        if not stat.S_ISREG(os.fstat(fh.fileno()).st_mode):
            raise imaging.ImageError("not a regular file")
        data = fh.read(video.MAX_VIDEO_BYTES + 1)
    if len(data) > video.MAX_VIDEO_BYTES:
        raise imaging.ImageError("input exceeds the size limit (images 100 MiB, videos 250 MiB)")
    return data


def _write_new(path: str, data: bytes) -> None:
    """Durably write a new file (0600). Never replaces an existing vault."""
    tmp = f"{path}.{os.getpid()}.{os.urandom(4).hex()}.tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        try:
            os.link(tmp, path)  # atomic, and fails if the destination exists
        except FileExistsError:
            raise
        except OSError:
            # Filesystem without hard links (FAT/exFAT USB drives, some network shares):
            # fall back to exclusive create. Still never replaces an existing vault.
            fd2 = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd2, "wb") as fh:
                fh.write(data)
                fh.flush()
                os.fsync(fh.fileno())
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def _restore_video(original: bytes, cfg: imaging.RepairConfig):
    """Combine aligned frames to remove glare, then run the normal repair on what is left."""
    vcfg = video.VideoConfig()
    frames, _ = video.read_frames(original, vcfg)
    if not cfg.repair:  # triage-and-seal only: keep the sharpest frame untouched
        best = max(frames, key=video._sharpness)
        mask, report = imaging.triage(best, cfg)
        report.update({"source_kind": "video", "frames_sampled": len(frames), "frames_used": 1})
        report["status"] = "detected_not_repaired" if mask.any() else "stable"
        return best, mask, report
    comp, vmask, vreport = video.composite(frames, cfg, vcfg)
    mask2, report = imaging.triage(comp, cfg)
    restored = imaging.repair(comp, mask2, cfg, report)       # inpaint only what frames could not fix
    report.update(vreport)
    if vreport.get("composite_replaced_fraction", 0) > 0 and report["status"] == "stable":
        report["status"] = "repaired"
    return restored, cv2.bitwise_or(vmask, mask2), report


def process_file(path: str, vault_dir: str, passphrase: str, ledger: Ledger,
                 cfg: imaging.RepairConfig | None = None, kdf: dict | None = None) -> Result:
    t0 = time.perf_counter()
    try:
        original = read_regular_file(path)
    except (imaging.ImageError, OSError) as exc:
        ledger.append("rejected", {"source_sha256": None, "reason": str(exc)})
        return Result(path, False, None, str(exc), {}, (time.perf_counter() - t0) * 1000)
    res = process_bytes(os.path.basename(path), original, vault_dir, passphrase, ledger, cfg, kdf)
    res.source = path
    res.ms = (time.perf_counter() - t0) * 1000
    return res


def process_bytes(src_name: str, original: bytes, vault_dir: str, passphrase: str, ledger: Ledger,
                  cfg: imaging.RepairConfig | None = None, kdf: dict | None = None) -> Result:
    """Seal already-acquired bytes (the app hands over dropped files this way)."""
    cfg = cfg or imaging.RepairConfig()
    t0 = time.perf_counter()
    src_name = os.path.basename(src_name) or "evidence"
    src_hash = sha256(original)
    try:
        # No flat size check here: video.read_frames enforces its own 250 MiB cap and
        # imaging.decode_image enforces its own 100 MiB cap (MAX_INPUT_BYTES) — a blanket
        # 100 MiB check here would wrongly reject a valid 100-250 MiB video.
        if video.video_kind(original):
            restored, mask, report = _restore_video(original, cfg)
        else:
            img = imaging.decode_image(original)
            mask, report = imaging.triage(img, cfg)
            restored = imaging.repair(img, mask, cfg, report)
        nodes = imaging.reading_order(restored)
        report["reading_order_nodes"] = len(nodes)

        restored_png = imaging.encode_png(restored)
        mask_png = imaging.encode_png(mask)
        manifest = {
            "tool": f"arcana-restore {__version__}",
            "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source_name": src_name,
            "entries": {
                "original": {"sha256": src_hash, "size": len(original)},
                "restored": {"sha256": sha256(restored_png), "size": len(restored_png)},
                "mask": {"sha256": sha256(mask_png), "size": len(mask_png)},
            },
            "report": report,
            "reading_order": nodes,
            "settings": {"flatten": cfg.flatten, "fill_shadow": cfg.fill_shadow, "repair": cfg.repair},
            "notice": "restored is a derivative: lighting is corrected across the whole page and the "
                      "pixels marked in mask were synthesized by inpainting (they carry no original data). "
                      "original is byte-identical to the acquired source.",
        }
        blob = vault.seal(
            {
                "manifest": json.dumps(manifest, sort_keys=True).encode(),
                "original": original,
                "restored": restored_png,
                "mask": mask_png,
            },
            passphrase,
            kdf,
        )
        os.makedirs(vault_dir, mode=0o700, exist_ok=True)
        out = os.path.join(vault_dir, f"evidence-{src_hash[:16]}-{os.urandom(3).hex()}.arcr")  # no source name (it stays in the encrypted manifest); suffix keeps identical files as separate exhibits
        _write_new(out, blob)
        ledger.append("evidence_sealed", {
            "source_sha256": src_hash,
            "vault": os.path.basename(out),
            "vault_sha256": sha256(blob),
            "status": report["status"],
            "masked_fraction": report["masked_fraction"],
        })
        return Result(src_name, True, out, None, report, (time.perf_counter() - t0) * 1000)
    except FileExistsError:
        err = "a vault for this exact file already exists (refusing to overwrite)"
    except (imaging.ImageError, vault.VaultError, OSError) as exc:
        err = str(exc)
    ledger.append("rejected", {"source_sha256": src_hash, "reason": err})
    return Result(src_name, False, None, err, {}, (time.perf_counter() - t0) * 1000)


SUPPORTED = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp") + video.VIDEO_EXTS


def collect(paths: list[str], recursive: bool = False) -> list[str]:
    files: list[str] = []
    for p in paths:
        if os.path.isdir(p) and not os.path.islink(p):
            for root, dirs, names in os.walk(p, followlinks=False):
                files += [os.path.join(root, n) for n in sorted(names) if n.lower().endswith(SUPPORTED)]
                if not recursive:
                    break
        else:
            files.append(p)
    return files


def process_batch(files: list[str], vault_dir: str, passphrase: str, workers: int = 4,
                  cfg: imaging.RepairConfig | None = None, kdf: dict | None = None,
                  on_result=None) -> list[Result]:
    """Process files in parallel. ``on_result(result)`` is called as each one finishes."""
    os.makedirs(vault_dir, mode=0o700, exist_ok=True)
    ledger = Ledger(os.path.join(vault_dir, LEDGER_NAME))
    results: list[Result | None] = [None] * len(files)
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = {pool.submit(process_file, f, vault_dir, passphrase, ledger, cfg, kdf): i for i, f in enumerate(files)}
        for fut in as_completed(futures):
            res = fut.result()
            results[futures[fut]] = res
            if on_result:
                on_result(res)
    return results  # type: ignore[return-value]


def extract(vault_path: str, passphrase: str, out_dir: str, only: tuple[str, ...] = ("original", "restored", "mask", "manifest"),
            force: bool = False) -> list[str]:
    """Unseal, verify every entry against the manifest, write files with safe names."""
    blob = read_regular_file_any(vault_path)
    entries = vault.unseal(blob, passphrase)
    manifest = json.loads(entries["manifest"])
    for role, meta in manifest["entries"].items():
        if role in entries and sha256(entries[role]) != meta["sha256"]:
            raise vault.VaultError(f"integrity check failed for {role}")
    stem = safe_name(manifest["source_name"])
    ext = {"original": os.path.splitext(stem)[1] or ".bin", "restored": ".png", "mask": ".png", "manifest": ".json"}
    base = os.path.splitext(stem)[0]
    os.makedirs(out_dir, mode=0o700, exist_ok=True)
    plan = [(role, os.path.join(out_dir, f"{base}.{role}{ext[role]}")) for role in only if role in entries]
    for _, dest in plan:
        _refuse_link(dest)
        if not force and os.path.lexists(dest):
            raise FileExistsError(f"{os.path.basename(dest)} already exists; nothing was written")
    written = []
    for role, dest in plan:
        flags = os.O_WRONLY | os.O_CREAT | (os.O_TRUNC if force else os.O_EXCL) | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(dest, flags, 0o600)
        with os.fdopen(fd, "wb") as fh:
            fh.write(entries[role])
        written.append(dest)
    return written


def read_regular_file_any(path: str) -> bytes:
    try:
        _refuse_link(path)
    except imaging.ImageError as exc:
        raise vault.VaultError(str(exc)) from None
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise vault.VaultError(f"cannot open vault: {exc.strerror}") from None
    with os.fdopen(fd, "rb") as fh:
        return fh.read(vault.MAX_PLAINTEXT_BYTES + vault.MAX_HEADER_BYTES + 1024)
