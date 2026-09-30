"""Smoke-test a built executable: seal, extract, verify, and reject a wrong passphrase.

Usage: python packaging/smoke.py dist/arcana-restore[.exe]
"""
import os
import subprocess
import sys
import tempfile

import cv2
import numpy as np


def run(exe, *args, expect=0):
    p = subprocess.run([exe, *args], capture_output=True, text=True)
    if p.returncode != expect:
        sys.exit(f"FAIL {args[0]}: exit {p.returncode} (expected {expect})\n{p.stdout}\n{p.stderr}")
    return p


def main(exe):
    exe = os.path.abspath(exe)
    with tempfile.TemporaryDirectory() as t:
        img = np.full((300, 400, 3), 200, np.uint8)
        cv2.rectangle(img, (20, 20), (380, 40), (40, 40, 40), -1)
        cv2.circle(img, (200, 150), 40, (255, 255, 255), -1)  # glare
        src = os.path.join(t, "scan.png")
        cv2.imwrite(src, img)
        good, bad = os.path.join(t, "pw"), os.path.join(t, "bad")
        open(good, "w").write("smoke test passphrase 123")
        open(bad, "w").write("not the right passphrase")
        vault = os.path.join(t, "v")
        run(exe, "--version")
        run(exe, "process", src, "-o", vault, "--passphrase-file", good)
        arcr = [os.path.join(vault, f) for f in os.listdir(vault) if f.endswith(".arcr")][0]
        out = os.path.join(t, "o")
        run(exe, "extract", arcr, "-o", out, "--passphrase-file", good)
        if open(os.path.join(out, "scan.original.png"), "rb").read() != open(src, "rb").read():
            sys.exit("FAIL: extracted original differs from source")
        run(exe, "verify-ledger", "--vault", vault)
        run(exe, "extract", arcr, "-o", os.path.join(t, "o2"), "--passphrase-file", bad, expect=2)
    print("smoke test passed")


if __name__ == "__main__":
    main(sys.argv[1])
