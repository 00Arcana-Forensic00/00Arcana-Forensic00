"""Append-only, SHA-256 hash-chained custody ledger (JSON Lines).

Each entry commits to the previous entry's hash, so editing, reordering or deleting a
line in the middle breaks verification. A chain alone cannot prove that *trailing*
entries were not removed: record ``head`` externally (or anchor it) and pass it to
``verify(expect_head=...)``.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
from datetime import datetime, timezone

try:  # POSIX cross-process lock
    import fcntl
except ImportError:  # pragma: no cover - Windows
    fcntl = None

GENESIS = "0" * 64


def _entry_hash(entry: dict) -> str:
    body = {k: entry[k] for k in ("seq", "ts", "event", "data", "prev")}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class Ledger:
    def __init__(self, path: str):
        self.path = path
        self._lock = threading.Lock()

    def _last(self, fh) -> dict | None:
        fh.seek(0, os.SEEK_END)
        size = fh.tell()
        if size == 0:
            return None
        chunk = min(size, 1 << 20)
        fh.seek(size - chunk)
        lines = fh.read().splitlines()
        return json.loads(lines[-1]) if lines else None

    def append(self, event: str, data: dict) -> dict:
        with self._lock:
            fd = os.open(self.path, os.O_RDWR | os.O_CREAT | os.O_APPEND, 0o600)
            with os.fdopen(fd, "r+b") as fh:
                if fcntl:
                    fcntl.flock(fh, fcntl.LOCK_EX)
                try:
                    last = self._last(fh)
                    entry = {
                        "seq": (last["seq"] + 1) if last else 1,
                        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                        "event": event,
                        "data": data,
                        "prev": last["hash"] if last else GENESIS,
                    }
                    entry["hash"] = _entry_hash(entry)
                    fh.write(json.dumps(entry, sort_keys=True, separators=(",", ":")).encode() + b"\n")
                    fh.flush()
                    os.fsync(fh.fileno())
                finally:
                    if fcntl:
                        fcntl.flock(fh, fcntl.LOCK_UN)
            return entry

    def verify(self, expect_head: str | None = None) -> tuple[bool, int, str, str]:
        """Return (ok, entries, head_hash, message)."""
        prev, n = GENESIS, 0
        if not os.path.exists(self.path):
            return (False, 0, GENESIS, "no ledger file found here (wrong folder, or nothing has been sealed yet)")
        with open(self.path, "rb") as fh:
            for lineno, raw in enumerate(fh, 1):
                try:
                    e = json.loads(raw)
                    ok = e["prev"] == prev and e["seq"] == n + 1 and e["hash"] == _entry_hash(e)
                except (ValueError, KeyError, TypeError):
                    ok = False
                if not ok:
                    return (False, n, prev, f"chain broken at line {lineno}")
                prev, n = e["hash"], n + 1
        if expect_head is not None and expect_head != prev:
            return (False, n, prev, "head does not match expected value (entries removed or replaced)")
        return (True, n, prev, "ok")
