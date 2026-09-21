use std::fs::{self, File};
use std::io::{Read, Write};
use std::path::PathBuf;
use std::process::ExitCode;

use clap::{Parser, Subcommand};
use walkdir::WalkDir;

use arcana_core::{
    classify_magic, confined_path, reject_special_file, sha256_bytes, sha256_file, unix_now,
    ArcanaError, CaseManifest, EvidenceRecord, DEFAULT_MAX_FILE_BYTES, TOOL_NAME, TOOL_VERSION,
};
use arcana_custody::Ledger;
use arcana_vault::{seal, unseal};

#[derive(Parser, Debug)]
#[command(
    name = "arcana-acquire",
    version = TOOL_VERSION,
    about = "Air-gapped filesystem acquisition with AES-256-GCM vault sealing and a hash-chained custody ledger."
)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand, Debug)]
enum Commands {
    /// Copy regular files from an approved root into a sealed case directory.
    Acquire {
        #[arg(long)]
        path: PathBuf,
        #[arg(long)]
        out: PathBuf,
        #[arg(long)]
        operator: String,
        #[arg(long, default_value = "case-001")]
        case_id: String,
        #[arg(long, default_value_t = DEFAULT_MAX_FILE_BYTES)]
        max_bytes: u64,
        #[arg(long, env = "ARCANA_VAULT_PASSWORD")]
        password: Option<String>,
    },
    /// Recompute hashes and verify the custody hash chain.
    Verify {
        #[arg(long)]
        case: PathBuf,
        #[arg(long, env = "ARCANA_VAULT_PASSWORD")]
        password: Option<String>,
    },
    /// Print the case manifest as JSON.
    ExportManifest {
        #[arg(long)]
        case: PathBuf,
    },
}

fn read_password(explicit: Option<String>) -> Result<String, ArcanaError> {
    if let Some(p) = explicit {
        if p.len() < 12 {
            return Err(ArcanaError::Vault(
                "passphrase must be at least 12 characters".into(),
            ));
        }
        return Ok(p);
    }
    Err(ArcanaError::Other(
        "passphrase required via --password or ARCANA_VAULT_PASSWORD".into(),
    ))
}

fn acquire(
    source: PathBuf,
    out: PathBuf,
    operator: String,
    case_id: String,
    max_bytes: u64,
    password: String,
) -> Result<(), ArcanaError> {
    if operator.trim().is_empty() {
        return Err(ArcanaError::Other("operator is required".into()));
    }
    if !source.is_dir() {
        return Err(ArcanaError::PathNotAllowed(format!(
            "source is not a directory: {}",
            source.display()
        )));
    }
    let source = source.canonicalize()?;
    fs::create_dir_all(&out)?;
    let out = out.canonicalize()?;
    let vault_dir = out.join("vault");
    let ledger_path = out.join("custody.sqlite");
    fs::create_dir_all(&vault_dir)?;
    let ledger = Ledger::open(&ledger_path)?;
    ledger.append(
        &operator,
        "case-open",
        &source.display().to_string(),
        &sha256_bytes(case_id.as_bytes()),
    )?;
    let mut evidence = Vec::new();
    let mut skipped = 0u64;
    for entry in WalkDir::new(&source).follow_links(false).into_iter() {
        let entry = match entry {
            Ok(e) => e,
            Err(_) => {
                skipped += 1;
                continue;
            }
        };
        let path = entry.path();
        if entry.file_type().is_dir() {
            continue;
        }
        if let Err(err) = reject_special_file(path) {
            eprintln!("skip: {err}");
            skipped += 1;
            continue;
        }
        if !entry.file_type().is_file() {
            skipped += 1;
            continue;
        }
        let confined = match confined_path(&source, path) {
            Ok(p) => p,
            Err(err) => {
                eprintln!("skip: {err}");
                skipped += 1;
                continue;
            }
        };
        let meta = confined.metadata()?;
        if meta.len() > max_bytes {
            eprintln!("skip oversized {} ({} bytes)", confined.display(), meta.len());
            skipped += 1;
            continue;
        }
        let digest = sha256_file(&confined)?;
        let mut header = [0u8; 16];
        let mut f = File::open(&confined)?;
        let n = f.read(&mut header)?;
        let rel = confined
            .strip_prefix(&source)
            .unwrap_or(confined.as_path())
            .to_string_lossy()
            .replace('\\', "/");
        let (ext, hint) = classify_magic(&header[..n], &rel);
        let plaintext = fs::read(&confined)?;
        let blob = seal(&plaintext, &password)?;
        let vault_name = format!("{digest}.arcv");
        let vault_path = vault_dir.join(&vault_name);
        let mut out_file = File::create(&vault_path)?;
        out_file.write_all(&blob)?;
        out_file.sync_all()?;
        ledger.append(&operator, "ingest-seal", &rel, &digest)?;
        evidence.push(EvidenceRecord {
            source_path: confined.display().to_string(),
            relative_path: rel,
            size_bytes: meta.len(),
            sha256: digest,
            claimed_extension: ext,
            magic_hint: hint,
            vault_relpath: format!("vault/{vault_name}"),
        });
    }
    let manifest = CaseManifest {
        tool: TOOL_NAME.to_string(),
        version: TOOL_VERSION.to_string(),
        case_id,
        operator: operator.clone(),
        created_unix: unix_now(),
        source_root: source.display().to_string(),
        evidence,
    };
    let manifest_bytes = serde_json::to_vec_pretty(&manifest)?;
    fs::write(out.join("manifest.json"), &manifest_bytes)?;
    ledger.append(
        &operator,
        "manifest-write",
        "manifest.json",
        &sha256_bytes(&manifest_bytes),
    )?;
    let (n, ok) = ledger.verify_chain()?;
    println!(
        "acquired {} file(s), skipped {skipped}, ledger events {n}, chain_ok={ok}",
        manifest.evidence.len()
    );
    println!("case directory: {}", out.display());
    Ok(())
}

fn verify(case: PathBuf, password: Option<String>) -> Result<(), ArcanaError> {
    let case = case.canonicalize()?;
    let raw = fs::read(case.join("manifest.json"))?;
    let manifest: CaseManifest = serde_json::from_slice(&raw)?;
    let ledger = Ledger::open(&case.join("custody.sqlite"))?;
    let (events, chain_ok) = ledger.verify_chain()?;
    let mut mismatches = 0u64;
    if let Some(pw) = password {
        for ev in &manifest.evidence {
            let vault = confined_path(&case, &case.join(&ev.vault_relpath))?;
            let blob = fs::read(&vault)?;
            let plain = unseal(&blob, &pw)?;
            let digest = sha256_bytes(&plain);
            if digest != ev.sha256 || plain.len() as u64 != ev.size_bytes {
                eprintln!("mismatch: {}", ev.relative_path);
                mismatches += 1;
            }
        }
    } else {
        println!("note: pass --password or ARCANA_VAULT_PASSWORD to unseal and re-hash vault blobs");
    }
    println!(
        "manifest files={}, ledger events={events}, chain_ok={chain_ok}, vault_mismatches={mismatches}",
        manifest.evidence.len()
    );
    if !chain_ok || mismatches > 0 {
        return Err(ArcanaError::Other("verification failed".into()));
    }
    Ok(())
}

fn export_manifest(case: PathBuf) -> Result<(), ArcanaError> {
    let case = case.canonicalize()?;
    let raw = fs::read(case.join("manifest.json"))?;
    let parsed: CaseManifest = serde_json::from_slice(&raw)?;
    println!("{}", serde_json::to_string_pretty(&parsed)?);
    Ok(())
}

fn run() -> Result<(), ArcanaError> {
    let cli = Cli::parse();
    match cli.command {
        Commands::Acquire {
            path,
            out,
            operator,
            case_id,
            max_bytes,
            password,
        } => {
            let password = read_password(password)?;
            acquire(path, out, operator, case_id, max_bytes, password)
        }
        Commands::Verify { case, password } => verify(case, password),
        Commands::ExportManifest { case } => export_manifest(case),
    }
}

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(err) => {
            eprintln!("error: {err}");
            ExitCode::from(1)
        }
    }
}
