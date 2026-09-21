CREATE TABLE IF NOT EXISTS forensic_cases (
    id BIGSERIAL PRIMARY KEY,
    case_id TEXT NOT NULL UNIQUE,
    operator TEXT NOT NULL,
    source_root TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS custody_ledger (
    id BIGSERIAL PRIMARY KEY,
    case_pk BIGINT NOT NULL REFERENCES forensic_cases(id),
    ts_unix BIGINT NOT NULL,
    operator TEXT NOT NULL,
    action_taken TEXT NOT NULL,
    path TEXT NOT NULL,
    sha256_hash CHAR(64) NOT NULL,
    prev_hash CHAR(64) NOT NULL,
    entry_hash CHAR(64) NOT NULL UNIQUE
);
