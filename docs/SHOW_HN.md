# Show HN packet

Post as **Show HN**. Weekday morning US. One primary link: the GitHub repo.
Do not lead with price, FedRAMP, or “audit-grade.”

## Title (pick one)

Best:

```
Show HN: Arcana – air-gapped file acquisition, AES-GCM vault, hash-chained custody (Rust)
```

Alternates:

```
Show HN: Offline forensic acquire/seal/verify in a small Rust workspace
Show HN: I replaced a broken “forensics” tree with a compiling air-gapped acquire CLI
```

## Post body

```
Show HN: Arcana Forensics

I needed a small offline pipeline: walk a directory of regular files, hash them,
seal copies with AES-256-GCM, and append a local SHA-256 hash chain in SQLite.
No cloud, no telemetry, no disk wipe.

Repo: https://github.com/mitchell5584dm-tech/00Arcana-Forensic00
Site: https://arcana-forensics.com
One-zip demo: https://github.com/mitchell5584dm-tech/00Arcana-Forensic00/archive/refs/heads/main.zip

What it does
- acquire: confined walk (no symlinks, no device nodes), SHA-256, seal to .arcv
- verify: unseal + re-hash + check the custody chain
- export-manifest: relative paths only (no host paths)

Vault blob: ARCN | version | salt(16) | nonce(12) | AES-256-GCM(ciphertext||tag)
KDF in this tree is 100k rounds of SHA-256 so it still builds on Rust 1.75.
Argon2id is the intended upgrade.

What it does not do
- wipe disks / ATA Secure Erase / NVMe format / LUKS destroy
- follow symlinks or copy special files
- phone home
- take card numbers (that is Stripe on the marketing pages, not the CLI)
- stand in as expert testimony

Try it (synthetic files only):

  git clone https://github.com/mitchell5584dm-tech/00Arcana-Forensic00.git
  cd 00Arcana-Forensic00
  cargo test --workspace
  cargo build -p arcana-acquire
  export ARCANA_VAULT_PASSWORD='REPLACE_WITH_PASSPHRASE'
  ./target/debug/arcana-acquire acquire \
    --path demo/single/evidence \
    --out ./cases/demo-001 \
    --operator hn \
    --case-id demo-001
  ./target/debug/arcana-acquire verify --case ./cases/demo-001

CI field-test is hard-wired to demo/ and uploads a text confirmation, not a case
directory. Inspection policy is source-level: docs/STATIC_REVIEW.md

Licensing: Community is MIT and free. Paid seats exist (Pro $3.5k/seat/yr,
Enterprise $35k/yr) if you want support; you do not need them to build or run
the demo. A Stripe receipt is not a chain-of-custody exhibit.

Happy to hear what you would change on the KDF, the vault header, or the ledger
canonicalization.
```

## First comment (post immediately)

```
Single demo packet with four synthetic files is demo/single/.

I will not run acquire against anyone's real disk image in this thread.
If you review it, please review crates/*/src — that is the product.
```

## Hygiene

- Title area link = GitHub repo. Domain goes in the body.
- Do not paste the full price table in the title.
- Do not claim FedRAMP / CJIS / ITAR unless the authorization exists.
- Do not say “court ready.”
- Reply to KDF / nonce / lockfile / SQLite comments first.
- Short answer to “just use dd + gpg”: yes for one file; this is acquire + per-object nonce + a hash chain in one CLI.
