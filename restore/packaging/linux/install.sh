#!/usr/bin/env bash
# Per-user install of Arcana Restore: no root needed.
#   ./install.sh             install + app-menu entry + Desktop icon
#   ./install.sh --no-desktop  skip the Desktop icon
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

for f in ArcanaRestore arcana-restore icon.png; do
  [[ -f "$HERE/$f" ]] || { echo "Missing $f next to install.sh. Run this from the extracted folder." >&2; exit 1; }
done
mkdir -p "$BIN" "$APPS" "$ICON_DIR"
install -m 0755 "$HERE/Arcalume" "$BIN/Arcalume"
install -m 0755 "$HERE/arcana-restore" "$BIN/arcana-restore"
install -m 0644 "$HERE/icon.png" "$ICON_DIR/arcalume.png"
cat > "$DESKTOP_FILE" <<DESK
[Desktop Entry]
Type=Application
Name=Arcana Restore
Comment=Repair, seal and verify evidence images
Exec="$BIN/ArcanaRestore"
Icon=arcana-restore
Terminal=false
Categories=Utility;Security;
DESK
chmod 0644 "$DESKTOP_FILE"

if [[ "${1:-}" != "--no-desktop" ]]; then
  D="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
  mkdir -p "$D"; cp "$DESKTOP_FILE" "$D/arcalume.desktop"; chmod +x "$D/arcalume.desktop"
fi
command -v update-desktop-database >/dev/null && update-desktop-database "$APPS" || true
echo "Installed. Find 'Arcalume' in your applications menu. (Command line: arcana-restore; ensure $BIN is on PATH.)"
  mkdir -p "$D"; cp "$DESKTOP_FILE" "$D/arcana-restore.desktop"; chmod +x "$D/arcana-restore.desktop"
  # GNOME shows desktop launchers as "untrusted" until allowed; mark ours trusted so one click works.
  command -v gio >/dev/null && gio set "$D/arcana-restore.desktop" metadata::trusted true 2>/dev/null || true
fi
if command -v update-desktop-database >/dev/null; then update-desktop-database "$APPS" 2>/dev/null || true; fi
case ":$PATH:" in *":$BIN:"*) ;; *) echo "Note: $BIN is not on your PATH, so the 'arcana-restore' command will not be found until you add it." ;; esac
echo "Installed. Find 'Arcana Restore' in your applications menu and on your Desktop (if the icon asks, right-click it and choose Allow Launching)."
