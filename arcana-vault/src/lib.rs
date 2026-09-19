use aes_gcm::{
    aead::Aead,
    Aes256Gcm, KeyInit, Nonce,
};
use argon2::Argon2;
use rand::{rngs::OsRng, RngCore};
use zeroize::{Zeroize, ZeroizeOnDrop};

#[derive(Clone, Zeroize, ZeroizeOnDrop)]
pub struct EncryptionKey(pub [u8; 32]);

impl EncryptionKey {
    pub fn from_password(password: &str, salt: &[u8; 16]) -> Self {
        let mut key_bytes = [0u8; 32];
        let argon2 = Argon2::default();
        argon2
            .hash_password_into(password.as_bytes(), salt, &mut key_bytes)
            .expect("Failed to derive Argon2 key");
        EncryptionKey(key_bytes)
    }

    pub fn as_bytes(&self) -> &[u8; 32] {
        &self.0
    }
}

pub fn seal_data(data: &[u8], key: &EncryptionKey) -> Result<Vec<u8>, aes_gcm::Error> {
    let cipher = Aes256Gcm::new(key.as_bytes().into());

    let mut nonce_bytes = [0u8; 12];
    OsRng.fill_bytes(&mut nonce_bytes);
    let nonce = Nonce::from(nonce_bytes);

    let ciphertext = cipher.encrypt(&nonce, data)?;

    let mut sealed_payload = Vec::with_capacity(12 + ciphertext.len());
    sealed_payload.extend_from_slice(&nonce_bytes);
    sealed_payload.extend_from_slice(&ciphertext);

    Ok(sealed_payload)
}

pub fn unseal_data(payload: &[u8], key: &EncryptionKey) -> Result<Vec<u8>, aes_gcm::Error> {
    if payload.len() < 12 {
        return Err(aes_gcm::Error);
    }

    let cipher = Aes256Gcm::new(key.as_bytes().into());
    let (nonce_slice, ciphertext) = payload.split_at(12);
    
    let nonce_array: [u8; 12] = nonce_slice.try_into().map_err(|_| aes_gcm::Error)?;
    let nonce = Nonce::from(nonce_array);

    cipher.decrypt(&nonce, ciphertext)
}
