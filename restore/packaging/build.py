"""Build the executables for the current OS/arch into restore/dist/.

    python packaging/build.py [--edition direct|store]

Produces ``Arcalume`` (the app window, with icon), ``arcana-restore`` (command line)
and SHA256SUMS. ``--edition store`` builds the app-store variant (payment handled by
the store, Pro unlocked, no command-line tool). PyInstaller output is OS-specific:
run this on each target OS.
"""
import argparse
import hashlib
import os
import shutil
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ICONS = os.path.join(ROOT, "packaging", "icons")
EDITION_PY = os.path.join(ROOT, "src", "arcana_restore", "edition.py")
BUNDLE_ID = "com.arcanaforensics.arcalume"


def run(*cmd):
    print("+", " ".join(cmd), flush=True)
    subprocess.check_call(cmd, cwd=ROOT)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edition", choices=["direct", "store"], default="direct")
    ap.add_argument("--skip-install", action="store_true")
    a = ap.parse_args()
    if not a.skip_install:
        extra = "app,gui" if sys.platform != "linux" else "app"
        run(sys.executable, "-m", "pip", "install", "-q", "-e", f".[{extra}]", "pyinstaller", "pillow")
    original = open(EDITION_PY, encoding="utf-8").read()
    try:
        if a.edition == "store":
            with open(EDITION_PY, "w", encoding="utf-8") as fh:
                fh.write(original.replace('EDITION = "direct"', 'EDITION = "store"'))
        common = [sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", "--paths", "src"]
        if a.edition == "direct":
            run(*common, "--onefile", "--name", "arcana-restore", "packaging/entry.py")
        icon = {"win32": "icon.ico", "darwin": "icon.icns"}.get(sys.platform, "icon.png")
        app = [*common, "--windowed", "--name", "Arcalume", "--icon", os.path.join(ICONS, icon),
               "--add-data", f"src/arcana_restore/app/web{os.pathsep}arcana_restore/app/web",
               "--add-data", f"src/arcana_restore/icon.png{os.pathsep}arcana_restore",
               "--collect-submodules", "webview", "--collect-data", "webview", "--osx-bundle-identifier", BUNDLE_ID]
        # macOS needs a .app bundle and MSIX needs a folder: onedir. Linux: one file is easiest to hand out.
        app += ["--onefile"] if sys.platform == "linux" else ["--onedir"]
        run(*app, "packaging/entry_app.py")
    finally:
        with open(EDITION_PY, "w", encoding="utf-8") as fh:
            fh.write(original)

    dist = os.path.join(ROOT, "dist")
    if a.edition == "store":
        # keep store output apart so it is never shipped as the direct download
        for name in ("Arcalume", "Arcalume.app"):
            src = os.path.join(dist, name)
            if os.path.exists(src):
                dst = os.path.join(dist, "store", name)
                shutil.rmtree(dst, ignore_errors=True)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.move(src, dst)
    lines = []
    for name in sorted(os.listdir(dist)):
        path = os.path.join(dist, name)
        if os.path.isfile(path) and name != "SHA256SUMS":
            lines.append(f"{hashlib.sha256(open(path, 'rb').read()).hexdigest()}  {name}")
    open(os.path.join(dist, "SHA256SUMS"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
