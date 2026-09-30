#!/usr/bin/env bash
# Per-user install of Arcalume: no root needed.
#   ./install.sh            install + app-menu entry
#   ./install.sh --desktop  also put a shortcut on the Desktop
#   ./install.sh --uninstall
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
BIN="${HOME}/.local/bin"
APPS="${HOME}/.local/share/applications"
ICON_DIR="${HOME}/.local/share/icons/hicolor/256x256/apps"
DESKTOP_FILE="${APPS}/arcalume.desktop"

if [[ "${1:-}" == "--uninstall" ]]; then
  rm -f "$BIN/Arcalume" "$BIN/arcana-restore" "$DESKTOP_FILE" "$ICON_DIR/arcalume.png"
  rm -f "$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")/arcalume.desktop"
  echo "Arcalume removed."; exit 0
fi

mkdir -p "$BIN" "$APPS" "$ICON_DIR"
install -m 0755 "$HERE/Arcalume" "$BIN/Arcalume"
install -m 0755 "$HERE/arcana-restore" "$BIN/arcana-restore"
install -m 0644 "$HERE/icon.png" "$ICON_DIR/arcalume.png"
cat > "$DESKTOP_FILE" <<DESK
[Desktop Entry]
Type=Application
Name=Arcalume
Comment=Recover documents damaged by glare and shadow
Exec=$BIN/Arcalume
Icon=arcalume
Terminal=false
Categories=Utility;Security;
DESK
chmod 0644 "$DESKTOP_FILE"

if [[ "${1:-}" == "--desktop" ]]; then
  D="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
  mkdir -p "$D"; cp "$DESKTOP_FILE" "$D/arcalume.desktop"; chmod +x "$D/arcalume.desktop"
fi
command -v update-desktop-database >/dev/null && update-desktop-database "$APPS" || true
echo "Installed. Find 'Arcalume' in your applications menu. (Command line: arcana-restore; ensure $BIN is on PATH.)"
