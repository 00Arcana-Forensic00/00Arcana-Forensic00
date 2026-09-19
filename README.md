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
