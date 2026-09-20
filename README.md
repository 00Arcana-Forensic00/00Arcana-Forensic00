# Arcana Forensics

[![Rust](https://img.shields.io/badge/Rust-2021_Edition-orange?logo=rust&logoColor=white)](https://www.rust-lang.org/)
[![License](https://img.shields.io/badge/License-MIT%20%2F%20Apache--2.0-blue)](LICENSE)
[![Security: AES-256-GCM](https://img.shields.io/badge/Encryption-AES--256--GCM-green?logo=lock&logoColor=white)](#vault-architecture)
[![Integrity: SHA-256](https://img.shields.io/badge/Hashing-SHA--256-red)](#chain-of-custody)
[![Storage: SQLite](https://img.shields.io/badge/Ledger-rusqlite-blueviolet?logo=sqlite&logoColor=white)](#ledger--audit)

**Arcana Forensics** is a high-assurance digital forensics acquisition suite engineered in Rust. It captures, classifies, and seals evidence inside tamper-evident cryptographic containers with an automated chain-of-custody ledger.

---

## Key Capabilities

* **Zero Cloud Exposure:** Air-gapped operational model. Artifacts are sealed locally without outbound telemetry or network dependency.
* **Cryptographic Enclave (`arcana-vault`):** Hardware-accelerated **AES-256-GCM** authenticated encryption ensures post-acquisition evidence confidentiality and tamper detection.
* **Automated Chain of Custody:** Calculates cryptographic **SHA-256** checksums at the point of ingestion and enforces strict write-locks.
* **Structured Ledger Tracking:** Commits acquisition metadata, epoch timestamps, and hashes to an embedded relational ledger (`rusqlite`) for defensible audit trails.
* **Multi-Format Ingestion Engine:** Native discovery heuristics for archives (`.zip`, `.7z`, `.gz`), structured documents (`.pdf`, `.docx`, `.xlsx`), scripts (`.sh`, `.py`), and raw filesystem traces (`unallocated_space.dat`).

---

## Architecture Overview

```text
Target Filesystem / Block Device
               │
               ▼
   [ arcana-acquire (CLI Engine) ]
        │                  │
        │ File Stream      │ Artifact Signatures
        ▼                  ▼
 [ arcana-vault ]   [ Forensic Classifier ]
  - AES-256-GCM      - Magic byte detection
  - SHA-256 seal     - Dormancy & metadata analysis
        │                  │
        └─────────┬────────┘
                  ▼
   [ Synchronized Relational Ledger ]
     (Local SQLite via rusqlite)

arcana-forensics/
├── Cargo.toml                    # Workspace root
├── crates/
│   ├── arcana-core/              # NEW: Shared types, traits, errors
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── types.rs          # Evidence, Hash, Timestamp
│   │       ├── traits.rs         # Sealer, Classifier, Ledger
│   │       └── errors.rs         # Unified error types
│   │
│   ├── arcana-vault/             # Cryptographic sealing (OPEN SOURCE)
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── seal.rs           # AES-256-GCM sealing
│   │       ├── verify.rs         # Integrity verification
│   │       └── keymgmt.rs        # Basic key handling
│   │
│   ├── arcana-custody/           # Audit ledger (OPEN SOURCE)
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── ledger.rs         # SQLite schema & writes
│   │       ├── chain.rs          # Hash chain verification
│   │       └── report.rs         # Audit report generation
│   │
│   ├── arcana-acquire/           # CLI acquisition tool (OPEN SOURCE)
│   │   └── src/
│   │       ├── main.rs
│   │       ├── commands/
│   │       │   ├── acquire.rs    # Disk/file acquisition
│   │       │   ├── verify.rs    # Verify sealed evidence
│   │       │   └── export.rs    # Export to open formats
│   │       └── classifiers/      # Basic file type detection
│   │           ├── magic.rs
│   │           └── mime.rs
│   │
│   └── arcana-plugins/           # PREMIUM — separate crate or workspace
│       ├── Cargo.toml            # Private crate, not in main workspace
│       ├── yara-engine/
│       ├── memory-forensics/
│       ├── registry-parser/
│       └── cloud-connectors/
│
├── plugins/                      # Alternative: premium as path dependencies
│   └── yara/                     # Only built with --features premium
│
└── Cargo.lock                    # Single lockfile for reproducibility
