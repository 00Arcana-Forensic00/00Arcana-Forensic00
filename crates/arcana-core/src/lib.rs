// crates/arcana-core/src/lib.rs
pub mod types;
pub mod traits;
pub mod errors;

// types.rs
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Evidence {
    pub id: uuid::Uuid,
    pub source_path: std::path::PathBuf,
    pub acquired_at: DateTime<Utc>,
    pub size_bytes: u64,
    pub sha256: Hash,
    pub metadata: serde_json::Value,
}

pub type Hash = [u8; 32];

// traits.rs
pub trait Sealer {
    fn seal(&self, data: &[u8], metadata: &Evidence) -> Result<SealedEvidence, SealError>;
    fn verify(&self, sealed: &SealedEvidence) -> Result<bool, VerifyError>;
}

pub trait Ledger {
    fn record_acquisition(&self, evidence: &Evidence) -> Result<LedgerEntry, LedgerError>;
    fn verify_chain(&self, from: Option<DateTime<Utc>>) -> Result<ChainVerification, LedgerError>;
}
