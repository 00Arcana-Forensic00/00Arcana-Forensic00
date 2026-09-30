# Google Play listing: Arcalume

Every claim below maps to code and a test. Nothing is claimed that the app does not do.
Character limits are Play Console's.

**App name (30):** `Arcalume: Document Forensics` (28)

**Short description (80):**
`Revive glare- and shadow-damaged pages, prove every change, seal the original.` (78)

**Category:** Productivity. **Tags:** Document scanner, PDF & document tools.
**Contains ads:** No. **In-app purchases:** Yes (one-time Pro unlock).

## Full description (4000)

Arcalume is a forensic document recovery app. Photograph or import a page that glare,
shadow or bad light has ruined, and Arcalume parses the damage, repairs what the photo still
holds, and tells you plainly what it could not bring back.

RECOVER, THEN PROVE IT
• Evens out shadows and uneven light, so faded text that is still in the photo comes back.
• Restores the ink around glare spots, where text is washed out but not gone.
• Fills blown-out glare cores smoothly, and marks every filled pixel with a hatched overlay.
  Those pixels held no data. Arcalume never invents characters and never calls them recovered.
• Leaves solid black areas alone by default, because they are often redactions.
• Maps the reading order of multi-column pages, column by column.

EVIDENCE YOU CAN CHECK (PRO)
• Seals the untouched original, the recovered copy, the filled-pixel map and a full report
  into one encrypted vault file (Argon2id and AES-256-GCM).
• Records every sealing in a custody log where each entry is chained to the one before it with
  SHA-256. Editing, reordering or removing entries breaks the chain, and the app checks it for you.
• Vaults open in the Arcalume desktop app too, and the desktop reads what the phone writes.

PRIVATE BY DESIGN
• Arcalume does not request internet access. No account, no ads, no tracking, no cloud.
• Evidence is excluded from cloud backups. Nothing leaves the phone unless you export it.

BUILT FOR EVERYONE
• Designed for TalkBack, Switch Access and keyboards, and checked with Google's
  Accessibility Test Framework. Comparing and zooming work without gestures.
• Findings are written in plain language and marked with a word and an icon, not colour alone.
• Text follows your system font size, in light and dark themes.

FREE AND PRO
Free: recovery, comparison, the filled-pixel map, and opening and checking any vault.
Pro, one payment: clean saved copies, sealing into vaults with a custody log, and sealing a
whole session at once. No subscription.

WHAT IT CAN'T DO
Text inside a blown-out glare spot is gone from that photo; retake it at an angle. The custody
log proves records were not changed after sealing. It cannot prove what happened to a photo
before it reached the app, and it is not a certification that evidence is admissible.

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
