use std::env;
use std::fs::{self, File};
use std::io::{self, Read, Write, stdout};
use std::path::{Path, PathBuf};
use std::sync::{mpsc, Arc, Mutex};
use std::thread;

use sha2::{Digest, Sha256};
use rusqlite::{params, Connection};
use rpassword::read_password;

// FIX 1: Removed duplicate const declarations
const WORKER_THREADS: usize = 4;
const CHUNK_SIZE: usize = 8192; // 8KB streaming chunks

// FIX 2: #[warn] -> #[allow] (warn *enables* the lint, allow *suppresses* it)
// FIX 3: Added #[derive(Debug)] — required for format!("{:?}", true_profile)
// FIX 4: Removed duplicate ZipCompressed and SevenZipPack variants
#[allow(dead_code)]
#[derive(Debug)]
enum ArtifactType {
    ZipCompressed,
    SevenZipPack,
    ElfBinary,
    ExeBinary,
    MsiInstaller,
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
    if path_str.starts_with("/proc")
        || path_str.starts_with("/sys")
        || path_str.starts_with("/dev")
    {
        return false;
    }

    true
}

// FIX 5: Moved above determine_file_signature — it's called by it
fn contains_bytes(haystack: &[u8], needle: &[u8]) -> bool {
    haystack.windows(needle.len()).any(|window| window == needle)
}

fn determine_file_signature(buffer: &[u8]) -> ArtifactType {
    if buffer.len() < 4 {
        return ArtifactType::Plaintext;
    }

    if buffer.starts_with(b"#!/") {
        // FIX 6: windows(7) with b"python" (6 bytes) never matched — use contains_bytes instead
        if contains_bytes(buffer, b"python3") || contains_bytes(buffer, b"python") {
            return ArtifactType::PythonScript;
        }
        return ArtifactType::ShellScript;
    }

    // FIX 7: Office doc check was inside the `_` wildcard arm — unreachable because
    // [0x50,0x4b,0x03,0x04] was already consumed by the ZipCompressed arm above it.
    // Moved here, before the match, so .docx/.xlsx are correctly identified.
    if buffer.starts_with(&[0x50, 0x4b, 0x03, 0x04]) {
        let buf_str = String::from_utf8_lossy(buffer);
        if buf_str.contains("word/") {
            return ArtifactType::WordDocument;
        }
        if buf_str.contains("xl/") {
            return ArtifactType::ExcelSpreadsheet;
        }
        return ArtifactType::ZipCompressed;
    }

    match &buffer[..4] {
        [0x7f, 0x45, 0x4c, 0x46] => ArtifactType::ElfBinary,
        [0x4d, 0x5a, _, _]       => ArtifactType::ExeBinary,
        [0xd0, 0xcf, 0x11, 0xe0] => ArtifactType::MsiInstaller,
        [0x37, 0x7a, 0xbc, 0xaf] => ArtifactType::SevenZipPack,
        [0x1f, 0x8b, ..]         => ArtifactType::GzipCompressed,
        [0x25, 0x50, 0x44, 0x46] => ArtifactType::PdfDocument,
        [0x89, 0x50, 0x4e, 0x47] => ArtifactType::PngImage,
        [0xff, 0xd8, 0xff, _]    => ArtifactType::JpegImage,
        [0x47, 0x49, 0x46, 0x38] => ArtifactType::GifImage,
        _ => {
            let non_printable = buffer.iter().filter(|&&b| b < 32 || b > 126).count();
            if non_printable as f32 / buffer.len() as f32 > 0.2 {
                ArtifactType::UnknownBinary
            } else {
                ArtifactType::Plaintext
            }
        }
    }
    // FIX 8: Removed the duplicate stray code block that appeared after the closing brace
}

fn hash_file_streaming(path: &Path) -> io::Result<String> {
    let mut file = File::open(path)?;
    let mut hasher = Sha256::new();
    let mut buffer = [0u8; CHUNK_SIZE];

    loop {
        let n = file.read(&mut buffer)?;
        if n == 0 {
            break;
        }
        hasher.update(&buffer[..n]);
    }

    Ok(hasher.finalize().iter().map(|b| format!("{:02x}", b)).collect())
}

fn execute_premium_db_sync(
    conn: &Connection,
    file_name: &str,
    hash: &str,
    size: i64,
    signature: &str,
) -> Result<(), rusqlite::Error> {
    conn.execute(
        "INSERT OR REPLACE INTO forensic_artifacts
         (file_name, file_size, true_signature, sha256_hash, processed_at)
         VALUES (?1, ?2, ?3, ?4, datetime('now'));",
        params![file_name, size, signature, hash],
    )?;
    Ok(())
}

fn init_database(conn: &Connection) -> Result<(), rusqlite::Error> {
    conn.execute(
        "CREATE TABLE IF NOT EXISTS forensic_artifacts (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name     TEXT    NOT NULL,
            file_size     INTEGER NOT NULL,
            true_signature TEXT   NOT NULL,
            sha256_hash   TEXT    NOT NULL UNIQUE,
            processed_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );",
        [],
    )?;

    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_hash ON forensic_artifacts(sha256_hash);",
        [],
    )?;

    Ok(())
}

fn process_forensic_job(
    job: ForensicJob,
    isolation_dir: &Path,
    key: &arcana_vault::EncryptionKey,
    conn: &Arc<Mutex<Connection>>,
) -> io::Result<()> {
    let mut file = File::open(&job.path)?;
    let mut header = vec![0u8; 1024.min(job.metadata.len() as usize)];
    file.read_exact(&mut header)?;
    drop(file);

    let true_profile = determine_file_signature(&header);
    let signature_string = format!("{:?}", true_profile);

    let crypto_signature = hash_file_streaming(&job.path)?;

    let mut file = File::open(&job.path)?;
    let mut plaintext = Vec::new();
    file.read_to_end(&mut plaintext)?;

    if let Ok(ciphertext) = arcana_vault::seal_data(&plaintext, key) {
        arcana_custody::log_chain_of_custody(&job.file_name, &crypto_signature, ciphertext.len());

        let vault_path = isolation_dir.join(format!("{}.enc", job.file_name));
        File::create(&vault_path)?.write_all(&ciphertext)?;

        let conn = conn.lock().unwrap();
        if let Err(e) = execute_premium_db_sync(
            &conn,
            &job.file_name,
            &crypto_signature,
            job.metadata.len() as i64,
            &signature_string,
        ) {
            eprintln!("[X] Database write failed: {}", e);
        } else {
            println!("[💎 Premium DB] Committed: {}", job.file_name);
        }
    }

    Ok(())
}

fn scan_directory_multithreaded(
    dir_path: &Path,
    key: arcana_vault::EncryptionKey,
) -> io::Result<()> {
    let isolation_dir = PathBuf::from("isolated_vault");
    if !isolation_dir.exists() {
        fs::create_dir(&isolation_dir)?;
    }

    let conn = Connection::open("forensic_evidence.db3")?;
    init_database(&conn)?;
    let conn = Arc::new(Mutex::new(conn));

    let (tx, rx) = mpsc::channel::<ForensicJob>();
    let rx = Arc::new(Mutex::new(rx));
    let isolation_dir_arc = Arc::new(isolation_dir);
    let mut handles = vec![];

    for _ in 0..WORKER_THREADS {
        let key_clone = key.clone();
        let rx_clone = Arc::clone(&rx);
        let iso_dir_clone = Arc::clone(&isolation_dir_arc);
        let conn_clone = Arc::clone(&conn);

        let handle = thread::spawn(move || loop {
            let job = {
                let lock = rx_clone.lock().unwrap();
                match lock.recv() {
                    Ok(job) => job,
                    Err(_) => break,
                }
            };
            if let Err(e) = process_forensic_job(job, &iso_dir_clone, &key_clone, &conn_clone) {
                eprintln!("[X] Processing error: {}", e);
            }
        });
        handles.push(handle);
    }

    let base_dir = dir_path.canonicalize()?;

    for entry in fs::read_dir(dir_path)? {
        let entry = entry?;
        let path = entry.path();

        if !is_safe_path(&path, &base_dir) {
            println!("[!] Blocked path traversal: {:?}", path);
            continue;
        }

        if path.is_file() {
            let path_str = path.to_string_lossy();
            if path_str.contains("/target/") || path_str.contains("/isolated_vault/") {
                continue;
            }

            let file_name = path
                .file_name()
                .unwrap_or_default()
                .to_string_lossy()
                .into_owned();
            let metadata = entry.metadata()?;
            let _ = tx.send(ForensicJob { path, file_name, metadata });
        }
    }

    drop(tx);
    for handle in handles {
        let _ = handle.join();
    }

    println!("[+] Forensic acquisition complete. Database: forensic_evidence.db3");
    Ok(())
}

fn main() -> io::Result<()> {
    println!("--- Arcana Forensics Workspace Execution Pipeline ---");

    print!("Enter vault password: ");
    stdout().flush()?;
    let password = read_password().unwrap_or_default();

    let salt = arcana_vault::EncryptionKey::generate_salt();
    let key = arcana_vault::EncryptionKey::from_password(&password, &salt);

    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        println!("[!] Usage: cargo run -p arcana-acquire -- <target_directory_path>");
        return Ok(());
    }

    scan_directory_multithreaded(Path::new(&args[1]), key)?;
    Ok(())
}
