//! Shared types, errors, hashing helpers, and path safety for Arcana Forensics.

use std::fs::File;
use std::io::{self, Read};
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use thiserror::Error;

pub const TOOL_NAME: &str = "arcana-forensics";
pub const TOOL_VERSION: &str = env!("CARGO_PKG_VERSION");
pub const VAULT_MAGIC: &[u8; 4] = b"ARCN";
pub const VAULT_VERSION: u8 = 1;
pub const DEFAULT_MAX_FILE_BYTES: u64 = 64 * 1024 * 1024;

#[derive(Debug, Error)]
pub enum ArcanaError {
    #[error("I/O error: {0}")]
    Io(#[from] io::Error),
    #[error("path is not allowed: {0}")]
    PathNotAllowed(String),
    #[error("refusing to process special file: {0}")]
    SpecialFile(String),
    #[error("file exceeds size limit ({0} bytes)")]
    FileTooLarge(u64),
    #[error("vault format error: {0}")]
    Vault(String),
    #[error("authentication failed (wrong passphrase or corrupted vault)")]
    Auth,
    #[error("ledger error: {0}")]
    Ledger(String),
    #[error("classification error: {0}")]
    Classify(String),
    #[error("serialization error: {0}")]
    Serde(#[from] serde_json::Error),
    #[error("{0}")]
    Other(String),
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct EvidenceRecord {
    pub relative_path: String,
    pub size_bytes: u64,
    pub sha256: String,
    pub claimed_extension: String,
    pub magic_hint: String,
    pub vault_relpath: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct CaseManifest {
    pub tool: String,
    pub version: String,
    pub case_id: String,
    pub operator: String,
    pub created_unix: u64,
    pub evidence: Vec<EvidenceRecord>,
}

pub fn unix_now() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
}

pub fn sha256_bytes(data: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(data);
    hex::encode(hasher.finalize())
}

pub fn sha256_file(path: &Path) -> Result<String, ArcanaError> {
    let mut file = File::open(path)?;
    let mut hasher = Sha256::new();
    let mut buf = [0u8; 65_536];
    loop {
        let n = file.read(&mut buf)?;
        if n == 0 {
            break;
        }
        hasher.update(&buf[..n]);
    }
    Ok(hex::encode(hasher.finalize()))
}

/// Canonicalize `candidate` and require it to stay under `root` via strip_prefix.
pub fn confined_path(root: &Path, candidate: &Path) -> Result<PathBuf, ArcanaError> {
    let root = if root.exists() {
        root.canonicalize()?
    } else {
        return Err(ArcanaError::PathNotAllowed(format!(
            "root does not exist: {}",
            root.display()
        )));
    };
    let candidate = if candidate.exists() {
        candidate.canonicalize()?
    } else {
        let parent = candidate
            .parent()
            .ok_or_else(|| ArcanaError::PathNotAllowed(candidate.display().to_string()))?;
        let name = candidate
            .file_name()
            .ok_or_else(|| ArcanaError::PathNotAllowed(candidate.display().to_string()))?;
        parent.canonicalize()?.join(name)
    };
    if candidate.strip_prefix(&root).is_err() {
        return Err(ArcanaError::PathNotAllowed(format!(
            "{} is outside {}",
            candidate.display(),
            root.display()
        )));
    }
    Ok(candidate)
}

pub fn reject_special_file(path: &Path) -> Result<(), ArcanaError> {
    let meta = path.symlink_metadata()?;
    let ft = meta.file_type();
    if ft.is_symlink() {
        return Err(ArcanaError::SpecialFile(format!(
            "symlink skipped: {}",
            path.display()
        )));
    }
    if !ft.is_file() && !ft.is_dir() {
        return Err(ArcanaError::SpecialFile(format!(
            "not a regular file or directory: {}",
            path.display()
        )));
    }
    Ok(())
}

pub fn classify_magic(bytes: &[u8], name: &str) -> (String, String) {
    let ext = Path::new(name)
        .extension()
        .and_then(|s| s.to_str())
        .unwrap_or("")
        .to_ascii_lowercase();
    let hint = if bytes.len() >= 4 && bytes.starts_with(&[0x50, 0x4B, 0x03, 0x04]) {
        "zip-family".to_string()
    } else if bytes.len() >= 5 && bytes.starts_with(b"%PDF-") {
        "pdf".to_string()
    } else if bytes.len() >= 4 && bytes.starts_with(&[0x7F, b'E', b'L', b'F']) {
        "elf".to_string()
    } else if bytes.len() >= 2 && bytes.starts_with(&[0xFF, 0xD8]) {
        "jpeg".to_string()
    } else if bytes.len() >= 8 && bytes.starts_with(&[0x89, b'P', b'N', b'G', 0x0D, 0x0A, 0x1A, 0x0A]) {
        "png".to_string()
    } else if bytes.len() >= 2 && bytes.starts_with(b"#!") {
        "script".to_string()
    } else if looks_like_text(bytes) {
        "text".to_string()
    } else {
        "unknown".to_string()
    };
    (ext, hint)
}

fn looks_like_text(bytes: &[u8]) -> bool {
    if bytes.is_empty() {
        return true;
    }
    let sample = if bytes.len() > 512 { &bytes[..512] } else { bytes };
    let printable = sample
        .iter()
        .filter(|b| b.is_ascii_graphic() || b.is_ascii_whitespace())
        .count();
    printable * 100 / sample.len() >= 85
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn hashes_are_stable() {
        assert_eq!(
            sha256_bytes(b"abc"),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        );
    }
    #[test]
    fn classifies_pdf() {
        let (ext, hint) = classify_magic(b"%PDF-1.7 rest", "report.PDF");
        assert_eq!(ext, "pdf");
        assert_eq!(hint, "pdf");
    }
}
