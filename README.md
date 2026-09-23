<div align="center">

<img src="https://raw.githubusercontent.com/mitchell5584dm-tech/00Arcana-Forensic00/main/site/assets/arcana-logo-dark.svg#gh-dark-mode-only" width="180" alt="Arcana Forensics">
<img src="https://raw.githubusercontent.com/mitchell5584dm-tech/00Arcana-Forensic00/main/site/assets/arcana-logo-light.svg#gh-light-mode-only" width="180" alt="Arcana Forensics">

# Arcana Forensics

[![CI](https://github.com/mitchell5584dm-tech/00Arcana-Forensic00/actions/workflows/field-test.yml/badge.svg)](https://github.com/mitchell5584dm-tech/00Arcana-Forensic00/actions/workflows/field-test.yml)
[![Security Audit](https://github.com/mitchell5584dm-tech/00Arcana-Forensic00/actions/workflows/security.yml/badge.svg)](https://github.com/mitchell5584dm-tech/00Arcana-Forensic00/actions/workflows/security.yml)
[![License](https://img.shields.io/badge/license-MIT%2FCommercial-blue.svg)](LICENSE)
[![Rust](https://img.shields.io/badge/rust-1.75%2B-000000?logo=rust)](https://www.rust-lang.org)
[![Crate](https://img.shields.io/crates/v/arcana-acquire)](https://crates.io/crates/arcana-acquire)

**Air-Gapped Digital Evidence Acquisition & Immutable Custody Chain**

[Documentation](https://docs.arcana-forensics.com) · [Live Demo](https://arcana-forensics.com/try) · [Pricing](https://arcana-forensics.com/pricing)

</div>

---

## Overview

Arcana is a **military-grade forensic acquisition engine** designed for environments where evidence integrity is non-negotiable. Built in Rust with zero network dependencies, it provides a cryptographically verifiable chain of custody from acquisition to the courtroom.

### Core Capabilities

| Feature | Implementation | Standard |
|---------|---------------|----------|
| **Air-Gapped Acquisition** | Zero network stack integration | NIST SP 800-86 |
| **Vault Encryption** | AES-256-GCM + Argon2id | FIPS 197 |
| **Custody Ledger** | SHA-256 hash chain + SQLite | ISO 27037 |
| **Path Confinement** | Canonicalization + sandboxing | OSSTMM |
| **Memory Safety** | Rust ownership model | CWE-416 elimination |

> **⚠️ Scope Declaration:** This is a **read-only acquisition tool**. Previous iterations included destructive operations—these have been **permanently removed**. Arcana acquires; it does not modify or destroy.

---

## Quick Start

```bash
# 1. Clone and verify signature
git clone https://github.com/mitchell5584dm-tech/00Arcana-Forensic00.git
cd 00Arcana-Forensic00
git verify-commit HEAD  # Signed releases only

# 2. Build with release optimizations
cargo build --release --locked

# 3. Generate synthetic evidence for testing
python3 demo/scripts/make_evidence.py

# 4. Execute field test
export ARCANA_VAULT_PASSWORD='your-secure-passphrase'
./target/release/arcana-acquire acquire \
  --path demo/opensource/01-acquire/evidence \
  --out ./cases/test-run \
  --operator "forensic-analyst" \
  --case-id TEST-001

# 5. Verify cryptographic integrity
./target/release/arcana-acquire verify --case ./cases/test-run
