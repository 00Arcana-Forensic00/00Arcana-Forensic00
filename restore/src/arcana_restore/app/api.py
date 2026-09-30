"""The app's back end: everything the window can ask for, as JSON-safe methods.

The HTML front end calls these through pywebview's bridge (no network socket).
Nothing here touches the UI toolkit, so it is unit tested directly. Native file
dialogs are injected as callables so tests can run without a window.
"""

from __future__ import annotations

import base64
import os
import subprocess
import sys
import threading
import uuid
from dataclasses import dataclass, field
from typing import Callable

import cv2
import numpy as np

from .. import __version__, brand, imaging, licensing, pipeline, synth, vault
from ..ledger import Ledger

PREVIEW_MAX = (1600, 1600)
THUMB_MAX = (160, 200)
WATERMARK = "ARCALUME FREE PREVIEW"


class UserError(Exception):
    """A message meant for the user, shown as-is."""


@dataclass
class Doc:
    id: str
    name: str
    data: bytes
    image: np.ndarray
    options: dict = field(default_factory=dict)
    restored: np.ndarray | None = None
    mask: np.ndarray | None = None
    report: dict | None = None
    nodes: list | None = None


def _data_url(img: np.ndarray, max_wh=PREVIEW_MAX, fmt: str = ".jpg") -> str:
    small = imaging.fit(img, *max_wh)
    params = [cv2.IMWRITE_JPEG_QUALITY, 88] if fmt == ".jpg" else []
    ok, buf = cv2.imencode(fmt, small, params)
    if not ok:
        raise UserError("Could not render a preview.")
    mime = "image/jpeg" if fmt == ".jpg" else "image/png"
    return f"data:{mime};base64,{base64.b64encode(buf.tobytes()).decode()}"


def _pct(x: float) -> str:
    v = x * 100
    return f"{v:.1f}%" if v >= 0.1 or v == 0 else "under 0.1%"


def findings(report: dict, nodes: list, opts: dict) -> list[dict]:
    """Plain-language summary of what happened to a page. Each item has a level and text."""
    out = []
    steps = report.get("repair", {})
    status = report.get("status")
    if status == "skipped_damage_too_extensive":
        out.append({"level": "warn", "text": f"Over {_pct(0.30)} of the page is blown out, so nothing was changed. "
                    "Retake the photo at an angle to the light."})
    elif status == "detected_not_repaired":
        out.append({"level": "info", "text": "Repair is off: damage is reported, pixels are untouched."})
    if steps.get("illumination_flattened"):
        out.append({"level": "ok", "text": "Shadows and uneven lighting were evened out across the page."})
    g = len(report.get("glare_regions", []))
    if g:
        out.append({"level": "warn", "text": (
            f"{g} glare spot{'s' if g != 1 else ''} found. Faded text around {'them' if g != 1 else 'it'} was restored. "
            f"The blown-out centre ({_pct(report.get('masked_fraction', 0))} of the page) held no data and was "
            "filled smoothly. Text that was there cannot be recovered from this photo; "
            "turn on “Show filled areas” to see where.")})
    s = len(report.get("shadow_regions", []))
    if s and not steps.get("shadow_filled"):
        out.append({"level": "info", "text": (
            f"{s} solid black area{'s' if s != 1 else ''} left untouched. These are often redactions, "
            "photos or scanner edges. You can fill them if they are shadows.")})
    elif s:
        out.append({"level": "warn", "text": f"{s} solid black area{'s were' if s != 1 else ' was'} filled, as you asked."})
    if not g and not s and status in ("stable", "enhanced"):
        out.append({"level": "ok", "text": "No blown-out or blacked-out areas: nothing was invented."})
    if nodes:
        out.append({"level": "info", "text": f"Reading order mapped: {len(nodes)} text blocks."})
    return out


class Api:
    def __init__(self, dialogs: dict[str, Callable] | None = None, public_keys: list[str] | None = None):
        self._docs: dict[str, Doc] = {}
        self._lock = threading.Lock()
        self._dialogs = dialogs or {}
        self._public_keys = public_keys

    # ---- info / license
    def app_info(self) -> dict:
        ent = licensing.current(self._public_keys)
        return {"name": brand.APP_NAME, "tagline": brand.APP_TAGLINE, "version": __version__,
                "buy_url": brand.BUY_URL, "support_url": brand.SUPPORT_URL,
                "license": ent.to_dict(), "min_passphrase": vault.MIN_PASSPHRASE_CHARS,
                "defaults": {"vault_dir": os.path.join(os.path.expanduser("~"), "Arcalume Vault"),
                             "out_dir": os.path.join(os.path.expanduser("~"), "Arcalume Recovered")}}

    def activate_license(self, key: str) -> dict:
        try:
            return {"ok": True, "license": licensing.activate(key, self._public_keys).to_dict()}
        except licensing.LicenseError as exc:
            return {"ok": False, "error": str(exc)}

    def deactivate_license(self) -> dict:
        licensing.deactivate()
        return {"ok": True, "license": licensing.current(self._public_keys).to_dict()}

    def _ent(self) -> licensing.Entitlements:
        return licensing.current(self._public_keys)

    # ---- dialogs (native in the app, injected in tests)
    def _dialog(self, name: str, *args):
        fn = self._dialogs.get(name)
        return fn(*args) if fn else None

    def pick_images(self) -> dict:
        paths = self._dialog("open_images") or []
        return self.open_paths(list(paths))

    def pick_folder(self, purpose: str = "") -> str | None:
        return self._dialog("folder", purpose)

    def pick_vault_file(self) -> str | None:
        return self._dialog("open_vault")

    # ---- documents
    def _add(self, name: str, data: bytes) -> dict:
        img = imaging.decode_image(data)
        doc = Doc(uuid.uuid4().hex, os.path.basename(name) or "page", data, img)
        with self._lock:
            self._docs[doc.id] = doc
        h, w = img.shape[:2]
        return {"id": doc.id, "name": doc.name, "width": w, "height": h, "bytes": len(data),
                "thumb": _data_url(img, THUMB_MAX)}

    def open_paths(self, paths: list[str]) -> dict:
        added, errors = [], []
        for p in pipeline.collect(paths):
            try:
                added.append(self._add(p, pipeline.read_regular_file(p)))
            except (imaging.ImageError, OSError) as exc:
                errors.append({"name": os.path.basename(p), "error": str(exc)})
        return {"docs": added, "errors": errors}

    def open_bytes(self, name: str, b64: str) -> dict:
        try:
            data = base64.b64decode(b64, validate=True)
        except ValueError:
            return {"docs": [], "errors": [{"name": name, "error": "file could not be read"}]}
        try:
            return {"docs": [self._add(name, data)], "errors": []}
        except imaging.ImageError as exc:
            return {"docs": [], "errors": [{"name": os.path.basename(name), "error": str(exc)}]}

    def load_sample(self) -> dict:
        page = synth.make_page()
        return {"docs": [self._add("sample-damaged-page.png", imaging.encode_png(page.damaged))], "errors": []}

    def close_doc(self, doc_id: str) -> dict:
        with self._lock:
            self._docs.pop(doc_id, None)
        return {"ok": True}

    def _doc(self, doc_id: str) -> Doc:
        doc = self._docs.get(doc_id)
        if doc is None:
            raise UserError("That page is no longer open.")
        return doc

    def recover(self, doc_id: str, options: dict | None = None) -> dict:
        doc = self._doc(doc_id)
        opts = {"flatten": True, "fill_shadow": False, **(options or {})}
        cfg = imaging.RepairConfig(flatten=bool(opts["flatten"]), fill_shadow=bool(opts["fill_shadow"]))
        restored, mask, report = imaging.recover(doc.image, cfg)
        nodes = imaging.reading_order(restored)
        doc.options, doc.restored, doc.mask, doc.report, doc.nodes = opts, restored, mask, report, nodes
        h, w = doc.image.shape[:2]
        return {
            "id": doc.id, "name": doc.name, "width": w, "height": h, "options": opts,
            "before": _data_url(doc.image), "after": _data_url(restored),
            "overlay": _data_url(imaging.mask_overlay(restored, mask)),
            "status": report["status"], "findings": findings(report, nodes, opts),
            "stats": {"glare_regions": len(report["glare_regions"]), "shadow_regions": len(report["shadow_regions"]),
                      "filled_fraction": report["masked_fraction"], "blocks": len(nodes)},
            "reading_order": [{k: n[k] for k in ("order", "x", "y", "w", "h")} for n in nodes[:400]],
            "report": {k: v for k, v in report.items()},
        }

    # ---- outputs
    def export(self, doc_id: str, dest: str | None = None) -> dict:
        doc = self._doc(doc_id)
        if doc.restored is None:
            self.recover(doc_id)
        ent = self._ent()
        stem = os.path.splitext(pipeline.safe_name(doc.name))[0]
        if dest is None:
            dest = self._dialog("save_png", f"{stem}-restored.png")
            if not dest:
                return {"ok": False, "cancelled": True}
        if not dest.lower().endswith(".png"):
            dest += ".png"
        img = doc.restored if ent.clean_export else imaging.watermark(doc.restored, WATERMARK)
        data = imaging.encode_png(img)
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(dest, flags, 0o600)
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        return {"ok": True, "path": dest, "watermarked": not ent.clean_export, "sha256": pipeline.sha256(data)}

    def seal(self, doc_ids: list[str], vault_dir: str, passphrase: str, confirm: str) -> dict:
        ent = self._ent()
        if not ent.seal:
            return {"ok": False, "error": "Sealing into a vault is part of Pro.", "upgrade": True}
        if len(doc_ids) > 1 and not ent.batch:
            return {"ok": False, "error": "Sealing several pages at once is part of Pro.", "upgrade": True}
        if len(passphrase) < vault.MIN_PASSPHRASE_CHARS:
            return {"ok": False, "error": f"Use a passphrase of at least {vault.MIN_PASSPHRASE_CHARS} characters."}
        if passphrase != confirm:
            return {"ok": False, "error": "The two passphrases don't match."}
        if not vault_dir:
            return {"ok": False, "error": "Choose a vault folder."}
        os.makedirs(vault_dir, mode=0o700, exist_ok=True)
        ledger = Ledger(os.path.join(vault_dir, pipeline.LEDGER_NAME))
        results = []
        for did in doc_ids:
            doc = self._doc(did)
            o = doc.options or {}
            cfg = imaging.RepairConfig(flatten=o.get("flatten", True), fill_shadow=o.get("fill_shadow", False))
            r = pipeline.process_bytes(doc.name, doc.data, vault_dir, passphrase, ledger, cfg)
            results.append({"name": doc.name, "ok": r.ok, "vault": r.vault_path, "error": r.error})
        ok, n, head, _ = ledger.verify()
        return {"ok": all(r["ok"] for r in results), "results": results, "ledger_ok": ok,
                "ledger_entries": n, "ledger_head": head, "vault_dir": vault_dir}

    def open_vault(self, vault_file: str, passphrase: str, out_dir: str) -> dict:
        try:
            written = pipeline.extract(vault_file, passphrase, out_dir)
        except vault.AuthError:
            return {"ok": False, "error": "Wrong passphrase, or the file was changed after sealing."}
        except FileExistsError:
            return {"ok": False, "error": "Files from this vault already exist in that folder. Choose another folder."}
        except (vault.VaultError, OSError) as exc:
            return {"ok": False, "error": str(exc)}
        return {"ok": True, "written": written, "out_dir": out_dir}

    def verify_ledger(self, vault_dir: str, expect_head: str = "") -> dict:
        path = os.path.join(vault_dir or "", pipeline.LEDGER_NAME)
        if not os.path.isfile(path):
            return {"ok": False, "entries": 0, "head": "", "message": "No ledger found in that folder."}
        ok, n, head, msg = Ledger(path).verify(expect_head.strip() or None)
        return {"ok": ok, "entries": n, "head": head, "message": msg}

    def reveal(self, path: str) -> dict:
        try:
            if sys.platform == "win32":
                os.startfile(path)  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", path])
        except OSError:
            return {"ok": False}
        return {"ok": True}


def call(api: Api, method: str, args: list) -> dict:
    """Dispatch used by the test bridge: same surface pywebview exposes."""
    if method.startswith("_") or not callable(getattr(api, method, None)):
        return {"__error__": f"unknown method {method}"}
    try:
        return {"result": getattr(api, method)(*args)}
    except UserError as exc:
        return {"__error__": str(exc)}
    except imaging.ImageError as exc:
        return {"__error__": str(exc)}
