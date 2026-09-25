# Security Policy

## Supported versions

`0.1.x` on branch `main` is the only supported line.

## Product boundary

Arcana Forensics is an **offline-first acquisition and sealing toolkit**.

It does:

- walk an operator-specified directory of regular files
- refuse symlinks and special files
- confine output paths to the case directory
- hash files with SHA-256
- seal copies with stretched-passphrase AES-256-GCM
- append a local hash-chained SQLite custody ledger

It does **not**:

- wipe disks, run ATA Secure Erase, format NVMe namespaces, or erase LUKS headers
- phone home, upload evidence, or require a network
- treat a printed ledger line as a court-ready expert opinion by itself

Operators remain responsible for legal authority, consent, and their own evidence-handling procedures.

## Cryptography

- Key derivation: 100,000 rounds of SHA-256 over passphrase||salt (Rust 1.75-compatible stretch; Argon2id is the intended upgrade when the toolchain allows it)
- Sealing: AES-256-GCM with a random 12-byte nonce per object
- Vault blob: `ARCN | version | salt(16) | nonce(12) | ciphertext+tag`
- Custody linkage: SHA-256 over canonical `ts|operator|action|path|sha256|prev_hash`

Passphrases must be at least 12 characters. Prefer `ARCANA_VAULT_PASSWORD` from a local secret store over argv.

## Reporting a vulnerability

Email `security@arcana-forensics.com' with:

- affected commit SHA
- reproduction steps
- impact (integrity, confidentiality, or availability)

Do not open a public issue for an exploitable flaw until a fix is available.
