"""Command line: process, extract, inspect, verify-ledger."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys

from . import __version__, pipeline, vault
from .imaging import RepairConfig
from .ledger import Ledger


def _passphrase(args, confirm: bool) -> str:
    """Never from argv (visible in process lists): file, env var, or prompt."""
    if args.passphrase_file:
        try:
            with open(args.passphrase_file, "r", encoding="utf-8") as fh:
                return fh.read().rstrip("\r\n")
        except (OSError, UnicodeDecodeError) as exc:
            print(f"cannot read the passphrase file: {getattr(exc, 'strerror', None) or exc}", file=sys.stderr)
            raise SystemExit(2)
    if os.environ.get("ARCANA_PASSPHRASE"):
        return os.environ["ARCANA_PASSPHRASE"]
    if not sys.stdin.isatty():
        raise SystemExit("no passphrase: use --passphrase-file, ARCANA_PASSPHRASE or a terminal")
    p = getpass.getpass("Vault passphrase: ")
    if confirm and getpass.getpass("Confirm passphrase: ") != p:
        raise SystemExit("passphrases do not match")
    return p


def _add_pass(p):
    p.add_argument("--passphrase-file", help="read the passphrase from this file (first line)")


def cmd_process(a) -> int:
    pw = _passphrase(a, confirm=True)
    if len(pw) < vault.MIN_PASSPHRASE_CHARS:
        print(f"passphrase must be at least {vault.MIN_PASSPHRASE_CHARS} characters", file=sys.stderr)
        return 2
    files = pipeline.collect(a.paths, a.recursive)
    if not files:
        print("no supported files found (PNG, JPEG, TIFF, BMP, MP4, MOV, AVI, WebM, MKV)", file=sys.stderr)
        return 2
    cfg = RepairConfig(repair=not a.no_repair, flatten=not a.no_flatten, fill_shadow=a.fill_shadow)
    results = pipeline.process_batch(files, a.vault, pw, a.workers, cfg)
    for r in results:
        name = os.path.basename(r.source)
        if r.ok:
            print(f"[ok]   {name} -> {os.path.basename(r.vault_path)}  {r.report['status']}  {r.ms:.0f} ms")
        else:
            print(f"[fail] {name}: {r.error}", file=sys.stderr)
    ok = sum(r.ok for r in results)
    ok_l, n, head, _ = Ledger(os.path.join(a.vault, pipeline.LEDGER_NAME)).verify()
    print(f"{ok}/{len(results)} sealed. Ledger head ({n} entries): {head}")
    return 0 if ok == len(results) else 1


def cmd_extract(a) -> int:
    pw = _passphrase(a, confirm=False)
    try:
        only = tuple(a.only) if a.only else ("original", "restored", "mask", "manifest")
        for p in pipeline.extract(a.vault_file, pw, a.out, only, a.force):
            print(f"wrote {p}")
        return 0
    except vault.VaultError as exc:           # wrong passphrase, not a vault, damaged vault
        print(f"[fail] {exc}", file=sys.stderr)
        return 2
    except (FileExistsError, OSError) as exc:  # output problems: file exists, no space, no permission
        print(f"[fail] {getattr(exc, 'strerror', None) or exc}" if not isinstance(exc, FileExistsError) else f"[fail] {exc}", file=sys.stderr)
        return 1


def cmd_gui(a) -> int:
    try:
        from . import gui
    except ImportError as exc:  # tkinter is a separate package on some Linux distributions
        print(f"the window needs Tk, which is not installed ({exc}). On Ubuntu/Debian: sudo apt install python3-tk",
              file=sys.stderr)
        return 1
    return gui.main()


def cmd_inspect(a) -> int:
    with open(a.vault_file, "rb") as fh:
        blob = fh.read(vault.MAX_HEADER_BYTES + 64)   # the header is all we need; never slurp a huge file
    header, _, _ = vault.parse_header(blob)
    header["kdf"].pop("salt", None)
    print(json.dumps(header, indent=2))
    return 0


def cmd_verify(a) -> int:
    ok, n, head, msg = Ledger(os.path.join(a.vault, pipeline.LEDGER_NAME)).verify(a.expect_head)
    print(f"{'VERIFIED' if ok else 'FAILED'}: {msg}; entries={n}; head={head}")
    return 0 if ok else 1


def cmd_license(a) -> int:
    from . import licensing
    if a.action == "activate":
        key = open(a.key_file, encoding="ascii").read() if a.key_file else (a.key or "")
        try:
            ent = licensing.activate(key)
        except licensing.LicenseError as exc:
            print(f"[fail] {exc}", file=sys.stderr)
            return 2
        print(f"Pro activated for {ent.licensee or 'this device'}")
        return 0
    if a.action == "remove":
        licensing.deactivate()
    print(json.dumps(licensing.current().to_dict(), indent=2))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="arcana-restore", description="Forensic document restoration with sealed vaults.")
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("process", help="repair and seal photos, screenshots or short videos (files or directories)")
    p.add_argument("paths", nargs="+")
    p.add_argument("-o", "--vault", default="./arcana_vault")
    p.add_argument("-r", "--recursive", action="store_true")
    p.add_argument("--workers", type=int, default=min(4, os.cpu_count() or 1))
    p.add_argument("--no-repair", action="store_true", help="triage and seal only; pixels untouched")
    p.add_argument("--fill-shadow", action="store_true", help="also fill clipped-black regions (may be redactions)")
    p.add_argument("--no-flatten", action="store_true", help="do not correct uneven lighting")
    _add_pass(p)
    p.set_defaults(fn=cmd_process)

    p = sub.add_parser("extract", help="decrypt and verify a vault")
    p.add_argument("vault_file")
    p.add_argument("-o", "--out", default="./arcana_out")
    p.add_argument("--only", nargs="+", choices=["original", "restored", "mask", "manifest"])
    p.add_argument("--force", action="store_true", help="overwrite existing output files")
    _add_pass(p)
    p.set_defaults(fn=cmd_extract)

    p = sub.add_parser("inspect", help="show vault header (no passphrase needed)")
    p.add_argument("vault_file")
    p.set_defaults(fn=cmd_inspect)

    p = sub.add_parser("verify-ledger", help="verify the custody hash chain")
    p.add_argument("--vault", default="./arcana_vault")
    p.add_argument("--expect-head", help="head hash recorded earlier; detects removed trailing entries")
    p.set_defaults(fn=cmd_verify)

    p = sub.add_parser("license", help="show, activate or remove the Arcalume license on this device")
    p.add_argument("action", choices=["status", "activate", "remove"])
    p.add_argument("key", nargs="?", help="license key (or use --key-file)")
    p.add_argument("--key-file")
    p.set_defaults(fn=cmd_license)

    p = sub.add_parser("app", help="open the Arcalume app window")
    p.set_defaults(fn=lambda a: __import__("arcana_restore.app.main", fromlist=["main"]).main())

    p = sub.add_parser("gui", help="open the classic (Tk) window")
    p.set_defaults(fn=lambda a: __import__("arcana_restore.gui", fromlist=["main"]).main())
    p = sub.add_parser("gui", help="open the desktop window")
    p.set_defaults(fn=cmd_gui)

    args = ap.parse_args(argv)
    try:
        return args.fn(args)
    except vault.VaultError as exc:
        print(f"[fail] {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"[fail] {exc.strerror or exc}" + (f": {exc.filename}" if exc.filename else ""), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("cancelled", file=sys.stderr)
        return 130
