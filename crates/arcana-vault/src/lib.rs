//! AES-256-GCM vault with stretched passphrase derivation.
//!
//! On-disk blob layout:
//! `ARCN | version(1) | salt(16) | nonce(12) | ciphertext+tag`
//!
//! Key stretching is 100_000 rounds of SHA-256 over `passphrase || salt || counter`.
//! That keeps the crate graph compatible with Rust 1.75. Swap in Argon2id when
//! the toolchain allows edition2024 crates.

use aes_gcm::aead::{Aead, KeyInit};
use aes_gcm::{Aes256Gcm, Key, Nonce};
use rand::rngs::OsRng;
use rand_core::RngCore;
use sha2::{Digest, Sha256};
use zeroize::Zeroize;

use arcana_core::{ArcanaError, VAULT_MAGIC, VAULT_VERSION};

const SALT_LEN: usize = 16;
const NONCE_LEN: usize = 12;
const HEADER_LEN: usize = 4 + 1 + SALT_LEN + NONCE_LEN;
const STRETCH_ROUNDS: u32 = 100_000;

pub struct VaultKey {
    bytes: [u8; 32],
}

impl Drop for VaultKey {
    fn drop(&mut self) {
        self.bytes.zeroize();
    }
}

impl VaultKey {
    pub fn derive(passphrase: &str, salt: &[u8; SALT_LEN]) -> Result<Self, ArcanaError> {
        if passphrase.len() < 12 {
            return Err(ArcanaError::Vault(
                "passphrase must be at least 12 characters".into(),
            ));
        }
        let mut hasher = Sha256::new();
        hasher.update(passphrase.as_bytes());
        hasher.update(salt);
        hasher.update(b"arcana-vault-kdf-v1");
        let mut acc: [u8; 32] = hasher.finalize().into();
        for round in 0..STRETCH_ROUNDS {
            let mut h = Sha256::new();
            h.update(acc);
            h.update(salt);
            h.update(round.to_le_bytes());
            acc = h.finalize().into();
        }
        Ok(Self { bytes: acc })
    }
}

pub fn generate_salt() -> [u8; SALT_LEN] {
    let mut salt = [0u8; SALT_LEN];
    OsRng.fill_bytes(&mut salt);
    salt
}

pub fn seal(plaintext: &[u8], passphrase: &str) -> Result<Vec<u8>, ArcanaError> {
    let salt = generate_salt();
    let key = VaultKey::derive(passphrase, &salt)?;

    let mut nonce_bytes = [0u8; NONCE_LEN];
    OsRng.fill_bytes(&mut nonce_bytes);

    let cipher = Aes256Gcm::new(Key::<Aes256Gcm>::from_slice(&key.bytes));
    let nonce = Nonce::from_slice(&nonce_bytes);
    let ciphertext = cipher
        .encrypt(nonce, plaintext)
        .map_err(|_| ArcanaError::Vault("encryption failed".into()))?;

    let mut out = Vec::with_capacity(HEADER_LEN + ciphertext.len());
    out.extend_from_slice(VAULT_MAGIC);
    out.push(VAULT_VERSION);
    out.extend_from_slice(&salt);
    out.extend_from_slice(&nonce_bytes);
    out.extend_from_slice(&ciphertext);
    Ok(out)
}

pub fn unseal(blob: &[u8], passphrase: &str) -> Result<Vec<u8>, ArcanaError> {
    if blob.len() < HEADER_LEN + 16 {
        return Err(ArcanaError::Vault("blob too short".into()));
    }
    if &blob[..4] != VAULT_MAGIC {
        return Err(ArcanaError::Vault("bad magic".into()));
    }
    if blob[4] != VAULT_VERSION {
        return Err(ArcanaError::Vault(format!("unsupported version {}", blob[4])));
    }

    let mut salt = [0u8; SALT_LEN];
    salt.copy_from_slice(&blob[5..21]);
    let nonce_bytes = &blob[21..33];
    let ciphertext = &blob[33..];

    let key = VaultKey::derive(passphrase, &salt)?;
    let cipher = Aes256Gcm::new(Key::<Aes256Gcm>::from_slice(&key.bytes));
    let nonce = Nonce::from_slice(nonce_bytes);
    cipher
        .decrypt(nonce, ciphertext)
        .map_err(|_| ArcanaError::Auth)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn roundtrip() {
        let secret = b"chain-of-custody evidence";
        let blob = seal(secret, "correct horse battery staple extra").unwrap();
        let plain = unseal(&blob, "correct horse battery staple extra").unwrap();
        assert_eq!(plain, secret);
    }

    #[test]
    fn wrong_password_fails() {
        let blob = seal(b"x", "correct horse battery staple extra").unwrap();
        assert!(unseal(&blob, "wrong password xxx").is_err());
    }

    #[test]
    fn short_passphrase_rejected() {
        assert!(seal(b"x", "short").is_err());
    }
}
