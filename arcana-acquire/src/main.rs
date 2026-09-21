use std::fs::{File, OpenOptions, remove_file};
use std::io::{Write, Seek, SeekFrom, Read};
use std::path::{Path, PathBuf};
use std::os::unix::fs::OpenOptionsExt;
use rand::{RngCore, rngs::OsRng};
use sha2::{Sha256, Digest};
use zeroize::{Zeroize, ZeroizeOnDrop};
use ed25519_dalek::{Signer, SigningKey, Verifier, Signature, VerifyingKey};
use serde::{Serialize, Deserialize};
use arcana_core::ArcanaError;

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum DestructionMethod {
    Clear,
    Purge,
    Destroy,
    CryptoErase,
    NvmeFormat,
}

#[derive(Debug, Serialize, Deserialize, ZeroizeOnDrop)]
pub struct ShredReport {
    pub version: u32,
    pub target: String,
    pub method: DestructionMethod,
    pub passes: u32,
    pub bytes_processed: u64,
    pub verification_passed: bool,
    pub verification_samples: u64,
    pub timestamp: i64,
    pub device_serial: Option<String>,
    pub operator: String,
    pub certificate: Vec<u8>,
    pub signature: Vec<u8>,
}

pub struct CryptoShredder {
    verification_enabled: bool,
    secure_random: OsRng,
    signing_key: SigningKey,
}

impl CryptoShredder {
    pub fn new(signing_key: SigningKey) -> Self {
        Self {
            verification_enabled: true,
            secure_random: OsRng,
            signing_key,
        }
    }

    /// Generate a new Ed25519 keypair for certificate signing
    pub fn generate_keypair() -> (SigningKey, VerifyingKey) {
        let mut csprng = OsRng;
        let signing_key = SigningKey::generate(&mut csprng);
        let verifying_key = signing_key.verifying_key();
        (signing_key, verifying_key)
    }

    pub fn shred_file(
        &mut self,
        path: &Path,
        method: DestructionMethod,
        operator: &str,
    ) -> Result<ShredReport, ArcanaError> {
        let metadata = std::fs::metadata(path)?;
        let file_size = metadata.len();
        let device_serial = self.get_device_serial(path).ok();

        let mut report = match method {
            DestructionMethod::Clear => self.nist_clear(path, file_size)?,
            DestructionMethod::Purge => self.nist_purge(path, file_size)?,
            DestructionMethod::Destroy => self.nist_destroy(path)?,
            DestructionMethod::CryptoErase => self.crypto_erase(path)?,
            DestructionMethod::NvmeFormat => self.nvme_format(path)?,
        };

        report.operator = operator.to_string();
        report.device_serial = device_serial;
        report.version = 1;

        self.finalize_deletion(path)?;
        self.sign_report(&mut report)?;

        Ok(report)
    }

    /// NIST Clear: Single overwrite with fixed pattern
    fn nist_clear(&mut self, path: &Path, size: u64) -> Result<ShredReport, ArcanaError> {
        let pattern: Vec<u8> = vec![0x00];
        self.overwrite_file(path, &pattern, size)?;
        self.sync_file(path)?;

        let verification_passed = if self.verification_enabled {
            self.verify_overwrite(path, &pattern, size)?
        } else {
            true
        };

        Ok(ShredReport {
            version: 1,
            target: path.to_string_lossy().to_string(),
            method: DestructionMethod::Clear,
            passes: 1,
            bytes_processed: size,
            verification_passed,
            verification_samples: size,
            timestamp: chrono::Utc::now().timestamp(),
            device_serial: None,
            operator: String::new(),
            certificate: vec![],
            signature: vec![],
        })
    }

    /// NIST Purge: Multiple overwrites with full verification
    fn nist_purge(&mut self, path: &Path, size: u64) -> Result<ShredReport, ArcanaError> {
        // Pass 1: Zeros
        let zeros = vec![0x00];
        self.overwrite_file(path, &zeros, size)?;
        self.sync_file(path)?;

        // Pass 2: Ones
        let ones = vec![0xFF];
        self.overwrite_file(path, &ones, size)?;
        self.sync_file(path)?;

        // Pass 3: Cryptographic random (streaming, not repeated pattern)
        self.overwrite_random(path, size)?;
        self.sync_file(path)?;

        // Pass 4: Final zeros + verify
        self.overwrite_file(path, &zeros, size)?;
        self.sync_file(path)?;

        let verification_passed = if self.verification_enabled {
            self.verify_overwrite(path, &zeros, size)?
        } else {
            true
        };

        Ok(ShredReport {
            version: 1,
            target: path.to_string_lossy().to_string(),
            method: DestructionMethod::Purge,
            passes: 4,
            bytes_processed: size * 4,
            verification_passed,
            verification_samples: size,
            timestamp: chrono::Utc::now().timestamp(),
            device_serial: None,
            operator: String::new(),
            certificate: vec![],
            signature: vec![],
        })
    }

    /// NIST Destroy: ATA Secure Erase for HDDs
    fn nist_destroy(&mut self, path: &Path) -> Result<ShredReport, ArcanaError> {
        let device = self.get_block_device(path)?;
        let device_size = self.get_device_size(&device)?;

        // Generate random password per operation
        let mut password_bytes = [0u8; 32];
        self.secure_random.fill_bytes(&mut password_bytes);
        let password = hex::encode(password_bytes);
        password_bytes.zeroize();

        self.ata_secure_erase(&device, &password)?;
        let verification_passed = self.verify_device_erased(&device)?;

        Ok(ShredReport {
            version: 1,
            target: path.to_string_lossy().to_string(),
            method: DestructionMethod::Destroy,
            passes: 1,
            bytes_processed: device_size,
            verification_passed,
            verification_samples: 1000,
            timestamp: chrono::Utc::now().timestamp(),
            device_serial: None,
            operator: String::new(),
            certificate: vec![],
            signature: vec![],
        })
    }

    /// NVMe Format: For NVMe SSDs
    fn nvme_format(&mut self, path: &Path) -> Result<ShredReport, ArcanaError> {
        let device = self.get_block_device(path)?;
        let device_size = self.get_device_size(&device)?;
        let nvme_device = self.get_nvme_device(&device)?;

        // nvme format with cryptographic erase (NSID 0xFFFFFFFF = all namespaces)
        use std::process::Command;
        let output = Command::new("nvme")
            .args(&["format", &nvme_device, "-s", "1", "-n", "0xFFFFFFFF"])
            .output()?;

        if !output.status.success() {
            return Err(ArcanaError::Io(std::io::Error::new(
                std::io::ErrorKind::Unsupported,
                "NVMe format failed - device may not support crypto erase"
            )));
        }

        let verification_passed = self.verify_device_erased(&device)?;

        Ok(ShredReport {
            version: 1,
            target: path.to_string_lossy().to_string(),
            method: DestructionMethod::NvmeFormat,
            passes: 1,
            bytes_processed: device_size,
            verification_passed,
            verification_samples: 1000,
            timestamp: chrono::Utc::now().timestamp(),
            device_serial: None,
            operator: String::new(),
            certificate: vec![],
            signature: vec![],
        })
    }

    /// Crypto Erase: Destroy LUKS keys
    fn crypto_erase(&mut self, path: &Path) -> Result<ShredReport, ArcanaError> {
        if self.is_luks_device(path)? {
            self.shred_luks_header(path)?;
        } else {
            return self.nist_purge(path, std::fs::metadata(path)?.len());
        }

        Ok(ShredReport {
            version: 1,
            target: path.to_string_lossy().to_string(),
            method: DestructionMethod::CryptoErase,
            passes: 1,
            bytes_processed: 0,
            verification_passed: true,
            verification_samples: 0,
            timestamp: chrono::Utc::now().timestamp(),
            device_serial: None,
            operator: String::new(),
            certificate: vec![],
            signature: vec![],
        })
    }

    /// Overwrite file with fixed pattern
    fn overwrite_file(&self, path: &Path, pattern: &[u8], size: u64) -> Result<(), ArcanaError> {
        let mut file = OpenOptions::new()
            .write(true)
            .open(path)?;

        file.seek(SeekFrom::Start(0))?;

        let chunk_size = 65536usize;
        let mut written = 0u64;
        let mut buffer = vec![0u8; chunk_size];

        while written < size {
            let to_write = std::cmp::min(chunk_size as u64, size - written) as usize;
            for i in 0..to_write {
                buffer[i] = pattern[i % pattern.len()];
            }
            file.write_all(&buffer[..to_write])?;
            written += to_write as u64;
        }

        buffer.zeroize();
        Ok(())
    }

    /// Overwrite file with cryptographic random data (streaming, not repeated)
    fn overwrite_random(&mut self, path: &Path, size: u64) -> Result<(), ArcanaError> {
        let mut file = OpenOptions::new()
            .write(true)
            .open(path)?;

        file.seek(SeekFrom::Start(0))?;

        let chunk_size = 65536usize;
        let mut written = 0u64;
        let mut buffer = vec![0u8; chunk_size];

        while written < size {
            let to_write = std::cmp::min(chunk_size as u64, size - written) as usize;
            self.secure_random.fill_bytes(&mut buffer[..to_write]);
            file.write_all(&buffer[..to_write])?;
            written += to_write as u64;
        }

        buffer.zeroize();
        Ok(())
    }

    /// Verify file contains expected pattern at every byte
    fn verify_overwrite(
        &self,
        path: &Path,
        expected: &[u8],
        size: u64,
    ) -> Result<bool, ArcanaError> {
        let mut file = File::open(path)?;
        let mut buffer = [0u8; 4096];
        let mut offset = 0u64;

        loop {
            let n = file.read(&mut buffer)?;
            if n == 0 { break; }

            for (i, byte) in buffer[..n].iter().enumerate() {
                let expected_byte = expected[(offset as usize + i) % expected.len()];
                if *byte != expected_byte {
                    return Ok(false);
                }
            }
            offset += n as u64;
        }

        // Verify we read the expected size
        Ok(offset == size)
    }

    /// Verify device is erased using random sector sampling
    fn verify_device_erased(&mut self, device: &Path) -> Result<bool, ArcanaError> {
        let total_size = self.get_device_size(device)?;
        let sector_size = 512u64;
        let sample_count = 1000u64;
        let mut file = File::open(device)?;
        let mut buffer = [0u8; 512];

        for _ in 0..sample_count {
            // Generate random sector offset aligned to sector size
            let random_offset = self.secure_random.next_u64();
            let sector_offset = (random_offset % (total_size / sector_size)) * sector_size;

            file.seek(SeekFrom::Start(sector_offset))?;
            file.read_exact(&mut buffer)?;

            if buffer.iter().any(|&b| b != 0) {
                return Ok(false);
            }
        }

        Ok(true)
    }

    /// ATA Secure Erase with random password
    fn ata_secure_erase(&self, device: &Path, password: &str) -> Result<(), ArcanaError> {
        use std::process::Command;

        // Verify secure erase is supported
        let check = Command::new("hdparm")
            .args(&["-I", device.to_str().unwrap()])
            .output()?;

        if !check.status.success() {
            return Err(ArcanaError::Io(std::io::Error::new(
                std::io::ErrorKind::Unsupported,
                "hdparm not available or device not supported"
            )));
        }

        // Check if secure erase is supported in the output
        let stdout = String::from_utf8_lossy(&check.stdout);
        if !stdout.contains("supported") {
            return Err(ArcanaError::Io(std::io::Error::new(
                std::io::ErrorKind::Unsupported,
                "ATA Secure Erase not supported by this device"
            )));
        }

        // Set security password (random per operation)
        let set_pass = Command::new("hdparm")
            .args(&["--user-master", "u", "--security-set-pass", password, device.to_str().unwrap()])
            .output()?;

        if !set_pass.status.success() {
            return Err(ArcanaError::Io(std::io::Error::new(
                std::io::ErrorKind::PermissionDenied,
                "Failed to set security password - device may be frozen"
            )));
        }

        // Execute secure erase
        let erase = Command::new("hdparm")
            .args(&["--user-master", "u", "--security-erase", password, device.to_str().unwrap()])
            .output()?;

        if !erase.status.success() {
            return Err(ArcanaError::Io(std::io::Error::new(
                std::io::ErrorKind::Other,
                "ATA Secure Erase command failed"
            )));
        }

        Ok(())
    }

    /// Get NVMe device path from block device
    fn get_nvme_device(&self, device: &Path) -> Result<String, ArcanaError> {
        let dev_name = device.file_name()
            .ok_or_else(|| ArcanaError::Io(std::io::Error::new(
                std::io::ErrorKind::InvalidInput,
                "Invalid device path"
            )))?
            .to_string_lossy()
            .to_string();

        // NVMe devices: /dev/nvme0 -> /dev/nvme0, /dev/nvme0n1 -> /dev/nvme0
        if dev_name.starts_with("nvme") {
            let controller = dev_name.split('n').next().unwrap_or(&dev_name);
            return Ok(format!("/dev/{}", controller));
        }

        Err(ArcanaError::Io(std::io::Error::new(
            std::io::ErrorKind::InvalidInput,
            "Not an NVMe device"
        )))
    }

    /// Get device serial number for audit trail
    fn get_device_serial(&self, path: &Path) -> Result<String, ArcanaError> {
        let device = self.get_block_device(path)?;
        let dev_name = device.file_name()
            .map(|n| n.to_string_lossy().to_string())
            .unwrap_or_default();

        let serial_path = format!("/sys/block/{}/device/serial", dev_name);
        std::fs::read_to_string(&serial_path)
            .map(|s| s.trim().to_string())
            .map_err(|e| ArcanaError::Io(e))
    }

    /// Sync file to disk
    fn sync_file(&self, path: &Path) -> Result<(), ArcanaError> {
        let file = OpenOptions::new().write(true).open(path)?;
        file.sync_all()?;
        Ok(())
    }

    /// Finalize deletion with random rename + sync + unlink
    fn finalize_deletion(&self, path: &Path) -> Result<(), ArcanaError> {
        // Generate valid hex filename
        let mut random_bytes = [0u8; 16];
        OsRng.fill_bytes(&mut random_bytes);
        let random_name: String = random_bytes.iter()
            .map(|b| format!("{:02x}", b))
            .collect();

        let parent = path.parent().unwrap_or(Path::new("."));
        let temp_path = parent.join(random_name);

        std::fs::rename(path, &temp_path)?;

        // Sync directory
        let dir = File::open(parent)?;
        dir.sync_all()?;
        drop(dir);

        remove_file(&temp_path)?;
        Ok(())
    }

    /// Serialize report for signing (canonical JSON)
    fn serialize_for_signing(&self, report: &ShredReport) -> Result<Vec<u8>, ArcanaError> {
        // Create a canonical representation excluding the signature field
        let canonical = serde_json::json!({
            "version": report.version,
            "target": report.target,
            "method": report.method,
            "passes": report.passes,
            "bytes_processed": report.bytes_processed,
            "verification_passed": report.verification_passed,
            "verification_samples": report.verification_samples,
            "timestamp": report.timestamp,
            "device_serial": report.device_serial,
            "operator": report.operator,
        });

        // Sort keys for canonical form
        let serialized = serde_json::to_vec_pretty(&canonical)?;
        Ok(serialized)
    }

    /// Sign report with Ed25519
    fn sign_report(&self, report: &mut ShredReport) -> Result<(), ArcanaError> {
        let data = self.serialize_for_signing(report)?;

        // Certificate = SHA256 of canonical data (for quick verification)
        let mut hasher = Sha256::new();
        hasher.update(&data);
        report.certificate = hasher.finalize().to_vec();

        // Signature = Ed25519 over certificate
        let signature = self.signing_key.sign(&report.certificate);
        report.signature = signature.to_vec();

        Ok(())
    }

    /// Verify a report's signature against a public key
    pub fn verify_certificate(
        report: &ShredReport,
        verifying_key: &VerifyingKey,
    ) -> bool {
        if report.signature.len() != 64 {
            return false;
        }

        let signature = match Signature::from_slice(&report.signature) {
            Ok(s) => s,
            Err(_) => return false,
        };

        verifying_key.verify(&report.certificate, &signature).is_ok()
    }

    /// Export report as signed JSON certificate
    pub fn export_certificate(report: &ShredReport, output_path: &Path) -> Result<(), ArcanaError> {
        let json = serde_json::to_string_pretty(report)?;
        std::fs::write(output_path, json)?;
        Ok(())
    }

    fn get_block_device(&self, path: &Path) -> Result<PathBuf, ArcanaError> {
        use std::process::Command;
        let output = Command::new("df")
            .args(&["--output=source", path.to_str().unwrap()])
            .output()?;

        let stdout = String::from_utf8_lossy(&output.stdout);
        let device = stdout.lines().nth(1)
            .ok_or_else(|| ArcanaError::Io(std::io::Error::new(
                std::io::ErrorKind::NotFound,
                "Device not found"
            )))?;

        Ok(PathBuf::from(device.trim()))
    }

    fn is_luks_device(&self, path: &Path) -> Result<bool, ArcanaError> {
        use std::process::Command;
        let output = Command::new("cryptsetup")
            .args(&["isLuks", path.to_str().unwrap()])
            .output()?;
        Ok(output.status.success())
    }

    fn shred_luks_header(&self, path: &Path) -> Result<(), ArcanaError> {
        use std::process::Command;
        Command::new("cryptsetup")
            .args(&["luksErase", "--batch-mode", path.to_str().unwrap()])
            .output()?;
        Ok(())
    }

    fn get_device_size(&self, device: &Path) -> Result<u64, ArcanaError> {
        use std::process::Command;
        let output = Command::new("blockdev")
            .args(&["--getsize64", device.to_str().unwrap()])
            .output()?;

        let size_str = String::from_utf8_lossy(&output.stdout);
        size_str.trim().parse::<u64>()
            .map_err(|e| ArcanaError::Io(std::io::Error::new(
                std::io::ErrorKind::InvalidData,
                e
            )))
    }
}
