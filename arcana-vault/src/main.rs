use aes_gcm::{Aes256Gcm, Key, Nonce};
use aes_gcm::aead::{Aead, KeyInit};
use std::io;

fn main() -> io::Result<()> {
    println!("--- Arcana Forensics: Storage Vault & Encryption Module ---");

    // 1. Setup a clean 256-bit symmetric encryption key manually via safe byte casting
    let mut key_bytes = [0u8; 32];
    key_bytes.copy_from_slice(b"sixteen_byte_key_sixteen_byte_ky"); // Exactly 32 bytes
    let key = Key::<Aes256Gcm>::from_slice(&key_bytes);

    // 2. Sample raw data received from the acquisition engine pipeline
    let raw_evidence = b"Forensic Payload Data: Hash verification metrics matched successfully.";
    println!("[+] Mocking incoming payload from arcana-acquire...");

    // 3. Initialize the Cipher
    let cipher = Aes256Gcm::new(key);
    
    // Generate a fixed initialization vector nonce (12 bytes)
    let mut nonce_bytes = [0u8; 12];
    nonce_bytes.copy_from_slice(b"unique_nonce"); // Exactly 12 bytes
    let nonce = Nonce::from_slice(&nonce_bytes);

    // 4. Encrypt the data securely
    match cipher.encrypt(nonce, raw_evidence.as_ref()) {
        Ok(ciphertext) => {
            println!("[+] Cryptographic Seal Applied Successfully.");
            println!("[+] Encrypted Block Size: {} bytes", ciphertext.len());
            println!("[+] Raw Hex Block: {:02x?}", &ciphertext[..10]); // Peek first 10 encrypted bytes
            
            // 5. Decrypt verification step to ensure zero data corruption
            if let Ok(plaintext) = cipher.decrypt(nonce, ciphertext.as_slice()) {
                println!("[+] Decryption Check Passed: {}", String::from_utf8_lossy(&plaintext));
                println!("[+] Integrity Validated. Handing off status logs to arcana-custody...");
            }
        }
        Err(_) => println!("[X] Cryptographic Error: Failed to safely seal the block."),
    }

    Ok(())
}
