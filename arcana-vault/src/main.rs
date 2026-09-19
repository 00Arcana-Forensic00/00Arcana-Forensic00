use aes_gcm::{Aes256Gcm, Key, Nonce};
use aes_gcm::aead::{Aead, KeyInit};
use std::fs::{self, File};
use std::io::{Read, Write};
use std::path::Path;

fn main() {
    println!("--- Emergency Workspace Recovery Channel ---");
    
    // 1. Reinitialize the exact symmetric key bytes used during the lockdown
    let mut key_bytes = [0u8; 32];
    key_bytes.copy_from_slice(b"sixteen_byte_key_sixteen_byte_ky");
    let key: &Key<Aes256Gcm> = key_bytes[..].into();
    let cipher = Aes256Gcm::new(key);
    
    let mut nonce_bytes = [0u8; 12];
    nonce_bytes.copy_from_slice(b"unique_nonce");
    let nonce: &Nonce = nonce_bytes[..].into();

    // 2. Identify the encrypted configuration block path
    let target_enc = Path::new("isolated_vault/Cargo.toml.enc");
    if !target_enc.exists() {
        println!("[X] Error: Encrypted block missing. Cannot recover.");
        return;
    }

    // 3. Read and Decrypt
    let mut encrypted_buffer = Vec::new();
    if File::open(target_enc).unwrap().read_to_end(&mut encrypted_buffer).is_ok() {
        // Fix the type trait constraint by wrapping the slice inside a generic container path
        let cipher_payload: &[u8] = encrypted_buffer.as_slice();
        
        match cipher.decrypt(nonce, cipher_payload) {
            Ok(plaintext) => {
                // Restore the original Cargo.toml right back into your root folder
                let mut recovered_file = File::create("Cargo.toml").unwrap();
                recovered_file.write_all(&plaintext).unwrap();
                println!("[+] SUCCESS: Cargo.toml has been decrypted and recovered to your root folder!");
                
                // Delete the locked remnant file safely
                let _ = fs::remove_file(target_enc);
            }
            Err(_) => {
                println!("[X] Decryption Failure: Key or nonce mismatch.");
            }
        }
    }
}
