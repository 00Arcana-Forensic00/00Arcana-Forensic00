# Getting Arcalume onto Google Play

Nothing here has been submitted, paid for or published. These are the steps only the account
owner can take, in order.

## 1. Accounts (owner)

1. **Google Play Console developer account** (one-time US$25). Choose *Organization* if Arcana
   Forensics is a registered business: that needs a D-U-N-S number and avoids the personal-account
   rule below. A *Personal* account works too.
2. **Identity and contact verification** in Play Console (legal name, address, phone, email).
3. **Personal accounts created after November 2023:** before production access, the app must run
   a **closed test with at least 12 testers, opted in for 14 continuous days**. Plan for this.
4. **Payments profile** (Play Console > Setup > Payments profile) with bank and tax details, to sell Pro.

## 2. Create the app and the product

1. Create app: name *Arcalume: Document Forensics*, default language English (US), App, Free,
   and accept the declarations.
2. Monetize > Products > In-app products: create **`arcalume_pro`** (this exact id is in
   `Brand.PRO_PRODUCT_ID`), one-time, priced at **US$5.99** (David's decision, 2026-09-30).
3. Monetization setup > Licensing: copy the **base64 RSA public key** into
   `Brand.PLAY_LICENSE_KEY` so purchases are signature-checked on the device.
4. Fill every App content form (privacy policy, ads, app access, content rating, target
   audience, data safety, advertising ID, financial and health features) from
   `PLAY_CONSOLE_ANSWERS.md`, the app access instructions from `scripts/REVIEWER_NOTES.md`, and
   the listing from `../fastlane/metadata/android/en-US/` (claims checked in `LISTING.md`).
5. Upload the eight screenshots and the feature graphic described in
   `scripts/SCREENSHOTS_AND_VIDEO.md`.
6. Declare trader status for the EU (Play Console > Policy > Developer account), with the
   business address and phone you want shown publicly.

## 3. Legal pages

Fill in the placeholders listed in `legal/README.md`, have the drafts reviewed, run
`python3 android/store/build_pages.py`, and merge so `arcana-forensics.com/arcalume/privacy`,
`/terms`, `/refunds`, `/notices` and `/support` are live. Play checks the privacy policy URL.

## 4. Signing

Use **Play App Signing** (Google holds the app signing key). You create an *upload key*:

    keytool -genkeypair -v -keystore arcalume-upload.jks -alias upload -keyalg RSA -keysize 4096 -validity 10000

Keep `arcalume-upload.jks` and its passwords outside the repository (`*.jks` is git-ignored).
To have CI sign release bundles, add the keystore (base64) and passwords as repository secrets;
the release job for that is not written yet, and uploading stays a manual step.

## 5. Build and upload

    cd android && ./gradlew :app:bundlePlayRelease

Upload `app/build/outputs/bundle/playRelease/app-play-release.aab` to an **internal test**
track first, then closed testing (invite testers with `scripts/TESTERS_AND_SUPPORT.md`), then
production. Release notes for each version go in
`../fastlane/metadata/android/en-US/changelogs/<versionCode>.txt`.

## Testing on your own phone before Play

The `beta` build type (`./gradlew :app:assemblePlayBeta`) is the shrunk release build under its
own package id and home-screen name, **Arcalume Beta**, so it installs next to the store version.
`android/tools/beta_smoke.sh` installs it on an emulator, walks through recovery, sealing and the
log check, and saves the store screenshots on the way.

## Decisions only the owner can make

- **180 days free (decided).** Every new install gets Pro free for 180 days, counted on the
  device from first launch (`core/Trial.kt`). It needs no Play free-trial setup, because Play
  trials exist only for subscriptions. Reinstalling or clearing app data restarts the count;
  closing that gap would need an account or server, which conflicts with local-only processing.
- **Organization or personal developer account** (affects the 12-tester rule and the seller name shown).
- **Direct (sideload) build:** whether to also offer the `direct` APK from the website with
  license keys. Keys need `Brand.LICENSE_PUBLIC_KEYS` filled from the same keygen as the desktop app.
  Google Play policy does not allow the Play build to point users to outside payment, so the
  Play build shows no key entry or buy link.
