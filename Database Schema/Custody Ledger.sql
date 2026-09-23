CREATE TABLE entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,  -- RFC 3339 format
    operation TEXT NOT NULL,  -- 'acquire', 'verify', 'export'
    path TEXT,                -- Relative path (sanitized)
    hash_prev TEXT NOT NULL,  -- SHA-256 of previous entry
    hash_data TEXT NOT NULL,  -- SHA-256 of this entry's data
    hash_chain TEXT NOT NULL, -- SHA-256(prev || timestamp || data)
    operator TEXT NOT NULL,   -- Authenticated identity
    signature TEXT            -- Optional Ed25519 signature
);

CREATE INDEX idx_chain ON entries(hash_chain);
CREATE INDEX idx_timestamp ON entries(timestamp);
