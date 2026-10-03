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
        with open(args.passphrase_file, "r", encoding="utf-8") as fh:
            return fh.read().rstrip("\r\n")
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
    cfg = RepairConfig(repair=not a.no_repair)
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
    except vault.AuthError as exc:
        print(f"[fail] {exc}", file=sys.stderr)
        return 2
    except (vault.VaultError, FileExistsError, OSError) as exc:
        print(f"[fail] {exc}", file=sys.stderr)
        return 1


def cmd_inspect(a) -> int:
    with open(a.vault_file, "rb") as fh:
        blob = fh.read()
    header, _, _ = vault.parse_header(blob)
    header["kdf"].pop("salt", None)
    print(json.dumps(header, indent=2))
    return 0


def cmd_verify(a) -> int:
    ok, n, head, msg = Ledger(os.path.join(a.vault, pipeline.LEDGER_NAME)).verify(a.expect_head)
    print(f"{'VERIFIED' if ok else 'FAILED'}: {msg}; entries={n}; head={head}")
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="arcana-restore", description="Forensic document restoration with sealed vaults.")
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("process", help="repair and seal photos, screenshots or short videos (files or directories)")
    p.add_argument("paths", nargs="+")
    p.add_argument("-o", "--vault", default="./arcana_vault")
    p.add_argument("-r", "--recursive", action="store_true")
    p.add_argument("--workers", type=int, default=min(4, os.cpu_count() or 1))
    p.add_argument("--no-repair", action="store_true", help="triage and seal only; do not inpaint")
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

    p = sub.add_parser("gui", help="open the desktop window")
    p.set_defaults(fn=lambda a: __import__("arcana_restore.gui", fromlist=["main"]).main())

    args = ap.parse_args(argv)
    try:
        return args.fn(args)
    except vault.VaultError as exc:
        print(f"[fail] {exc}", file=sys.stderr)
        return 2
