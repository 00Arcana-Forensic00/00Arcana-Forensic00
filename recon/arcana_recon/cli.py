"""Command line: ``arcana-recon process|extract|synth``.

The passphrase comes from ``ARCANA_VAULT_PASSWORD`` (same variable as
``arcana-acquire``), ``--password``, or an interactive prompt, in that order
of preference for real use.
"""
from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from . import __version__
from .engine import extract, process_file
from .ingest import SUPPORTED_EXTENSIONS, InputRejected
from .synth import write_samples
from .vault import VaultError, check_passphrase

ENV_VAR = "ARCANA_VAULT_PASSWORD"


def _passphrase(explicit: Optional[str]) -> str:
    pw = explicit or os.environ.get(ENV_VAR)
    if not pw and sys.stdin.isatty():
        pw = getpass.getpass("Vault passphrase: ")
    if not pw:
        raise SystemExit(f"error: passphrase required via --password, {ENV_VAR}, or prompt")
    try:
        check_passphrase(pw)
    except VaultError as exc:
        raise SystemExit(f"error: {exc}")
    return pw


def collect_inputs(paths: List[Path]) -> List[Path]:
    files: List[Path] = []
    for p in paths:
        if p.is_dir():
            files.extend(sorted(
                f for f in p.iterdir()
                if f.is_file() and not f.is_symlink() and f.suffix.lower() in SUPPORTED_EXTENSIONS
            ))
        else:
            files.append(p)
    return files


def assign_output_names(files: List[Path], out_dir: Path) -> List[Tuple[Path, str]]:
    """Give every input a unique output stem up front, so parallel workers never collide."""
    taken = {f.name for f in out_dir.iterdir()} if out_dir.exists() else set()
    plan = []
    for f in files:
        stem, n = f.name, 1
        while f"{stem}.arcv" in taken or f"{stem}.json" in taken:
            stem = f"{f.name}-{n}"
            n += 1
        taken.update({f"{stem}.arcv", f"{stem}.json"})
        plan.append((f, stem))
    return plan


def cmd_process(args: argparse.Namespace) -> int:
    pw = _passphrase(args.password)
    out_dir = Path(args.out)
    files = collect_inputs([Path(p) for p in args.inputs])
    if not files:
        print("no supported images found", file=sys.stderr)
        return 1
    plan = assign_output_names(files, out_dir)
    workers = max(1, args.workers or min(8, os.cpu_count() or 2))
    failures = 0
    summary: List[Dict] = []
    # OpenCV releases the GIL, so threads overlap the image work. The
    # pure-Python key stretch does not, so very large batches are KDF-bound.
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(process_file, src, out_dir, pw, stem, args.fill_shadow): src
            for src, stem in plan
        }
        for fut in as_completed(futures):
            src = futures[fut]
            try:
                rep = fut.result()
            except (InputRejected, VaultError, OSError, ValueError) as exc:
                failures += 1
                print(f"REJECTED {src}: {exc}", file=sys.stderr)
                summary.append({"source": str(src), "ok": False, "error": str(exc)})
                continue
            tri = rep["triage"]
            print(f"SEALED   {src} -> {rep['output']['vault_file']} | "
                  f"glare {tri['glare_region_pixels']} px, shadow {tri['shadow_region_pixels']} px, "
                  f"{rep['layout']['node_count']} blocks, {rep['elapsed_ms']} ms")
            summary.append({"source": str(src), "ok": True, "vault": rep["output"]["vault_file"]})
    print(f"{len(files) - failures}/{len(files)} sealed into {out_dir}")
    if args.json:
        print(json.dumps(summary, indent=2))
    return 0 if failures == 0 else 2


def cmd_extract(args: argparse.Namespace) -> int:
    pw = _passphrase(args.password)
    vault_path = Path(args.vault)
    out = Path(args.out) if args.out else vault_path.with_suffix(".recovered.png")
    try:
        res = extract(vault_path, pw, out, report_path=args.report)
    except (VaultError, OSError, KeyError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    check = "verified against report" if res["report_verified"] else "no report found, hash not checked"
    print(f"extracted {vault_path} -> {res['out']} (sha256 {res['sha256']}, {check})")
    return 0


def cmd_synth(args: argparse.Namespace) -> int:
    for p in write_samples(Path(args.out), seed=args.seed):
        print(p)
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="arcana-recon", description=__doc__.splitlines()[0])
    ap.add_argument("--version", action="version", version=__version__)
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("process", help="repair images and seal them into a vault directory")
    p.add_argument("inputs", nargs="+", help="image files or directories")
    p.add_argument("--out", required=True, help="output directory for .arcv and .json files")
    p.add_argument("--password", help=f"vault passphrase (prefer {ENV_VAR})")
    p.add_argument("--workers", type=int, default=0, help="parallel workers (default: min(8, CPUs))")
    p.add_argument("--fill-shadow", action="store_true",
                   help="also inpaint large clipped-black regions (off by default: they are often redactions)")
    p.add_argument("--json", action="store_true", help="print a JSON summary at the end")
    p.set_defaults(func=cmd_process)

    e = sub.add_parser("extract", help="unseal a .arcv file to PNG and verify it against its report")
    e.add_argument("vault")
    e.add_argument("--out", help="output PNG path (default: <name>.recovered.png next to the vault)")
    e.add_argument("--report", help="report JSON (default: sidecar next to the vault)")
    e.add_argument("--password", help=f"vault passphrase (prefer {ENV_VAR})")
    e.set_defaults(func=cmd_extract)

    s = sub.add_parser("synth", help="write synthetic damaged test pages")
    s.add_argument("out")
    s.add_argument("--seed", type=int, default=7)
    s.set_defaults(func=cmd_synth)
    return ap


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
