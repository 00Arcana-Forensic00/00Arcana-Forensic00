# Arcana Forensics

[![field-test](https://github.com/mitchell5584dm-tech/00Arcana-Forensic00/actions/workflows/field-test.yml/badge.svg)](https://github.com/mitchell5584dm-tech/00Arcana-Forensic00/actions/workflows/field-test.yml)

Air-gapped filesystem acquisition, AES-256-GCM vault isolation, and a SHA-256 hash-chained custody ledger. Written in Rust.

This tree is a **compiling workspace**. The previous layout listed crates that did not exist and shipped a disk-wipe prototype as `arcana-acquire`. That destructive path is gone.

## Licensing (audit-grade)

| Tier | Price | Audience |
|---|---|---|
| Community Edition | Free (MIT) | researchers, this public tree |
| Professional License | $3,500 / year / seat | boutique labs, solo examiners |
| Enterprise License | $35,000 / year | law firms, corporate security; unlimited seats in one org |
| Government / Federal | custom, from $150,000 / year | quote only; FedRAMP / CJIS / ITAR when required |
| Professional services | $250–$500 / hour | deployment, training, separately scoped expert-witness engagement |

Public catalog: [site/pricing.html](site/pricing.html) · https://arcana-forensics.com/site/pricing.html  
Stripe playbook: [docs/STRIPE.md](docs/STRIPE.md)

The MIT grant on the source does not change. Paid SKUs are seat/org entitlements billed on Stripe. A receipt is not a custody exhibit. The binary does not testify.

## Inspection policy

Review this pack through the **raw source** (`crates/*/src/`) and synthetic demo files only. Do not open live vault blobs, `custody.sqlite` from a real matter, or customer paths to “test” the tool. Policy: [docs/STATIC_REVIEW.md](docs/STATIC_REVIEW.md).

Automated CI is hard-wired to `demo/opensource/01-acquire/evidence` and uploads only a one-line confirmation text file — never a case directory.

## Live field test (download this)

| What | Link |
|---|---|
| **Download current `main`** | https://github.com/mitchell5584dm-tech/00Arcana-Forensic00/archive/refs/heads/main.zip |
| Domain | https://arcana-forensics.com |
| Evaluator page | [site/try.html](site/try.html) |
| Licensing | [site/pricing.html](site/pricing.html) |
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
- It will not take card numbers. Stripe hosts checkout.

Use only on systems and files you are authorized to examine.

## License

Community source: MIT. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
Paid seats: [docs/STRIPE.md](docs/STRIPE.md).

## Demo packs

| Pack | Path | Purpose |
|---|---|---|
| Community / open source | `demo/opensource/` | acquire / vault / custody / site samples |
| Professional trial (14-day) | `demo/trial/` | 5-file cap, passphrase `trial-pack-passphrase` |

See `demo/README.md`.
