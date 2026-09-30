# Arcalume (arcana-restore)

**Arcalume** is the app: it recovers photographed documents damaged by glare and shadow,
shows exactly which pixels were filled in, and seals the untouched original with the result
in a passphrase-encrypted vault with a hash-chained custody ledger. Everything runs on the
device; the app makes no network connections. `arcana-restore` is the Python package and
command line underneath it.

```bash
pip install './restore[app]'
arcalume                                            # the app window (pywebview)
python -m arcana_restore.app.devserver              # same UI in a browser, for development
```

Store listing, privacy policy, screenshots and the submission checklist are in [`store/`](store/);
the competitor and accessibility research is in [`docs/BENCHMARK.md`](docs/BENCHMARK.md) and
[`docs/ACCESSIBILITY.md`](docs/ACCESSIBILITY.md).

## Plans and licensing
Free: recover, compare, see filled areas, open any vault, check any ledger, save watermarked copies.
Pro: clean copies, sealing with the custody ledger, several pages at once. Keys are Ed25519-signed
and checked offline (`src/arcana_restore/licensing.py`); `packaging/license_tool.py` creates the
signing key and issues keys by hand; `../license-worker/` issues them after a Stripe checkout.
Store builds (`packaging/build.py --edition store`) are unlocked because the store takes payment.

## Command line
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

## What the recovery is
1. **Illumination flattening:** each channel is divided by a smooth estimate of the page background.
   Text that shadows or uneven light dimmed but did not clip comes back (tested: F1 from under 0.5
   to over 0.95 on a shadowed column).
2. **Glare halo stretch:** around each glare spot, local contrast is restored so washed-out ink is dark again.
3. **Inpainting of clipped glare cores** (Telea). Clipped pixels hold no data; filling them hides the
   blown-out spot but cannot bring back text, and a test asserts it does not. Every filled pixel is in the mask.

Large pure-black regions are reported and left alone unless `--fill-shadow` is given (they are often
redactions). Damage over 30% of the image is reported and nothing is changed. Reading order is a
recursive XY-cut over detected blocks (columns before rows), geometry only. The engine came from
`arcana-recon` (draft PR #1) and now lives in `imaging.py`.

## Develop
```bash
pip install -e './restore[test]' && pytest restore
```
Tests cover round trips, tamper/truncation/forged-header rejection, wrong passphrase, fresh-process extraction, ledger edits and concurrency, hostile inputs and repair behavior.

## Desktop app and installers
The installers ship the Arcalume window. The earlier Tk window is still available as `arcana-restore gui`.
```bash
arcana-restore gui                      # from a Python install
python restore/packaging/build.py       # builds dist/Arcalume (app) + dist/arcana-restore (CLI) for this OS; add --edition store for store packages
python restore/packaging/smoke.py restore/dist/arcana-restore
```
Installers come from the `restore-release` workflow (manual run, or push a `restore-vX.Y.Z` tag to publish a GitHub Release with checksums):

| OS | Download | What the user does |
|---|---|---|
| Windows | `Arcalume-Setup-X.exe` | double-click; Start menu entry and optional desktop shortcut; per-user, no admin prompt |
| macOS | `Arcalume-X-macos.dmg` | drag "Arcalume" to Applications |
| Linux | `Arcalume-X-linux.tar.gz` | extract, run `./install.sh --desktop` |

**Status:** Linux is built and tested here (CLI smoke test, installer script, window launch, automated widget tests under Xvfb). The Windows installer, macOS dmg, and the signing/notarization steps are written but have not been run: run the workflow once before shipping. Builds are unsigned unless these repository secrets exist: `WIN_CERT_PFX_BASE64`, `WIN_CERT_PASSWORD` (Windows) and `APPLE_CERT_P12_BASE64`, `APPLE_CERT_PASSWORD`, `APPLE_SIGN_IDENTITY`, `APPLE_ID`, `APPLE_TEAM_ID`, `APPLE_APP_PASSWORD` (macOS). Unsigned installers trigger SmartScreen/Gatekeeper warnings. The app icon is a placeholder (`packaging/icons/icon.png`): replace it and run `python packaging/make_icons.py --from-png`, which also regenerates the Microsoft Store tiles. The ledger file lock is POSIX-only (Windows serializes threads, not separate processes).
