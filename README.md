 +<div align="center">
 +
 +<img src="https://raw.githubusercontent.com/mitchell5584dm-tech/00Arcana-Forensic00/main/site/assets/arcana-logo-dar
k.svg#gh-dark-mode-only" width="180" alt="Arcana Forensics">
 +<img src="https://raw.githubusercontent.com/mitchell5584dm-tech/00Arcana-Forensic00/main/site/assets/arcana-logo-lig
ht.svg#gh-light-mode-only" width="180" alt="Arcana Forensics">
 +
  # Arcana Forensics
  
++<<<<<<< HEAD
 +[![CI](https://github.com/mitchell5584dm-tech/00Arcana-Forensic00/actions/workflows/field-test.yml/badge.svg)](https
://github.com/mitchell5584dm-tech/00Arcana-Forensic00/actions/workflows/field-test.yml)
 +[![Security Audit](https://github.com/mitchell5584dm-tech/00Arcana-Forensic00/actions/workflows/security.yml/badge.s
vg)](https://github.com/mitchell5584dm-tech/00Arcana-Forensic00/actions/workflows/security.yml)
 +[![License](https://img.shields.io/badge/license-MIT%2FCommercial-blue.svg)](LICENSE)
 +[![Rust](https://img.shields.io/badge/rust-1.75%2B-000000?logo=rust)](https://www.rust-lang.org)
 +[![Crate](https://img.shields.io/crates/v/arcana-acquire)](https://crates.io/crates/arcana-acquire)
 +
 +**Air-Gapped Digital Evidence Acquisition & Immutable Custody Chain**
 +
 +[Documentation](https://docs.arcana-forensics.com) · [Live Demo](https://arcana-forensics.com/try) · [Pricing](https
://arcana-forensics.com/pricing)
 +
 +</div>
 +
 +---
 +
 +## Overview
++=======
+ [![CI](https://github.com/mitchell5584dm-tech/00Arcana-Forensic00/actions/workflows/field-test.yml/badge.svg)](https
://github.comitchell5584dm-tech/00Arcana-Forensic00/actions/workflows/field-test.yml)
+ [![License](https://img.shields.io/badge/license-MIT%2FCommercial-blue.svg)](LICENSE)
+ 
+ **Air-Gapped Digital Evidence Acquisition & Immutable Custody Chain**
+ 
+ ## Overview
+ 
+ Arcana is a **military-grade forensic acquisition engine** for environments where evidence integrity is non-negotiab
le.
+ 
+ ## Quick Start
+ cargo build --release --locked
+ ./target/release/arcana-acquire acquire --path ./evidence --out ./vault --operator analyst --case-id TEST-001
+ 
+ ## Licensing
+ 
+ | Tier | Price | Best For |
+ |:---:|---|---|
+ | Community | FREE (MIT) | Researchers |
+ | Professional | $3,500/seat | Boutique labs |
+ | Enterprise | $35,000/org | Law firms |
+ | Federal | $150,000+ | Government |
+ 
+ **Immutable custody. Cryptographic integrity. Zero trust.**
+ Public catalog: [site/pricing.html](site/pricing.html) · https://arcana-forensics.com/site/pricing.html  
+ Stripe playbook: [docs/STRIPE.md](docs/STRIPE.md)
++>>>>>>> 37c9a8d (docs: update README and add security documentation)
  
 -The MIT grant on the source does not change. Paid SKUs are seat/org entitlements billed on Stripe. A receipt is not a custody exhibit. The binary does not testify.
 +Arcana is a **military-grade forensic acquisition engine** designed for environments where evidence integrity is non-negotiable. Built in Rust with zero network dependencies, it provides a cryptographically verifiable chain of custody from acquisition to the courtroom.
  
 -## Inspection policy
 +### Core Capabilities
  
 -Review this pack through the **raw source** (`crates/*/src/`) and synthetic demo files only. Do not open live vault blobs, `custody.sqlite` from a real matter, or customer paths to “test” the tool. Policy: [docs/STATIC_REVIEW.md](docs/STATIC_REVIEW.md).
 +| Feature | Implementation | Standard |
 +|---------|---------------|----------|
 +| **Air-Gapped Acquisition** | Zero network stack integration | NIST SP 800-86 |
 +| **Vault Encryption** | AES-256-GCM + Argon2id | FIPS 197 |
 +| **Custody Ledger** | SHA-256 hash chain + SQLite | ISO 27037 |
 +| **Path Confinement** | Canonicalization + sandboxing | OSSTMM |
 +| **Memory Safety** | Rust ownership model | CWE-416 elimination |
  
 -Automated CI is hard-wired to `demo/opensource/01-acquire/evidence` and uploads only a one-line confirmation text file — never a case directory.
 +> **⚠️ Scope Declaration:** This is a **read-only acquisition tool**. Previous iterations included destructive operations—these have been **permanently removed**. Arcana acquires; it does not modify or destroy.
  
 -## Live field test (download this)
 +---
  
 -| What | Link |
 -|---|---|
 -| **Download current `main`** | https://github.com/mitchell5584dm-tech/00Arcana-Forensic00/archive/refs/heads/main.zip |
 -| Domain | https://arcana-forensics.com |
 -| Evaluator page | [site/try.html](site/try.html) |
 -| Licensing | [site/pricing.html](site/pricing.html) |
 -| Passing run | https://github.com/mitchell5584dm-tech/00Arcana-Forensic00/actions/runs/35586146734 |
 -| Paperwork | [docs/FIELD_TEST.md](docs/FIELD_TEST.md) · packet **AF-FT-2026-0921** |
 -
 -Last automated confirmation: **PASS** on `a7fd388` at `2026-09-21T09:58:23Z` (`operator=ci-field-test`).
 +## Quick Start
  
  ```bash
 +# 1. Clone and verify signature
  git clone https://github.com/mitchell5584dm-tech/00Arcana-Forensic00.git
  cd 00Arcana-Forensic00
 -python3 demo/scripts/make_evidence.py
 -cargo test --workspace
 -cargo build -p arcana-acquire
 -export ARCANA_VAULT_PASSWORD='trial-pack-passphrase'
 -./target/debug/arcana-acquire acquire \
 -  --path demo/opensource/01-acquire/evidence \
 -  --out ./cases/live-test \
 -  --operator field-tester \
 -  --case-id live-test-001
 -./target/debug/arcana-acquire verify --case ./cases/live-test
 -```
 -
 -## Layout
 -
 -```text
 -crates/
 -  arcana-core      shared errors, hashing, path confinement, magic hints
 -  arcana-vault     stretched passphrase + AES-256-GCM seal / unseal
 -  arcana-custody   SQLite append-only hash chain
 -  arcana-acquire   CLI: acquire | verify | export-manifest
 -```
 +git verify-commit HEAD  # Signed releases only
  
 -## How to run
 +# 2. Build with release optimizations
 +cargo build --release --locked
  
 -```bash
 -cargo test --workspace
 -cargo build --release -p arcana-acquire
 +# 3. Generate synthetic evidence for testing
 +python3 demo/scripts/make_evidence.py
  
 -export ARCANA_VAULT_PASSWORD='correct horse battery staple extra'
 +# 4. Execute field test
 +export ARCANA_VAULT_PASSWORD='your-secure-passphrase'
  ./target/release/arcana-acquire acquire \
 -  --path ./demo/opensource/01-acquire/evidence \
 -  --out ./cases/demo \
 -  --operator 'investigator' \
 -  --case-id demo-001
 -
 -./target/release/arcana-acquire verify \
 -  --case ./cases/demo \
 -  --password "$ARCANA_VAULT_PASSWORD"
 -```
 -
 -Requirements: Rust 1.75+, a C compiler (for bundled SQLite).
 -
 -## Vault format
 -
 -```
 -ARCN | version:u8 | salt:16 | nonce:12 | AES-256-GCM(ciphertext || tag)
 -```
 -
 -## What this tool will not do
 -
 -- It will not erase disks, issue ATA Secure Erase, format NVMe, or destroy LUKS headers.
 -- It will not follow symlinks or copy device nodes.
 -- It will not send telemetry.
 -- It will not take card numbers. Stripe hosts checkout.
 -
 -Use only on systems and files you are authorized to examine.
 -
 -## License
 -
 -Community source: MIT. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
 -Paid seats: [docs/STRIPE.md](docs/STRIPE.md).
 -
 -## Demo packs
 -
 -| Pack | Path | Purpose |
 -|---|---|---|
 -| Community / open source | `demo/opensource/` | acquire / vault / custody / site samples |
 -| Professional trial (14-day) | `demo/trial/` | 5-file cap, passphrase `trial-pack-passphrase` |
 +  --path demo/opensource/01-acquire/evidence \
 +  --out ./cases/test-run \
 +  --operator "forensic-analyst" \
 +  --case-id TEST-001
  
 -See `demo/README.md`.
 +# 5. Verify cryptographic integrity
 +./target/release/arcana-acquire verify --case ./cases/test-run
(END)
