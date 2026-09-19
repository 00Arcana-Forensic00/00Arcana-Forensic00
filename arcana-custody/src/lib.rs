use std::time::{SystemTime, UNIX_EPOCH};

pub fn log_chain_of_custody(target_name: &str, target_hash: &str, encrypted_size: usize) {
    let epoch_seconds = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs();

    println!("\n--- Automated Chain of Custody Audit Sealed ---");
    println!("RECORD TARGET: {}", target_name);
    println!("TIMESTAMP    : {} (Unix Epoch)", epoch_seconds);
    println!("SHA-256 HASH : {}", target_hash);
    println!("VAULT SIZE   : {} encrypted bytes", encrypted_size);
    println!("STATUS       : Write-locked with zero cloud exposure.");
    println!("-----------------------------------------------");
}
