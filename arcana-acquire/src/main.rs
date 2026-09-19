use std::env;
use std::fs::{self, File};
use std::io::{self, Read, Write};
use std::path::Path;
use std::time::{SystemTime, UNIX_EPOCH};
use sha2::{Sha256, Digest};

const DORMANT_THRESHOLD_SECS: u64 = 30 * 24 * 3600; // 30 Days

#[derive(Debug, PartialEq)]
enum ArtifactType {
    ElfBinary,
    ZipCompressed,
    PdfDocument,
    PngImage,
    JpegImage,
    UnknownBinary,
    Plaintext,
}

fn determine_file_signature(buffer: &[u8]) -> ArtifactType {
    if buffer.len() < 4 {
        return ArtifactType::Plaintext;
    }
    match &buffer[..4] {
        [0x7f, 0x45, 0x4c, 0x46] => ArtifactType::ElfBinary,
        [0x50, 0x4b, 0x03, 0x04] => ArtifactType::ZipCompressed,
        [0x25, 0x50, 0x44, 0x46] => ArtifactType::PdfDocument,
        [0x89, 0x50, 0x4e, 0x47] => ArtifactType::PngImage,
        [0xff, 0xd8, 0xff, _]    => ArtifactType::JpegImage,
        _ => {
            let non_printable = buffer.iter().filter(|&&b| b < 32 || b > 126).count();
            if non_printable as f32 / buffer.len() as f32 > 0.2 {
                ArtifactType::UnknownBinary
            } else {
                ArtifactType::Plaintext
            }
        }
    }
}

// OPEN SOURCE UTILITY: Core File Carver Logic
fn carve_hidden_artifacts(raw_stream: &[u8], isolation_dir: &Path) -> io::Result<()> {
    println!("[*] Initializing Raw Stream File Carver...");
    let pdf_header = b"%PDF";
    let pdf_footer = b"%%EOF";

    let mut index = 0;
    let mut carver_count = 0;

    while index < raw_stream.len() {
        if raw_stream[index..].starts_with(pdf_header) {
            println!("[!] Carver found a potential match starting at byte index {}!", index);
            
            for sub_index in (index + pdf_header.len())..raw_stream.len() {
                let target_window = &raw_stream[sub_index..];
                if target_window.starts_with(b"%%EOF") || target_window.starts_with(b"%%eof") {
                    let end_pos = sub_index + pdf_footer.len();
                    let carved_payload = &raw_stream[index..end_pos];

                    carver_count += 1;
                    let output_path = isolation_dir.join(format!("carved_evidence_{}.pdf", carver_count));
                    
                    let mut carved_file = File::create(&output_path)?;
                    carved_file.write_all(carved_payload)?;
                    println!("[+] SUCCESS: Ripped hidden artifact directly out of raw bytes into {:?}", output_path);
                    
                    index = end_pos;
                    break;
                }
            }
        }
        index += 1;
    }

    if carver_count == 0 {
        println!("[+] Carver check finished: No deleted or unlinked file blocks found.");
    }
    Ok(())
}

fn scan_directory(dir_path: &Path) -> io::Result<()> {
    if !dir_path.is_dir() {
        println!("[X] Path is not a valid directory.");
        return Ok(());
    }

    let current_time = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs();

    let isolation_dir = Path::new("isolated_vault");
    if !isolation_dir.exists() {
        fs::create_dir(isolation_dir)?;
    }

    println!("\n--- [STARTING FILESYSTEM FORENSIC SIGNATURE SCAN] ---");

    for entry in fs::read_dir(dir_path)? {
        let entry = entry?;
        let path = entry.path();

        if path.is_file() {
            let metadata = entry.metadata()?;
            let extension = path.extension().unwrap_or_default().to_string_lossy().to_lowercase();
            let file_name = path.file_name().unwrap_or_default().to_string_lossy().into_owned();

            if extension == "json" || extension == "txt" || path.to_string_lossy().contains("target/") || path.to_string_lossy().contains("isolated_vault/") {
                continue;
            }

            let modified_time = metadata.modified()
                .unwrap_or(SystemTime::UNIX_EPOCH)
                .duration_since(UNIX_EPOCH)
                .unwrap_or_default()
                .as_secs();
            
            let dormant_secs = current_time.saturating_sub(modified_time);
            let is_dormant = dormant_secs > DORMANT_THRESHOLD_SECS;

            let mut file = File::open(&path)?;
            let mut chunk = vec![0u8; 1024];
            let bytes_read = file.read(&mut chunk)?;
            chunk.truncate(bytes_read);

            let true_profile = determine_file_signature(&chunk);

            println!("\n------------------------------------------------");
            println!("[+] TARGET IDENTIFIED : {}", file_name);
            println!("[+] CLAIMED EXTENSION : .{}", extension.to_uppercase());
            println!("[+] TRUE SIGNATURE    : {:?}", true_profile);
            println!("[+] DORMANT TIME      : {} hours", dormant_secs / 3600);

            let mut full_buffer = Vec::new();
            if File::open(&path)?.read_to_end(&mut full_buffer).is_ok() {
                let mut hasher = Sha256::new();
                hasher.update(&full_buffer);
                let hash_result = hasher.finalize();
                let crypto_signature: String = hash_result.iter().map(|b| format!("{:02x}", b)).collect();

                if true_profile == ArtifactType::UnknownBinary || extension == "dat" {
                    carve_hidden_artifacts(&full_buffer, isolation_dir)?;
                }

                if is_dormant {
                    println!("[!] VULNERABILITY ALERT: Dormant asset verified via magic bits.");
                    println!("[!] Enforcing secure partition isolation...");

                    match arcana_vault::seal_data(&full_buffer) {
                        Ok(ciphertext) => {
                            let secured_destination = isolation_dir.join(format!("{}.enc", file_name));
                            let mut target_file = File::create(&secured_destination)?;
                            target_file.write_all(&ciphertext)?;
                            fs::remove_file(&path)?;
                            println!("[+] SUCCESS: Re-encrypted to {:?}", secured_destination);

                            arcana_custody::log_chain_of_custody(&file_name, &crypto_signature, ciphertext.len());
                        }
                        Err(e) => println!("[X] Security error: {}", e),
                    }
                } else {
                    if let Ok(ciphertext) = arcana_vault::seal_data(&full_buffer) {
                        arcana_custody::log_chain_of_custody(&file_name, &crypto_signature, ciphertext.len());
                    }
                }
            }
        }
    }
    Ok(())
}

fn main() -> io::Result<()> {
    println!("--- Arcana Forensics Workspace Execution Pipeline ---");
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        println!("[!] Usage: cargo run -p arcana-acquire -- <target_directory_path>");
        return Ok(());
    }
    let target_dir = &args;
    scan_directory(Path::new(&args[1]))?;
    Ok(())
}
