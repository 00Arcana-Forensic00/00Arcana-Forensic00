#!/usr/bin/env bash
# Per-user install of Arcana Restore: no root needed.
#   ./install.sh            install + app-menu entry
#   ./install.sh --desktop  also put a shortcut on the Desktop
#   ./install.sh --uninstall
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
BIN="${HOME}/.local/bin"
APPS="${HOME}/.local/share/applications"
ICON_DIR="${HOME}/.local/share/icons/hicolor/256x256/apps"
DESKTOP_FILE="${APPS}/arcana-restore.desktop"

if [[ "${1:-}" == "--uninstall" ]]; then
  rm -f "$BIN/ArcanaRestore" "$BIN/arcana-restore" "$DESKTOP_FILE" "$ICON_DIR/arcana-restore.png"
  rm -f "$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")/arcana-restore.desktop"
  echo "Arcana Restore removed."; exit 0
fi

mkdir -p "$BIN" "$APPS" "$ICON_DIR"
install -m 0755 "$HERE/ArcanaRestore" "$BIN/ArcanaRestore"
install -m 0755 "$HERE/arcana-restore" "$BIN/arcana-restore"
install -m 0644 "$HERE/icon.png" "$ICON_DIR/arcana-restore.png"
cat > "$DESKTOP_FILE" <<DESK
[Desktop Entry]
Type=Application
Name=Arcana Restore
Comment=Repair, seal and verify evidence images
Exec=$BIN/ArcanaRestore
Icon=arcana-restore
Terminal=false
Categories=Utility;Security;
DESK
chmod 0644 "$DESKTOP_FILE"

if [[ "${1:-}" == "--desktop" ]]; then
  D="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
  mkdir -p "$D"; cp "$DESKTOP_FILE" "$D/arcana-restore.desktop"; chmod +x "$D/arcana-restore.desktop"
fi
command -v update-desktop-database >/dev/null && update-desktop-database "$APPS" || true
echo "Installed. Find 'Arcana Restore' in your applications menu. (Command line: arcana-restore; ensure $BIN is on PATH.)"
