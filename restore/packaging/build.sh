#!/usr/bin/env bash
# Build a single-file arcana-restore executable for the current OS/arch.
# Usage: packaging/build.sh   (run from anywhere; output in restore/dist/)
set -euo pipefail
cd "$(dirname "$0")/.."
python -m pip install -q -e . pyinstaller
rm -rf build dist
python -m PyInstaller --onefile --clean --noconfirm --name arcana-restore \
  --paths src packaging/entry.py
cd dist
if command -v sha256sum >/dev/null; then sha256sum arcana-restore* > SHA256SUMS
else shasum -a 256 arcana-restore* > SHA256SUMS; fi
cat SHA256SUMS
