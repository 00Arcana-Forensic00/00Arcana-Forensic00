use std::env;
use std::fs::{self, File};
use std::io::{self, Read, Write};
use std::path::{Path, PathBuf};
use std::sync::{mpsc, Arc, Mutex};
use std::thread;
use std::time::{SystemTime, UNIX_EPOCH};
use sha2::{Sha256, Digest};

const DORMANT_THRESHOLD_SECS: u64 = 30 * 24 * 3600; // 30 Days
const WORKER_THREADS: usize = 4; // Number of parallel processing channels

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
    extension: String,
    metadata: fs::Metadata,
}
fn determine_file_signature(buffer: &[u8]) -> ArtifactType {
    if buffer.len() < 4 {
        return ArtifactType::Plaintext;
    }

    // Advanced Dictionary Match: Parse raw hex magic headers 
    match &buffer[..4] {
        // --- Executables, Binaries & Installers ---
        [0x7f, 0x45, 0x4c, 0x46] => ArtifactType::ElfBinary,     // .ELF (Linux Binary)
        [0x4d, 0x5a, _, _]       => ArtifactType::ExeBinary,     // .EXE / .DLL (Windows PE)
        [0xd0, 0xcf, 0x11, 0xe0] => ArtifactType::MsiInstaller,  // .MSI / .DOC (Legacy Compound File)
        
        // --- Archives & Compressed Packs ---
        [0x50, 0x4b, 0x03, 0x04] => {
            // Distinguish OpenXML formats (DOCX/XLSX) from standard ZIP containers
            let content_str = String::from_utf8_lossy(buffer);
            if content_str.contains("word/") {
                ArtifactType::WordDocument
            } else if content_str.contains("xl/") {
                ArtifactType::ExcelSpreadsheet
            } else {
                ArtifactType::ZipCompressed
            }
        },
        [0x37, 0x7a, 0xbc, 0xaf] => ArtifactType::SevenZipPack,   // .7Z
        [0x1f, 0x8b, _, _]       => ArtifactType::GzipCompressed, // .GZ
        
        // --- Documents & Forensic Media ---
        [0x25, 0x50, 0x44, 0x46] => ArtifactType::PdfDocument,   // .PDF
        [0x89, 0x50, 0x4e, 0x47] => ArtifactType::PngImage,      // .PNG
        [0xff, 0xd8, 0xff, _]    => ArtifactType::JpegImage,     // .JPG / .JPEG
        [0x47, 0x49, 0x46, 0x38] => ArtifactType::GifImage,      // .GIF
        
        // --- Fallback Script or Raw Plaintext Strings ---
        _ => {
            // Catch hash files or script strings starting with common plaintext signatures
            if buffer.starts_with(b"#!/") {
                ArtifactType::ShellScript
            } else if buffer.starts_with(b"import ") || buffer.starts_with(b"def ") {
                ArtifactType::PythonScript
            } else {
                // High entropy indicates obscured binary payloads or missing keys
                let non_printable = buffer.iter().filter(|&&b| b < 32 || b > 126).count();
                if non_printable as f32 / buffer.len() as f32 > 0.2 {
                    ArtifactType::UnknownBinary
                } else {
                    ArtifactType::Plaintext
                }
            }
        }
    }
}

fn carve_hidden_artifacts(raw_stream: &[u8], isolation_dir: &Path) -> io::Result<()> {
    let pdf_header = b"%PDF";
    let pdf_footer = b"%%EOF";
    let mut index = 0;
    let mut carver_count = 0;

    while index < raw_stream.len() {
        if raw_stream[index..].starts_with(pdf_header) {
            for sub_index in (index + pdf_header.len())..raw_stream.len() {
                let target_window = &raw_stream[sub_index..];
                if target_window.starts_with(b"%%EOF") || target_window.starts_with(b"%%eof") {
                    let end_pos = sub_index + pdf_footer.len();
                    let carved_payload = &raw_stream[index..end_pos];

                    carver_count += 1;
                    let output_path = isolation_dir.join(format!("carved_evidence_{}.pdf", carver_count));
                    let mut carved_file = File::create(&output_path)?;
                    carved_file.write_all(carved_payload)?;
                    println!("[🚀 Worker] SUCCESS: Carved unlinked artifact to {:?}", output_path);
                    index = end_pos;
                    break;
                }
            }
        }
        index += 1;
    }
    Ok(())
}

fn process_forensic_job(job: ForensicJob, current_time: u64, isolation_dir: &Path) -> io::Result<()> {
    let modified_time = job.metadata.modified()
        .unwrap_or(SystemTime::UNIX_EPOCH)
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs();
    
    let dormant_secs = current_time.saturating_sub(modified_time);
    let is_dormant = dormant_secs > DORMANT_THRESHOLD_SECS;

    let mut file = File::open(&job.path)?;
    let mut chunk = vec![0u8; 1024];
    let bytes_read = file.read(&mut chunk)?;
    chunk.truncate(bytes_read);

    let true_profile = determine_file_signature(&chunk);

    println!("\n[🔬 Thread Worker Processing Asset]");
    println!("------------------------------------------------");
    println!("[+] TARGET IDENTIFIED : {}", job.file_name);
    println!("[+] TRUE SIGNATURE    : {:?}", true_profile);
    println!("[+] DORMANT TIME      : {} hours", dormant_secs / 3600);

    let mut full_buffer = Vec::new();
    if File::open(&job.path)?.read_to_end(&mut full_buffer).is_ok() {
        let mut hasher = Sha256::new();
        hasher.update(&full_buffer);
        let hash_result = hasher.finalize();
        let crypto_signature: String = hash_result.iter().map(|b| format!("{:02x}", b)).collect();

        if true_profile == ArtifactType::UnknownBinary || job.extension == "dat" {
            carve_hidden_artifacts(&full_buffer, isolation_dir)?;
        }

        if is_dormant {
            println!("[!] VULNERABILITY ALERT: Enforcing isolation re-encryption...");
            if let Ok(ciphertext) = arcana_vault::seal_data(&full_buffer) {
                let secured_destination = isolation_dir.join(format!("{}.enc", job.file_name));
                File::create(&secured_destination)?.write_all(&ciphertext)?;
                fs::remove_file(&job.path)?;
                println!("[+] SUCCESS: Re-encrypted to {:?}", secured_destination);
                arcana_custody::log_chain_of_custody(&job.file_name, &crypto_signature, ciphertext.len());
            }
        } else {
            if let Ok(ciphertext) = arcana_vault::seal_data(&full_buffer) {
                arcana_custody::log_chain_of_custody(&job.file_name, &crypto_signature, ciphertext.len());
            }
        }
    }
    Ok(())
}

fn scan_directory_multithreaded(dir_path: &Path) -> io::Result<()> {
    if !dir_path.is_dir() {
        println!("[X] Path is not a valid directory.");
        return Ok(());
    }

    let current_time = SystemTime::now().duration_since(UNIX_EPOCH).unwrap_or_default().as_secs();
    let isolation_dir = PathBuf::from("isolated_vault");
    if !isolation_dir.exists() {
        fs::create_dir(&isolation_dir)?;
    }

    // Initialize Thread Pool Messaging Channels
    let (tx, rx) = mpsc::channel::<ForensicJob>();
    let rx = Arc::new(Mutex::new(rx));
    let isolation_dir_arc = Arc::new(isolation_dir);
    let mut handles = vec![];

    println!("\n--- [STARTING MULTI-THREADED FORENSIC PIPELINE ASYNC] ---");
    println!("[*] Spawning {} asynchronous thread channel workers...", WORKER_THREADS);

    for worker_id in 0..WORKER_THREADS {
        let rx_clone = Arc::clone(&rx);
        let iso_dir_clone = Arc::clone(&isolation_dir_arc);
        
        let handle = thread::spawn(move || {
            loop {
                let job = {
                    let lock = rx_clone.lock().unwrap();
                    match lock.recv() {
                        Ok(job) => job,
                        Err(_) => break, // Channel closed, finish thread loop execution
                    }
                };
                if let Err(e) = process_forensic_job(job, current_time, &iso_dir_clone) {
                    println!("[X] Thread Worker {} hit processing error: {}", worker_id, e);
                }
            }
        });
        handles.push(handle);
    }

    // Master File-Scanner Thread feeds the job queues asynchronously
    for entry in fs::read_dir(dir_path)? {
        let entry = entry?;
        let path = entry.path();

        if path.is_file() {
            let extension = path.extension().unwrap_or_default().to_string_lossy().to_lowercase();
            let file_name = path.file_name().unwrap_or_default().to_string_lossy().into_owned();

            if extension == "json" || extension == "txt" || path.to_string_lossy().contains("target/") || path.to_string_lossy().contains("isolated_vault/") {
                continue;
            }

            let metadata = entry.metadata()?;
            let job = ForensicJob {
                path,
                file_name,
                extension,
                metadata,
            };
            
            tx.send(job).unwrap_or_default();
        }
    }

    // Drop the sender channel to let background threads know no more files are coming
    drop(tx);

    // Wait for all asynchronous background workers to finish up
    for handle in handles {
        handle.join().unwrap_or_default();
    }

    println!("\n[+] Pipeline Complete: All background thread worker allocations finished.");
    Ok(())
}

fn main() -> io::Result<()> {
    println!("--- Arcana Forensics Workspace Execution Pipeline ---");
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        println!("[!] Usage: cargo run -p arcana-acquire -- <target_directory_path>");
        return Ok(());
    }
    scan_directory_multithreaded(Path::new(&args[1]))?;
    Ok(())
}
