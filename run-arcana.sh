#!/usr/bin/env bash
# Launcher for the arcana-acquire command-line tool (the Rust evidence acquirer).
# This is NOT the Arcana Restore desktop app; install that from the releases page.
# Usage:  ./run-arcana.sh <arcana-acquire arguments>     (run with bash, not python)
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN="$HERE/target/release/arcana-acquire"

if [[ ! -x "$BIN" ]]; then
  echo "arcana-acquire is not built yet. Build it first:" >&2
  echo "  cd \"$HERE\" && cargo build --release -p arcana-acquire" >&2
  exit 1
fi

exec "$BIN" "$@"
