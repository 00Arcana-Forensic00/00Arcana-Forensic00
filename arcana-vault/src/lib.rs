use aes_gcm::{
    aead::{Aead, AeadCore},
    Aes256Gcm, Key, KeyInit, Nonce,
};
use argon2::Argon2;
use rand_core::OsRng;
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
    let cipher = Aes256Gcm::new(Key::<Aes256Gcm>::from_slice(key.as_bytes()));
    let nonce = Aes256Gcm::generate_nonce(&mut OsRng);

    let ciphertext = cipher.encrypt(&nonce, data)?;

    // Output format: [12-byte Nonce] + [Ciphertext + 16-byte Poly1305 Tag]
    let mut sealed_payload = Vec::with_capacity(nonce.len() + ciphertext.len());
    sealed_payload.extend_from_slice(nonce.as_slice());
    sealed_payload.extend_from_slice(&ciphertext);

    Ok(sealed_payload)
}

pub fn unseal_data(payload: &[u8], key: &EncryptionKey) -> Result<Vec<u8>, aes_gcm::Error> {
    if payload.len() < 12 {
        return Err(aes_gcm::Error);
    }

    let cipher = Aes256Gcm::new(Key::<Aes256Gcm>::from_slice(key.as_bytes()));
    let (nonce_bytes, ciphertext) = payload.split_at(12);
    let nonce = Nonce::from_slice(nonce_bytes);

    cipher.decrypt(nonce, ciphertext)
}
