# Arcalume for Android

Forensic document recovery on the phone: take or import a photo of a page damaged by glare,
shadow or poor light, recover what the photo still holds, see exactly which pixels had to be
filled, and seal the untouched original with the result into an encrypted vault with a
hash-chained custody log. No network access, no account, no tracking.

This is the primary edition. The desktop app in `../restore` shares the same engine, vault
format, custody log and license keys, and each app opens what the other seals.

## Layout

| Path | What it is |
|---|---|
| `core/` | Plain Kotlin/JVM library, testable without the Android SDK: the recovery engine (OpenCV Java API), ARCR vault (Argon2id + AES-256-GCM via Bouncy Castle), custody ledger, canonical JSON, license keys, findings |
| `core/src/test/resources/fixtures/` | Outputs of the desktop engine and tools, made by `tools/make_fixtures.py` |
| `app/` | The Compose app: camera (CameraX), Photo Picker and file import, compare viewer, findings, sealing, vault and custody log, plan |
| `app/src/play`, `app/src/direct` | Pro through Google Play Billing, or through offline license keys |
| `store/` | Play listing, Data safety answers, submission steps |
| `docs/BENCHMARK.md` | The 15 Android apps Arcalume was measured against, with sources |

## Build and test

    cd android
    ./gradlew -p core test                 # engine, vault, ledger, licensing vs the desktop (no SDK needed)
    ./gradlew :app:testPlayDebugUnitTest    # screens on Robolectric
    ./gradlew :app:assemblePlayDebug        # needs the Android SDK (compileSdk 36)
    ./gradlew :app:connectedPlayDebugAndroidTest   # on a device: real engine + accessibility checks

After changing the desktop engine, regenerate the fixtures and re-run the core tests:

    python tools/make_fixtures.py && ./gradlew -p core test

CI (`.github/workflows/android.yml`) runs all of it, checks that the desktop opens what the
Android core sealed, and fails if the packaged app asks for network access.

## Recovery on a phone

Photos are recovered at up to 3200 pixels on the long side (`Brand.WORK_MAX_SIDE`); the
original is kept byte-for-byte and the manifest records the scale. Camera photos keep their
EXIF data in the sealed original, and the recovery honours the EXIF rotation. HEIC and other
formats OpenCV cannot read are decoded by Android, and the original file is still sealed as-is.
