# Arcana Restore

Repairs glare/shadow damage in photographed documents, maps reading order, and seals the result in a passphrase-encrypted vault with a hash-chained custody ledger. It is the productized form of the earlier prototype scripts.

```bash
pip install ./restore
arcana-restore process ./damaged_scans -o ./vault          # prompts for a passphrase (12+ chars)
arcana-restore extract ./vault/receipt.png-ab12….arcr -o ./out
arcana-restore verify-ledger --vault ./vault [--expect-head <hash>]
arcana-restore inspect ./vault/….arcr                       # header only, no passphrase
```
The passphrase comes from `--passphrase-file`, `ARCANA_PASSPHRASE`, or a hidden prompt. It is never accepted on the command line.

## What each vault contains
| entry | meaning |
|---|---|
| `original` | the acquired file, byte-identical (SHA-256 recorded) |
| `restored` | repaired PNG; a derivative |
| `mask` | every pixel that may have been synthesized |
| `manifest` | source name, hashes, repair report, reading-order blocks |

## Security properties (and their limits)
- **Format `ARCR` v1:** Argon2id (t=3, m=64 MiB, p=4, per-file salt) -> AES-256-GCM. The entire header, including KDF parameters, is authenticated. File names and hashes live only inside the encrypted manifest. Crafted headers are bounds-checked before any KDF work.
- **Works across processes:** unlike the prototype, nothing depends on in-memory state; a vault opens anywhere with its passphrase.
- **Input hardening:** magic-byte check, 100 MiB and 100 MP limits, symlinks and non-regular files refused, no overwrite of existing vaults or extracted files, outputs created 0600, names sanitized.
- **Custody ledger:** SHA-256 chain in `ledger.jsonl`, cross-process locked and fsynced. A chain cannot reveal removed *trailing* entries; record the printed head elsewhere (or anchor it, see `docs/ANCHORING.md`) and use `--expect-head`.
- **Not provided:** a lost passphrase is unrecoverable by design. There is no key escrow, no secure memory wiping in Python, no protection against a compromised host, and no independent security audit yet. Do not describe it as audited or court-certified until it is.

## What the repair is
Glare and deep shadow are found by thresholding, filtered to compact regions so black text on white paper is left alone, then filled by Telea inpainting. Damage over 30% of the image is reported and not repaired. This is interpolation: it can make text easier to see, never proves what the missing text said. Use the mask and original when the result matters. Reading order is a geometric column heuristic, not semantic understanding.

## Develop
```bash
pip install -e './restore[test]' && pytest restore
```
Tests cover round trips, tamper/truncation/forged-header rejection, wrong passphrase, fresh-process extraction, ledger edits and concurrency, hostile inputs and repair behavior.

## Standalone executable
```bash
restore/packaging/build.sh          # builds restore/dist/arcana-restore (+ SHA256SUMS) for this OS
python restore/packaging/smoke.py restore/dist/arcana-restore
```
The `restore-build` workflow (manual run, or a `restore-v*` tag) builds Linux, Windows and macOS executables and smoke-tests each one. PyInstaller output is OS-specific, so build on the target OS. Linux is verified; Windows and macOS builds have not been run yet, and the ledger file lock is POSIX-only (on Windows, concurrent *processes* are not serialized; threads are). Binaries are unsigned: code-sign and notarize before distributing to customers, and publish the SHA256SUMS.
