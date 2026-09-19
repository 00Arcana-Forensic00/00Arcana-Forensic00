use aes_gcm::{
    aead::{Aead, OsRng},
    Aes256Gcm, Key, Nonce,
};
use zeroize::{Zeroize, ZeroizeOnDrop};

#[derive(Clone, Zeroize, ZeroizeOnDrop)]
pub struct EncryptionKey([u8; 32]);

impl EncryptionKey {
    pub fn from_password(password: &str, salt: &[u8; 16]) -> Self {
        use argon2::{self, Config, ThreadMode, Variant, Version};
        
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
        
        let hash = argon2::hash_raw(password.as_bytes(), salt, &config)
            .expect("Key derivation failed");
        
        let mut key = [0u8; 32];
        key.copy_from_slice(&hash);
        key.zeroize(); // Clear the hash from memory
        EncryptionKey(key)
    }
    
    pub fn generate() -> Self {
        let mut key = [0u8; 32];
        OsRng.fill_bytes(&mut key);
        EncryptionKey(key)
    }
    
    pub fn as_bytes(&self) -> &[u8; 32] {
        &self.0
    }
}

pub fn seal_data(payload: &[u8], key: &EncryptionKey) -> Result<Vec<u8>, &'static str> {
    let cipher = Aes256Gcm::new(Key::<Aes256Gcm>::from_slice(key.as_bytes()));
    
    // Generate secure random nonce for EACH encryption
    let mut nonce_bytes = [0u8; 12];
    OsRng.fill_bytes(&mut nonce_bytes);
    let nonce = Nonce::from_slice(&nonce_bytes);
    
    let ciphertext = cipher.encrypt(nonce, payload)
        .map_err(|_| "Encryption failed")?;
    
    // Format: [nonce (12 bytes)] + [ciphertext]
    let mut result = Vec::with_capacity(12 + ciphertext.len());
    result.extend_from_slice(&nonce_bytes);
    result.extend_from_slice(&ciphertext);
    Ok(result)
}

pub fn unseal_data(vault_data: &[u8], key: &EncryptionKey) -> Result<Vec<u8>, &'static str> {
    if vault_data.len() < 12 {
        return Err("Invalid vault data");
    }
    
    let (nonce_bytes, ciphertext) = vault_data.split_at(12);
    let cipher = Aes256Gcm::new(Key::<Aes256Gcm>::from_slice(key.as_bytes()));
    let nonce = Nonce::from_slice(nonce_bytes);
    
    cipher.decrypt(nonce, ciphertext)
        .map_err(|_| "Decryption failed")
}
