# Google Play listing: Arcalume

Every claim below maps to code and a test. Nothing is claimed that the app does not do.
Character limits are Play Console's.

**App name (30):** `Arcalume: Document Forensics` (28)

**Short description (80):**
`Revive glare- and shadow-damaged pages, prove every change, seal the original.` (78)

**Category:** Productivity. **Tags:** Document scanner, PDF & document tools.
**Contains ads:** No. **In-app purchases:** Yes (one-time Pro unlock, US$5.99).

## Full description (4000)

The text Play shows is in `android/fastlane/metadata/android/en-US/` (`title.txt`,
`short_description.txt`, `full_description.txt`, and `changelogs/<versionCode>.txt`), in the layout
`fastlane supply` and Play Console's bulk upload use. Edit it there, then check every claim
against the map below.

## Claim-to-evidence map

| Claim | Where it is proven |
|---|---|
| Faded text comes back; glare halos restored; cores filled and marked | `android/core/.../Engine.kt`; `EngineTest` matches the desktop engine exactly on masks, regions and status (`restore/tests/test_recovery.py` measures the text recovery) |
| Never invents characters | Filled pixels are exactly the mask (`EngineTest`: mask equals desktop mask); findings wording in `Findings.kt` |
| Black areas left alone by default | `RepairConfig.fillShadow = false`; `bars_page` vs `bars_fill_shadow` fixtures |
| Reading order column by column | `ReadingOrder.kt`; `EngineTest` "reads the left column before the right" |
| Argon2id + AES-256-GCM vault | `Vault.kt`; `VaultLedgerTest` (tamper, wrong passphrase, hostile headers) |
| SHA-256 chained log, app checks it | `Ledger.kt`, `EvidenceRepo.verify`; `VaultLedgerTest` (edit, reorder, truncate) |
| Desktop and phone read each other's vaults | `VaultLedgerTest` (phone opens desktop vault/log), `restore/tests/test_android_interop.py` (desktop opens phone vault/log) |
| No internet access | `AndroidManifest.xml` removes network permissions; CI fails if the APK requests them (`.github/workflows/android.yml`) |
| Excluded from backups | `allowBackup=false`, `res/xml/data_extraction_rules.xml` |
| Accessibility checks; no gesture-only comparison or zoom | `SampleFlowTest` runs Google's Accessibility Test Framework on every screen; `ScreensTest`; zoom buttons and slider in `RecoverScreen.kt` |

## Graphics to produce

- Icon 512×512 (from `app/src/main/res/drawable/ic_launcher_foreground.xml` on `#1B2A3A`).
- Feature graphic 1024×500.
- Phone screenshots (at least 2, up to 8): empty state, compare slider on the sample page,
  filled-area overlay with legend, findings, seal dialog, sealed fingerprint, custody log check.
  Capture them from the emulator run with the sample page; do not use competitor imagery.
