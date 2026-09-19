use aes_gcm::{
    aead::{Aead, OsRng},
    Aes256Gcm, Key, Nonce,
};
use argon2::{self, Config, ThreadMode, Variant, Version};
use generic_array::GenericArray;

pub struct EncryptionKey {
    pub key_bytes: [u8; 32],
    pub salt: [u8; 16],
}

impl EncryptionKey {
    pub fn from_password(password: &str, salt: &[u8; 16]) -> Self {
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

        let mut key_bytes = [0u8; 32];
        let hash = argon2::hash_raw(password.as_bytes(), salt, &config).unwrap();
        key_bytes.copy_from_slice(&hash);
        
        Self { key_bytes, salt: *salt }
    }
    
    pub fn generate_salt() -> [u8; 16] {
        let mut salt = [0u8; 16];
        OsRng.fill_bytes(&mut salt);
        salt
    }
}

impl Clone for EncryptionKey {
    fn clone(&self) -> Self {
        Self {
            key_bytes: self.key_bytes,
            salt: self.salt,
        }
    }
}

pub fn seal_data(plaintext: &[u8], key: &EncryptionKey) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    // Generate random nonce
    let mut nonce_bytes = [0u8; 12];
    OsRng.fill_bytes(&mut nonce_bytes);
    
    // Use TryFrom instead of deprecated from_slice
    let key_array = Key::<Aes256Gcm>::from(GenericArray::clone_from_slice(&key.key_bytes));
    let nonce = Nonce::from(GenericArray::clone_from_slice(&nonce_bytes));
    
    let cipher = Aes256Gcm::new(&key_array);
    let ciphertext = cipher.encrypt(&nonce, plaintext)?;
    
    // Prepend nonce and salt to ciphertext for decryption
    let mut result = Vec::with_capacity(12 + 16 + ciphertext.len());
    result.extend_from_slice(&nonce_bytes);
    result.extend_from_slice(&key.salt);
    result.extend_from_slice(&ciphertext);
    
    Ok(result)
}
