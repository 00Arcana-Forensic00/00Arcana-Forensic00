"""Build the executables for the current OS/arch into restore/dist/.

    python packaging/build.py

Produces `arcana-restore` (command line) and `ArcanaRestore` (windowed app, with icon),
plus SHA256SUMS. PyInstaller output is OS-specific: run this on each target OS.
"""
import hashlib
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ICONS = os.path.join(ROOT, "packaging", "icons")


def run(*cmd):
    print("+", " ".join(cmd), flush=True)
    subprocess.check_call(cmd, cwd=ROOT)


def main():
    run(sys.executable, "-m", "pip", "install", "-q", "-e", ".[gui]", "pyinstaller", "pillow")
    common = [sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", "--paths", "src"]
    icon = {"win32": "icon.ico", "darwin": "icon.icns"}.get(sys.platform, "icon.png")
    run(*common, "--onefile", "--name", "arcana-restore", "packaging/entry.py")
    gui = [*common, "--windowed", "--name", "ArcanaRestore", "--icon", os.path.join(ICONS, icon),
           "--add-data", f"src/arcana_restore/icon.png{os.pathsep}arcana_restore",
           "--collect-all", "tkinterdnd2", "--osx-bundle-identifier", "com.arcana-forensics.restore"]
    # macOS needs a .app bundle (onedir); elsewhere one file is easiest to hand out.
    gui += ["--onedir"] if sys.platform == "darwin" else ["--onefile"]
    run(*gui, "packaging/entry_gui.py")

    dist = os.path.join(ROOT, "dist")
    lines = []
    for name in sorted(os.listdir(dist)):
        path = os.path.join(dist, name)
        if os.path.isfile(path) and name != "SHA256SUMS":
            lines.append(f"{hashlib.sha256(open(path, 'rb').read()).hexdigest()}  {name}")
    open(os.path.join(dist, "SHA256SUMS"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
