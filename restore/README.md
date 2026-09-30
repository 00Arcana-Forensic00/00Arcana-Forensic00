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

## Desktop app and installers
Double-click app with a window (Seal evidence / Open vault / Verify ledger), drag-and-drop for images, and an app icon:
```bash
arcana-restore gui                      # from a Python install
python restore/packaging/build.py       # builds dist/ArcanaRestore (app) + dist/arcana-restore (CLI) for this OS
python restore/packaging/smoke.py restore/dist/arcana-restore
```
Installers come from the `restore-release` workflow (manual run, or push a `restore-vX.Y.Z` tag to publish a GitHub Release with checksums):

| OS | Download | What the user does |
|---|---|---|
| Windows | `ArcanaRestore-Setup-X.exe` | double-click; Start menu entry and optional desktop shortcut; per-user, no admin prompt |
| macOS | `ArcanaRestore-X-macos.dmg` | drag "Arcana Restore" to Applications |
| Linux | `ArcanaRestore-X-linux.tar.gz` | extract, run `./install.sh --desktop` |

**Status:** Linux is built and tested here (CLI smoke test, installer script, window launch, automated widget tests under Xvfb). The Windows installer, macOS dmg, and the signing/notarization steps are written but have not been run: run the workflow once before shipping. Builds are unsigned unless these repository secrets exist: `WIN_CERT_PFX_BASE64`, `WIN_CERT_PASSWORD` (Windows) and `APPLE_CERT_P12_BASE64`, `APPLE_CERT_PASSWORD`, `APPLE_SIGN_IDENTITY`, `APPLE_ID`, `APPLE_TEAM_ID`, `APPLE_APP_PASSWORD` (macOS). Unsigned installers trigger SmartScreen/Gatekeeper warnings. The app icon is a placeholder (`packaging/icons/icon.png`): replace it and run `python packaging/make_icons.py --from-png`. The ledger file lock is POSIX-only (Windows serializes threads, not separate processes).
