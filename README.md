# Arcana Forensics

[![field-test](https://github.com/mitchell5584dm-tech/00Arcana-Forensic00/actions/workflows/field-test.yml/badge.svg)](https://github.com/mitchell5584dm-tech/00Arcana-Forensic00/actions/workflows/field-test.yml)

Air-gapped filesystem acquisition, AES-256-GCM vault isolation, and a SHA-256 hash-chained custody ledger. Written in Rust.

This tree is a **compiling workspace**. The previous layout listed crates that did not exist and shipped a disk-wipe prototype as `arcana-acquire`. That destructive path is gone.

## Live field test (download this)

| What | Link |
|---|---|
| **Download current `main`** | https://github.com/mitchell5584dm-tech/00Arcana-Forensic00/archive/refs/heads/main.zip |
| Evaluator page | [site/try.html](site/try.html) |
| Passing run | https://github.com/mitchell5584dm-tech/00Arcana-Forensic00/actions/runs/35586146734 |
| Paperwork | [docs/FIELD_TEST.md](docs/FIELD_TEST.md) · packet **AF-FT-2026-0921** |

Last automated confirmation: **PASS** on `a7fd388` at `2026-09-21T09:58:23Z` (`operator=ci-field-test`).

```bash
git clone https://github.com/mitchell5584dm-tech/00Arcana-Forensic00.git
cd 00Arcana-Forensic00
python3 demo/scripts/make_evidence.py
cargo test --workspace
cargo build -p arcana-acquire
export ARCANA_VAULT_PASSWORD='trial-pack-passphrase'
./target/debug/arcana-acquire acquire \
  --path demo/opensource/01-acquire/evidence \
  --out ./cases/live-test \
  --operator field-tester \
  --case-id live-test-001
./target/debug/arcana-acquire verify --case ./cases/live-test
```

## Layout

```text
crates/
  arcana-core      shared errors, hashing, path confinement, magic hints
  arcana-vault     stretched passphrase + AES-256-GCM seal / unseal
  arcana-custody   SQLite append-only hash chain
  arcana-acquire   CLI: acquire | verify | export-manifest
```

## How to run

```bash
cargo test --workspace
cargo build --release -p arcana-acquire

export ARCANA_VAULT_PASSWORD='correct horse battery staple extra'
./target/release/arcana-acquire acquire \
  --path ./demo/opensource/01-acquire/evidence \
  --out ./cases/demo \
  --operator 'investigator' \
  --case-id demo-001

./target/release/arcana-acquire verify \
  --case ./cases/demo \
  --password "$ARCANA_VAULT_PASSWORD"
```

Requirements: Rust 1.75+, a C compiler (for bundled SQLite).

## Vault format

```
ARCN | version:u8 | salt:16 | nonce:12 | AES-256-GCM(ciphertext || tag)
```

## What this tool will not do

- It will not erase disks, issue ATA Secure Erase, format NVMe, or destroy LUKS headers.
- It will not follow symlinks or copy device nodes.
- It will not send telemetry.

Use only on systems and files you are authorized to examine.

## License

MIT. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

## Demo packs

| Pack | Path | Purpose |
|---|---|---|
| Open source | `demo/opensource/` | acquire / vault / custody / site samples |
| Trial (14-day) | `demo/trial/` | 5-file cap, passphrase `trial-pack-passphrase`, enterprise schema preview |

See `demo/README.md`.
