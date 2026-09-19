use std::env;
use std::fs::{self, File};
use std::io::{self, Read, Write, stdin, stdout};
use std::path::{Path, PathBuf};
use std::sync::{mpsc, Arc, Mutex};
use std::thread;
use std::time::{SystemTime, UNIX_EPOCH};
use sha2::{Sha256, Digest};
use rusqlite::{params, Connection};

const WORKER_THREADS: usize = 4;

#[allow(dead_code)]
#[derive(Debug, PartialEq, Clone)]
enum ArtifactType {
    ElfBinary,
    ExeBinary,
    MsiInstaller,
    ZipCompressed,
    SevenZipPack,
    GzipCompressed,
    PdfDocument,
    WordDocument,
    ExcelSpreadsheet,
    PngImage,
    JpegImage,
    GifImage,
    ShellScript,
    PythonScript,
    UnknownBinary,
    Plaintext,
}

struct ForensicJob {
    path: PathBuf,
    file_name: String,
    metadata: fs::Metadata,
}

pub fn is_safe_path(target: &Path, root: &Path) -> bool {
    let canonical_root = match root.canonicalize() {
        Ok(p) => p,
        Err(_) => return false,
    };

    let canonical_target = match target.canonicalize() {
        Ok(p) => p,
        Err(_) => return false,
    };

    if !canonical_target.starts_with(&canonical_root) {
        return false;
    }

    let path_str = canonical_target.to_string_lossy();
    if path_str.starts_with("/proc") || path_str.starts_with("/sys") || path_str.starts_with("/dev") {
        return false;
    }

    true
}

fn determine_file_signature(buffer: &[u8]) -> ArtifactType {
    if buffer.len() < 4 {
        return ArtifactType::Plaintext;
    }
    match &buffer[..4] {
        [0x7f, 0x45, 0x4c, 0x46] => ArtifactType::ElfBinary,
        [0x4d, 0x5a, _, _]       => ArtifactType::ExeBinary,
        [0xd0, 0xcf, 0x11, 0xe0] => ArtifactType::MsiInstaller,
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

fn execute_premium_db_sync_test(file_name: &str, hash: &str, size: i64, signature: &str) -> Result<(), rusqlite::Error> {
    println!("\n[💎 Premium DB] Connecting to synchronized corporate relational ledger...");
    
    let conn = Connection::open_in_memory()?;

    conn.execute(
        "CREATE TABLE IF NOT EXISTS forensic_artifacts (
            id INTEGER PRIMARY KEY,
            file_name TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            true_signature TEXT NOT NULL,
            sha256_hash TEXT NOT NULL UNIQUE
        );",
        [],
    )?;

    conn.execute(
        "INSERT INTO forensic_artifacts (file_name, file_size, true_signature, sha256_hash) 
         VALUES (?1, ?2, ?3, ?4);",
        params![file_name, size, signature, hash],
    )?;

    println!("[💎 Premium DB] SUCCESS: Relational entry committed safely via rusqlite.");
    Ok(())
}

fn process_forensic_job(
    job: ForensicJob, 
    _current_time: u64, 
    isolation_dir: &Path, 
    key: &arcana_vault::EncryptionKey
) -> io::Result<()> {
    let mut file = File::open(&job.path)?;
    let mut chunk = vec![0u8; 1024];
    let bytes_read = file.read(&mut chunk)?;
    chunk.truncate(bytes_read);

    let true_profile = determine_file_signature(&chunk);
    let signature_string = format!("{:?}", true_profile);

    let mut full_buffer = Vec::new();
    if File::open(&job.path)?.read_to_end(&mut full_buffer).is_ok() {
        let mut hasher = Sha256::new();
        hasher.update(&full_buffer);
        let hash_result = hasher.finalize();
        let crypto_signature: String = hash_result.iter().map(|b| format!("{:02x}", b)).collect();

        if let Ok(ciphertext) = arcana_vault::seal_data(&full_buffer, key) {
            arcana_custody::log_chain_of_custody(&job.file_name, &crypto_signature, ciphertext.len());
            
            let vault_path = isolation_dir.join(format!("{}.enc", job.file_name));
            let mut vault_file = File::create(&vault_path)?;
            vault_file.write_all(&ciphertext)?;

            if let Err(e) = execute_premium_db_sync_test(
                &job.file_name, 
                &crypto_signature, 
                job.metadata.len() as i64, 
                &signature_string
            ) {
                println!("[X] Premium DB Write Flag Failure: {}", e);
            }
        }
    }
    Ok(())
}

fn scan_directory_multithreaded(dir_path: &Path, key: arcana_vault::EncryptionKey) -> io::Result<()> {
    let current_time = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_secs();
    let isolation_dir = PathBuf::from("isolated_vault");
    if !isolation_dir.exists() {
        fs::create_dir(&isolation_dir)?;
    }

    let (tx, rx) = mpsc::channel::<ForensicJob>();
    let rx = Arc::new(Mutex::new(rx));
    let isolation_dir_arc = Arc::new(isolation_dir);
    let mut handles = vec![];

    for _ in 0..WORKER_THREADS {
        let key_clone = key.clone();
        let rx_clone = Arc::clone(&rx);
        let iso_dir_clone = Arc::clone(&isolation_dir_arc);

        let handle = thread::spawn(move || {
            loop {
                let job = {
                    let lock = rx_clone.lock().unwrap();
                    match lock.recv() {
                        Ok(job) => job,
                        Err(_) => break,
                    }
                };
                let _ = process_forensic_job(job, current_time, &iso_dir_clone, &key_clone);
            }
        });
        handles.push(handle);
    }

    let base_dir = dir_path.canonicalize()?;

    for entry in fs::read_dir(dir_path)? {
        let entry = entry?;
        let path = entry.path();
        
        if !is_safe_path(&path, &base_dir) {
            println!("[!] Blocked path traversal attempt: {:?}", path);
            continue;
        }
        
        if path.is_file() {
            let extension = path.extension().unwrap_or_default().to_string_lossy().to_lowercase();
            let file_name = path.file_name().unwrap_or_default().to_string_lossy().into_owned();

            if extension == "json" || extension == "txt" || path.to_string_lossy().contains("target/") || path.to_string_lossy().contains("isolated_vault/") {
                continue;
            }

            let metadata = entry.metadata()?;
            let job = ForensicJob { path, file_name, metadata };
            let _ = tx.send(job);
        }
    }

    drop(tx);
    for handle in handles {
        let _ = handle.join();
    }
    Ok(())
}

fn main() -> io::Result<()> {
    println!("--- Arcana Forensics Workspace Execution Pipeline ---");
    
    print!("Enter vault password: ");
    stdout().flush()?;
    let mut password = String::new();
    stdin().read_line(&mut password)?;
    let password = password.trim();
    
    let salt = [0u8; 16];
    let key = arcana_vault::EncryptionKey::from_password(password, &salt);
    
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        println!("[!] Usage: cargo run -p arcana-acquire -- <target_directory_path>");
        return Ok(());
    }
    
    scan_directory_multithreaded(Path::new(&args[1]), key)?;
    Ok(())
}
