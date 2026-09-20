use aes_gcm::{Aes256Gcm, Key, Nonce};
use aes_gcm::aead::{Aead, KeyInit};
use std::fs::{self, File};
use std::io::{Read, Write};
use std::path::Path;

fn main() {
    println!("--- Emergency Workspace Recovery Channel ---");

    // FIX: From<[u8; N]> is the non-deprecated path — no slice ref needed
    let key   = Key::<Aes256Gcm>::from(*b"sixteen_byte_key_sixteen_byte_ky");
    let nonce = Nonce::from(*b"unique_nonce");
    let cipher = Aes256Gcm::new(&key);

    let target_enc = Path::new("isolated_vault/Cargo.toml.enc");
    if !target_enc.exists() {
        println!("[X] Error: Encrypted block missing. Cannot recover.");
        return;
    }

    let mut encrypted_buffer = Vec::new();
    if File::open(target_enc).unwrap().read_to_end(&mut encrypted_buffer).is_ok() {
        match cipher.decrypt(&nonce, encrypted_buffer.as_slice()) {
            Ok(plaintext) => {
                File::create("Cargo.toml")
                    .unwrap()
                    .write_all(&plaintext)
                    .unwrap();
                println!("[+] SUCCESS: Cargo.toml recovered to root.");
                let _ = fs::remove_file(target_enc);
            }
            Err(_) => println!("[X] Decryption Failure: Key or nonce mismatch."),
        }
    }
}
