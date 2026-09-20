use aes_gcm::{
    aead::{Aead, KeyInit},
    Aes256Gcm, Key, Nonce,
};
use argon2::{Algorithm, Argon2, Params, Version};
use rand_core::{OsRng, RngCore};

pub struct EncryptionKey {
    pub key_bytes: [u8; 32],
    pub salt: [u8; 16],
}

impl EncryptionKey {
    pub fn from_password(password: &str, salt: &[u8; 16]) -> Self {
        // argon2 v0.5: Argon2::new() + hash_password_into() replaces Config + hash_raw()
        let params = Params::new(65536, 3, 4, Some(32)).unwrap();
        let argon2 = Argon2::new(Algorithm::Argon2id, Version::V0x13, params);

        let mut key_bytes = [0u8; 32];
        argon2
            .hash_password_into(password.as_bytes(), salt, &mut key_bytes)
            .unwrap();

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
        Self { key_bytes: self.key_bytes, salt: self.salt }
    }
}

pub fn seal_data(
    plaintext: &[u8],
    key: &EncryptionKey,
) -> Result<Vec<u8>, Box<dyn std::error::Error>> {
    let mut nonce_bytes = [0u8; 12];
    OsRng.fill_bytes(&mut nonce_bytes);

    // From<[u8; N]> is the non-deprecated path — no GenericArray import needed
    let key_array = Key::<Aes256Gcm>::from(key.key_bytes);
    let nonce = Nonce::from(nonce_bytes);

    let cipher = Aes256Gcm::new(&key_array);
    let ciphertext = cipher.encrypt(&nonce, plaintext)?;

    let mut result = Vec::with_capacity(12 + 16 + ciphertext.len());
    result.extend_from_slice(&nonce_bytes);
    result.extend_from_slice(&key.salt);
    result.extend_from_slice(&ciphertext);

    Ok(result)
}
