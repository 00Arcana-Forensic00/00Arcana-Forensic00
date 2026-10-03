"""Package dist/store/Arcalume into an .msix for Microsoft Store submission (run on Windows).

    python packaging/windows/msix/build_msix.py --version 0.2.0.0

Reads IDENTITY_NAME, PUBLISHER and PUBLISHER_DISPLAY_NAME from the environment (copy
them from Partner Center). The Store re-signs the package, so it is left unsigned
here; sideloading it for testing needs a signature from a trusted certificate.
"""
import argparse
import glob
import os
import shutil
import string
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))


def makeappx() -> str:
    found = sorted(glob.glob(r"C:\Program Files (x86)\Windows Kits\10\bin\*\x64\makeappx.exe"))
    if not found:
        sys.exit("makeappx.exe not found: install the Windows 10/11 SDK")
    return found[-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True, help="four-part version, e.g. 0.2.0.0")
    a = ap.parse_args()
    values = {k: os.environ.get(k, "") for k in ("IDENTITY_NAME", "PUBLISHER", "PUBLISHER_DISPLAY_NAME")}
    missing = [k for k, v in values.items() if not v]
    if missing:
        sys.exit(f"set {', '.join(missing)} from Partner Center > Product identity")
    app = os.path.join(ROOT, "dist", "store", "Arcalume")
    if not os.path.isdir(app):
        sys.exit("build the store edition first: python packaging/build.py --edition store")
    stage = os.path.join(ROOT, "dist", "msix-stage")
    shutil.rmtree(stage, ignore_errors=True)
    shutil.copytree(app, os.path.join(stage, "Arcalume"))
    shutil.copytree(os.path.join(ROOT, "packaging", "icons", "store"), os.path.join(stage, "Assets"))
    tpl = string.Template(open(os.path.join(HERE, "AppxManifest.xml"), encoding="utf-8").read())
    with open(os.path.join(stage, "AppxManifest.xml"), "w", encoding="utf-8") as fh:
        fh.write(tpl.substitute(VERSION=a.version, **values))
    out = os.path.join(ROOT, "dist", f"Arcalume-{a.version}-store.msix")
    subprocess.check_call([makeappx(), "pack", "/o", "/d", stage, "/p", out])
    print(out)


if __name__ == "__main__":
    main()
