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

        # Video: the bundled decoder must work inside the packaged app (moving glare across frames).
        vid = os.path.join(t, "clip.avi")
        w = cv2.VideoWriter(vid, cv2.VideoWriter_fourcc(*"MJPG"), 10, (400, 300))
        if w.isOpened():
            rng = np.random.default_rng(1)
            page = np.clip(np.full((260, 360, 3), 200) + rng.normal(0, 8, (260, 360, 3)), 0, 255).astype(np.uint8)
            for row in range(6):
                cv2.putText(page, f"EVIDENCE LINE {row*7}", (10, 30 + row * 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (30, 30, 30), 2)
            for i in range(10):
                f = np.full((300, 400, 3), 110, np.uint8)
                f[20 + i : 280 + i, 20 + i : 380 + i] = page
                cv2.circle(f, (60 + i * 30, 140), 35, (255, 255, 255), -1)
                w.write(f)
            w.release()
            vault2 = os.path.join(t, "v2")
            p = run(exe, "process", vid, "-o", vault2, "--passphrase-file", good)
            if "repaired" not in p.stdout:
                sys.exit(f"FAIL: video was not repaired in the packaged app\n{p.stdout}\n{p.stderr}")
        else:
            print("note: MJPG writer unavailable here, video smoke test skipped")
    print("smoke test passed")


if __name__ == "__main__":
    main(sys.argv[1])
