# Signing the installers

Unsigned installers work but show warnings (Windows SmartScreen, macOS Gatekeeper) that cost you customers. The `restore-release` workflow signs automatically **when these repository secrets exist**. Add them at: GitHub repo, Settings, Secrets and variables, Actions, New repository secret. Secret values are attached only to the signing steps.

## Windows (Authenticode)
1. Buy a code-signing certificate from a public certificate authority. An **OV** certificate removes the "unknown publisher" name; an **EV** certificate also gives instant SmartScreen reputation (usually a hardware token or cloud HSM, which needs a different signing step than this workflow's `.pfx` file: ask before buying EV).
2. Export the certificate and private key as a `.pfx` file with a strong password.
3. Convert to base64: `base64 -w0 cert.pfx` (Linux) or `certutil -encode cert.pfx cert.b64` (Windows).
4. Add secrets `WIN_CERT_PFX_BASE64` (the base64 text) and `WIN_CERT_PASSWORD`.

## macOS (Developer ID + notarization)
1. Join the Apple Developer Program (about $99/year).
2. In Xcode or the developer portal create a **Developer ID Application** certificate. Export it from Keychain Access as a `.p12` with a password.
3. `base64 -i cert.p12 | pbcopy`.
4. Create an app-specific password at appleid.apple.com.
5. Add secrets: `APPLE_CERT_P12_BASE64`, `APPLE_CERT_PASSWORD`, `APPLE_SIGN_IDENTITY` (for example `Developer ID Application: Your Name (TEAMID)`), `APPLE_ID`, `APPLE_TEAM_ID`, `APPLE_APP_PASSWORD`.

## After adding secrets
Run **Actions, restore-release, Run workflow**. The Windows and macOS jobs will sign; notarization can take several minutes. Check a download on a clean machine: Windows, right-click the `.exe`, Properties, Digital Signatures; macOS, `spctl -a -vv "Arcana Restore.app"` should say "accepted, Notarized Developer ID".

## Status
These signing steps are written but **have never run**: there are no certificates in this repository. Expect to fix small issues the first time (for example the `signtool` path, or hardened-runtime entitlements for the bundled Python). Treat the first signed build as a test.

Keep certificates and passwords out of the repository. Rotate them if they are ever exposed.
