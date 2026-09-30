# Arcana Restore: security notes

Status: **self-reviewed, not independently audited.** Do not describe it as audited, certified or court-approved until a third party has reviewed it (see `AUDIT_SCOPE.md`).

## What it protects, and against whom
| Goal | Mechanism | Holds against |
|---|---|---|
| Confidentiality of sealed evidence at rest | Argon2id (t=3, m=64 MiB, p=4, per-file salt) then AES-256-GCM, fresh key per vault | Someone who copies the vault but lacks the passphrase |
| Tamper detection of a vault | The whole header (including KDF parameters) is GCM associated data; any changed byte fails authentication | Edits to header or ciphertext, truncation, forged KDF parameters |
| Evidence fidelity | The original is sealed byte-identical with its SHA-256 in the encrypted manifest; repaired pixels are recorded in a mask | Silent alteration of the original by the tool |
| Custody record | SHA-256 hash chain in `ledger.jsonl` | Edits, reordering or deletion of **middle** entries |
| Safe handling of hostile inputs | Magic-byte check, 100 MiB / 100 MP limits, symlink/junction refusal, no overwrite, sanitized output names | Crafted file names, oversized images, symlink swaps |
| Privacy of file names | Names live only in the encrypted manifest; vault file name and ledger carry hashes only | Someone reading the vault folder |

## Known limitations (read before selling or relying on it)
1. **The ledger is tamper-evident, not tamper-proof.** It is unkeyed: anyone who can write the folder can rebuild a fresh, self-consistent chain. Removed *trailing* entries are also invisible. Record the printed head hash somewhere independent (or anchor it with a timestamping service) and verify with `--expect-head`.
2. **No secure memory handling.** Python cannot reliably wipe passphrases or decrypted data from RAM, and they may reach swap or crash dumps. Use an encrypted disk and a trusted machine.
3. **Passphrase via `ARCANA_PASSPHRASE`** is visible to other processes of the same user. Prefer the prompt or a locked-down `--passphrase-file`.
4. **Image decoders parse untrusted files.** OpenCV bundles libpng/libjpeg/libtiff; a memory-safety bug there is out of our control. Keep OpenCV current, process evidence from a low-privilege account, and consider a sandbox for hostile sources.
5. **Timestamps come from the local clock** and are not independently attested.
6. **Symlink/junction check is check-then-open** (Windows has no `O_NOFOLLOW`). A local attacker who can swap files during a run could race it. Use folders only trusted users can write.
7. **Windows file permissions:** the `0600` mode is a no-op; vaults inherit the folder ACL.
8. **Repair is interpolation**, not recovery. It is labeled as such and never replaces the original.
9. **Supply chain:** dependencies are version-ranged, not hash-pinned, and workflow actions are pinned by tag not commit. Pin both before shipping commercial releases.
10. **Not FIPS-validated;** cryptography comes from the `cryptography` package (OpenSSL).
11. A vault sealed but whose ledger write then fails is reported as failed although the file exists (rare; disk-full or permission errors).

## Issues found in our own review and fixed
| Finding | Fix |
|---|---|
| Windows followed symlinks (no `O_NOFOLLOW`) | Explicit symlink/junction check on reads, vault opens and extraction writes |
| Original file names leaked in vault file names and the ledger despite "names are encrypted" | Names now only in the encrypted manifest; vault is `evidence-<hash>-<rand>.arcr` |
| Identical files collided on the vault name, risking refusal or loss of the second exhibit's context | Random suffix; every vault is independent, nothing is ever overwritten |
| Extraction could write some files, then fail on an existing one (partial output) | All destinations are checked before anything is written |
| Sealing failed on FAT/exFAT drives and some network shares (no hard links) | Exclusive-create fallback; still never replaces an existing file |
| Release workflow exposed signing secrets to every step, including dependency installs | Secrets are attached only to the signing steps |

## Reporting
Email sales@arcana-forensics.com with details. Please allow reasonable time before public disclosure.
