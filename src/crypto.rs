use aes_gcm::{
    aead::{Aead, KeyInit, OsRng},
    Aes256Gcm, Key, Nonce,
};
use argon2::{self, Config, ThreadMode, Variant, Version};
use zeroize::{Zeroize, ZeroizeOnDrop};

#[derive(Zeroize, ZeroizeOnDrop)]
pub struct SecureKey(Vec<u8>);

pub fn derive_key(password: &str, salt: &[u8]) -> Result<SecureKey, argon2::Error> {
    let config = Config {
        variant: Variant::Argon2id,
        version: Version::Version13,
        mem_cost: 65536,
        time_cost: 3,
        lanes: 4,
        thread_mode: ThreadMode::Parallel,
        secret: &[],
        ad: &[],
        hash_length: 32,
    };
    
    let hash = argon2::hash_raw(password.as_bytes(), salt, &config)?;
    Ok(SecureKey(hash))
}

pub fn encrypt_vault(plaintext: &[u8], key: &SecureKey) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    let cipher = Aes256Gcm::new(Key::<Aes256Gcm>::from_slice(&key.0));
    
    // Generate random nonce for EACH encryption
    let mut nonce_bytes = [0u8; 12];
    OsRng.fill_bytes(&mut nonce_bytes);
    let nonce = Nonce::from_slice(&nonce_bytes);
    
    let ciphertext = cipher.encrypt(nonce, plaintext)
        .map_err(|_| "Encryption failed")?;
    
    // Format: [nonce (12 bytes)] + [ciphertext]
    let mut result = Vec::with_capacity(12 + ciphertext.len());
    result.extend_from_slice(&nonce_bytes);
    result.extend_from_slice(&ciphertext);
    
    Ok(result)
}

pub fn decrypt_vault(vault_data: &[u8], key: &SecureKey) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    if vault_data.len() < 12 {
        return Err("Invalid vault data".into());
    }
    
    let (nonce_bytes, ciphertext) = vault_data.split_at(12);
    let cipher = Aes256Gcm::new(Key::<Aes256Gcm>::from_slice(&key.0));
    let nonce = Nonce::from_slice(nonce_bytes);
    
    cipher.decrypt(nonce, ciphertext)
        .map_err(|_| "Decryption failed - wrong password or corrupted data".into())
}
