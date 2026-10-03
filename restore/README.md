# Arcana Restore

Repairs glare/shadow damage in photographed documents, maps reading order, and seals the result in a passphrase-encrypted vault with a hash-chained custody ledger. It is the productized form of the earlier prototype scripts.

```bash
pip install ./restore
arcana-restore process ./damaged_scans -o ./vault          # prompts for a passphrase (12+ chars)
arcana-restore extract ./vault/evidence-….arcr -o ./out
arcana-restore verify-ledger --vault ./vault [--expect-head <hash>]
arcana-restore inspect ./vault/….arcr                       # header only, no passphrase
```
The passphrase comes from `--passphrase-file`, `ARCANA_PASSPHRASE`, or a hidden prompt. It is never accepted on the command line.

## Inputs: photos, screenshots and short videos
PNG, JPEG, TIFF and BMP images (HEIC/AVIF are recognised and rejected with instructions to export as JPEG), and MP4 / MOV / AVI / WebM / MKV videos (up to 250 MiB). For a **video of a document**, the glare moves as the camera moves, so Arcana Restore picks sharp frames, aligns them to the sharpest one and replaces blown-out pixels with the matching clean pixels from other frames. These are real captured pixels, not guesses; anything still unrecoverable goes through the normal inpainting. Every pixel it changed is marked in the mask; all other pixels are exactly as captured in the reference frame. Needs: a page with some texture or text (so frames can be aligned), glare that moves between frames, and at least 3 alignable frames (otherwise it falls back to the sharpest single frame and says so in the report). The restored image is at most 1920 px on its longest side. Static glare (a light fixed relative to the page) cannot be fixed by moving the camera. The original video is sealed byte-identical.

## What each vault contains
| entry | meaning |
|---|---|
| `original` | the acquired file, byte-identical (SHA-256 recorded) |
| `restored` | repaired PNG; a derivative |
| `mask` | every pixel that may have been synthesized |
| `manifest` | source name, hashes, repair report, reading-order blocks |

## Security properties (and their limits)
- **Format `ARCR` v1:** Argon2id (t=3, m=64 MiB, p=4, per-file salt) -> AES-256-GCM. The entire header, including KDF parameters, is authenticated. File names and hashes live only inside the encrypted manifest (vault files are named `evidence-<hash>-<random>.arcr`, and the ledger records hashes only). Crafted headers are bounds-checked before any KDF work.
- **Works across processes:** unlike the prototype, nothing depends on in-memory state; a vault opens anywhere with its passphrase.
- **Windows:** the 0600 file mode is a no-op (files inherit the folder's ACL), so keep vaults in a per-user folder. Symlinks and junctions are refused by an explicit check, because Windows has no `O_NOFOLLOW`.
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

**More:** `docs/SECURITY.md` (threat model, limitations, findings fixed), `docs/AUDIT_SCOPE.md` (brief for an external reviewer), `docs/SIGNING.md` (certificates and secrets).

## Exit codes and troubleshooting
Exit codes (command line): `0` success; `1` a file failed or an I/O problem (file exists, no space, no permission); `2` usage error, wrong passphrase, or not a valid vault. Errors are always one plain line, never a traceback.

| Symptom | Cause and fix |
|---|---|
| "Unsupported file type" | The file is not a supported photo/video. Use PNG, JPEG, TIFF, BMP or MP4/MOV/AVI/WebM/MKV. |
| "HEIC/AVIF photos are not supported yet" | iPhone photo format. Export or share it as JPEG. |
| "authentication failed: wrong passphrase or the vault was modified" | Wrong passphrase, or the `.arcr` file was altered or damaged. There is no recovery. |
| "already exists; nothing was written" | The output folder already has files from this vault. Choose another folder or use `--force`. |
| `verify-ledger` says "no ledger file found" | Wrong folder: pick the vault folder that holds `ledger.jsonl`. |
| Window will not start on Linux (`No module named tkinter`) | `sudo apt install python3-tk` when running from source. The packaged app already includes Tk. |
| Desktop icon will not launch (Linux) | Right-click it and choose "Allow Launching" (the installer tries to do this for you). |
| Video "frames could not be aligned" | The page needs visible text or texture and the camera must move slowly with the whole page in view. |

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
| Linux | `ArcanaRestore-X-linux.tar.gz` | extract, run `./install.sh` |

**Status:** Linux is built and tested here (CLI smoke test, installer script, window launch, automated widget tests under Xvfb). The Windows installer, macOS dmg, and the signing/notarization steps are written but have not been run: run the workflow once before shipping. Builds are unsigned unless these repository secrets exist: `WIN_CERT_PFX_BASE64`, `WIN_CERT_PASSWORD` (Windows) and `APPLE_CERT_P12_BASE64`, `APPLE_CERT_PASSWORD`, `APPLE_SIGN_IDENTITY`, `APPLE_ID`, `APPLE_TEAM_ID`, `APPLE_APP_PASSWORD` (macOS). Unsigned installers trigger SmartScreen/Gatekeeper warnings. The app icon is a placeholder (`packaging/icons/icon.png`): replace it and run `python packaging/make_icons.py --from-png`. The ledger file lock is POSIX-only (Windows serializes threads, not separate processes).
