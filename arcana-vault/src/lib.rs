use aes_gcm::{Aes256Gcm, Key, Nonce};
use aes_gcm::aead::{Aead, KeyInit};

pub fn seal_data(payload: &[u8]) -> Result<Vec<u8>, &'static str> {
    let mut key_bytes = [0u8; 32];
    key_bytes.copy_from_slice(b"sixteen_byte_key_sixteen_byte_ky");
    let key = Key::<Aes256Gcm>::from_slice(&key_bytes);
    let cipher = Aes256Gcm::new(key);

    let mut nonce_bytes = [0u8; 12];
    nonce_bytes.copy_from_slice(b"unique_nonce");
    let nonce = Nonce::from_slice(&nonce_bytes);

    cipher.encrypt(nonce, payload).map_err(|_| "Encryption failed")
}
