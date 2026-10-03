# Independent security review: scope for an external auditor

**Goal:** an independent review of `arcana-restore` (v0.1.0) sufficient to support statements such as "independently reviewed". Budget and report format are for the vendor to agree with the reviewer.

## Code in scope (about 1,100 lines of Python, `restore/src/arcana_restore/`)
| File | Why it matters |
|---|---|
| `vault.py` | Container format `ARCR` v1: Argon2id key derivation, AES-256-GCM, header authentication, parameter bounds |
| `pipeline.py` | File acquisition (symlink/size/type checks), atomic no-overwrite writes, extraction and integrity checks |
| `ledger.py` | SHA-256 hash-chained custody log, locking, verification |
| `imaging.py` | Decoding of untrusted images, resource limits, repair and reading-order heuristics |
| `video.py` | Decoding of untrusted video (temp copy, limits), frame alignment and glare compositing |
| `cli.py`, `gui.py` | Passphrase handling, user-facing flows |
| `.github/workflows/restore-release.yml`, `packaging/` | Build, signing and release pipeline |

Out of scope: the Rust `arcana-acquire` crates (separate format `ARCN` v1) and the marketing site.

## Design summary
- Per vault: random 16-byte salt and 12-byte nonce; key = Argon2id(passphrase, salt); AES-256-GCM over `manifest || original || restored || mask`; associated data is the whole prefix (magic, version, header length, header JSON). The header holds only KDF parameters and entry sizes.
- Extraction verifies each entry's SHA-256 against the authenticated manifest.
- Ledger entry hash = SHA-256 of canonical JSON of `{seq, ts, event, data, prev}`.

## Questions we want answered
1. Is the container format sound (nonce/key uniqueness, AAD coverage, header parsing, downgrade or parameter-substitution attacks)?
2. Are the Argon2id parameters and the 12-character minimum passphrase adequate for the intended threat model?
3. Can a crafted image, video or vault cause memory exhaustion, crashes or code execution (decoders, limits, JSON handling)?
4. Do path handling, symlink/junction checks and output naming hold on Windows, macOS and Linux, including race conditions?
5. Are the ledger's integrity claims accurately stated? Should a keyed MAC or external timestamp anchoring be mandatory?
6. Are the release workflow, secret handling and dependency pinning adequate? Is reproducible build feasible?
7. Do the documentation claims (README, `SECURITY.md`, Quick Start) match actual behavior?

## Materials for the reviewer
- Source, 45 automated tests (`pytest restore`), and `SECURITY.md` (threat model, known limitations, findings already fixed).
- A way to build: `python restore/packaging/build.py`.
- Suggested extras to request: fuzzing of `vault.parse_header` and `imaging.decode_image`, dependency audit (`pip-audit`), review of signing/notarization configuration.

## Choosing a reviewer
Look for a firm with applied-cryptography and application-security experience and public reports (for example firms that publish audits of open-source cryptographic tools). Ask for a fixed-scope quote, a retest of fixes, and permission to publish a summary.
