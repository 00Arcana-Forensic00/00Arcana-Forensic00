//! Append-only SQLite custody ledger with a SHA-256 hash chain.

use std::path::Path;

use rusqlite::{params, Connection, OptionalExtension};

use arcana_core::{sha256_bytes, unix_now, ArcanaError};

const GENESIS: &str = "0000000000000000000000000000000000000000000000000000000000000000";

#[derive(Debug, Clone)]
pub struct CustodyEvent {
    pub id: i64,
    pub ts: i64,
    pub operator: String,
    pub action: String,
    pub path: String,
    pub sha256: String,
    pub prev_hash: String,
    pub entry_hash: String,
}

pub struct Ledger {
    conn: Connection,
}

impl Ledger {
    pub fn open(path: &Path) -> Result<Self, ArcanaError> {
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)?;
        }
        let conn = Connection::open(path).map_err(|e| ArcanaError::Ledger(e.to_string()))?;
        conn.execute_batch(
            "
            PRAGMA journal_mode = WAL;
            PRAGMA foreign_keys = ON;
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
            CREATE INDEX IF NOT EXISTS idx_custody_sha ON custody_events(sha256);
            ",
        )
        .map_err(|e| ArcanaError::Ledger(e.to_string()))?;
        Ok(Self { conn })
    }

    fn tip_hash(&self) -> Result<String, ArcanaError> {
        let hash: Option<String> = self
            .conn
            .query_row(
                "SELECT entry_hash FROM custody_events ORDER BY id DESC LIMIT 1",
                [],
                |row| row.get(0),
            )
            .optional()
            .map_err(|e| ArcanaError::Ledger(e.to_string()))?;
        Ok(hash.unwrap_or_else(|| GENESIS.to_string()))
    }

    pub fn append(
        &self,
        operator: &str,
        action: &str,
        path: &str,
        sha256: &str,
    ) -> Result<CustodyEvent, ArcanaError> {
        let ts = unix_now() as i64;
        let prev = self.tip_hash()?;
        let material = format!("{ts}|{operator}|{action}|{path}|{sha256}|{prev}");
        let entry_hash = sha256_bytes(material.as_bytes());
        self.conn
            .execute(
                "INSERT INTO custody_events
                 (ts, operator, action, path, sha256, prev_hash, entry_hash)
                 VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
                params![ts, operator, action, path, sha256, prev, entry_hash],
            )
            .map_err(|e| ArcanaError::Ledger(e.to_string()))?;
        let id = self.conn.last_insert_rowid();
        Ok(CustodyEvent {
            id,
            ts,
            operator: operator.to_string(),
            action: action.to_string(),
            path: path.to_string(),
            sha256: sha256.to_string(),
            prev_hash: prev,
            entry_hash,
        })
    }

    pub fn verify_chain(&self) -> Result<(usize, bool), ArcanaError> {
        let mut stmt = self
            .conn
            .prepare(
                "SELECT id, ts, operator, action, path, sha256, prev_hash, entry_hash
                 FROM custody_events ORDER BY id ASC",
            )
            .map_err(|e| ArcanaError::Ledger(e.to_string()))?;
        let rows = stmt
            .query_map([], |row| {
                Ok(CustodyEvent {
                    id: row.get(0)?,
                    ts: row.get(1)?,
                    operator: row.get(2)?,
                    action: row.get(3)?,
                    path: row.get(4)?,
                    sha256: row.get(5)?,
                    prev_hash: row.get(6)?,
                    entry_hash: row.get(7)?,
                })
            })
            .map_err(|e| ArcanaError::Ledger(e.to_string()))?;
        let mut prev = GENESIS.to_string();
        let mut count = 0usize;
        for row in rows {
            let ev = row.map_err(|e| ArcanaError::Ledger(e.to_string()))?;
            if ev.prev_hash != prev {
                return Ok((count, false));
            }
            let material = format!(
                "{}|{}|{}|{}|{}|{}",
                ev.ts, ev.operator, ev.action, ev.path, ev.sha256, ev.prev_hash
            );
            if sha256_bytes(material.as_bytes()) != ev.entry_hash {
                return Ok((count, false));
            }
            prev = ev.entry_hash;
            count += 1;
        }
        Ok((count, true))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::env;
    #[test]
    fn hash_chain_verifies() {
        let dir = env::temp_dir().join(format!("arcana-ledger-{}.sqlite", std::process::id()));
        let _ = std::fs::remove_file(&dir);
        let ledger = Ledger::open(&dir).unwrap();
        ledger.append("op", "ingest", "a.txt", "aa").unwrap();
        ledger.append("op", "seal", "a.txt", "aa").unwrap();
        let (n, ok) = ledger.verify_chain().unwrap();
        assert_eq!(n, 2);
        assert!(ok);
        let _ = std::fs::remove_file(&dir);
    }
}
