PRAGMA journal_mode = WAL;
CREATE TABLE IF NOT EXISTS custody_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INTEGER NOT NULL,
    operator TEXT NOT NULL,
    action TEXT NOT NULL,
    path TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    prev_hash TEXT NOT NULL,
    entry_hash TEXT NOT NULL UNIQUE
);
