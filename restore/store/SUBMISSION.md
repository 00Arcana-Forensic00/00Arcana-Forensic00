# Getting Arcalume into stores

Status as of this branch: the app, installers, store packages and license flow are built
and tested in code. Nothing has been submitted, published or paid for.

## What is ready
| Piece | State |
|---|---|
| App (recovery engine, UI, licensing, vaults) | Built; 70+ automated tests incl. accessibility |
| Direct download installers (Windows .exe, macOS .dmg, Linux .tar.gz) | `restore-release` workflow; Linux built and CLI smoke-tested here; Windows/macOS written, run the workflow once |
| Microsoft Store `.msix` | Manifest and packer written (`packaging/windows/msix/`); runs in the workflow once the MSIX_* variables exist |
| Mac App Store `.pkg` | Sandbox entitlements and `packaging/macos/build_mas.sh` written; not run (needs Apple certificates) |
| License keys | Ed25519, verified offline; `packaging/license_tool.py` makes keys; worker source in `license-worker/` |
| Store listing, privacy policy, screenshots | `store/` drafts |

## What only David can do
1. **Accounts.** Microsoft Partner Center developer account (one-time fee for individuals,
   none for companies at the time of writing) and Apple Developer Program (yearly fee).
2. **Reserve the name "Arcalume"** in both stores, then copy the Partner Center identity
   into repository variables `MSIX_IDENTITY_NAME`, `MSIX_PUBLISHER`, `MSIX_PUBLISHER_DISPLAY_NAME`.
3. **Signing.** Apple: Developer ID (direct .dmg) plus Mac App Distribution and Installer
   certificates and a provisioning profile for `com.arcanaforensics.arcalume`. Windows
   direct download: a code-signing certificate (the Store signs its own package).
   The existing secrets names are in `restore/README.md`.
4. **License signing key.** Run `python restore/packaging/license_tool.py keygen --out <outside the repo>`,
   paste the printed public key into `licensing.PUBLIC_KEYS`, and store the private key as the
   worker secret. Until then no key can unlock Pro in the direct edition (store editions are unaffected).
5. **Stripe.** Create Arcalume Payment Links (current links in `site/stripe.config.js` are for
   the forensics suite), set their success URL to
   `https://arcana-forensics.com/arcalume/thanks?session_id={CHECKOUT_SESSION_ID}`, add a webhook
   to `https://<worker>/stripe/webhook` for `checkout.session.completed`, and map each link in
   `PAYMENT_LINK_PLANS`. Then deploy `license-worker/` (it replaces the current stub worker).
6. **Pricing and tiers** (see decision below).
7. **Export compliance.** The app uses encryption (AES-256-GCM) for data protection. Apple asks
   this at upload (`ITSAppUsesNonExemptEncryption` is set to true); US mass-market encryption
   usually needs an annual self-classification report to BIS. Check with counsel.
8. **Trademark.** A web search found no conflict for "Arcalume" (docs/BENCHMARK.md); that is
   not legal clearance. A USPTO/EUIPO search in classes 9 and 42 is recommended before paying
   for anything with the name on it.

## Decisions
- **Price model.** Proposed default: free download, Pro as a one-time unlock (lifetime key on
  the website, non-consumable in-app purchase in stores). Subscriptions work for website keys
  (keys expire after the period plus 14 days) but renewal keys are not automated yet.
- **Store purchase model.** The store editions currently unlock Pro for everyone (paid-upfront
  app). A free-with-in-app-purchase store listing needs StoreKit / Windows.Services.Store
  integration, which is not built.
- **Mobile.** Not in this version. The recovery engine is Python + OpenCV; a phone app would
  need either a native port of the engine or a different app shell. Worth deciding before
  promising it in any listing.

## Known gaps
- Screen-reader passes with NVDA, JAWS, Narrator, VoiceOver and Orca are still manual to-dos.
- The Linux app window (WebKitGTK) bundle is built in CI but its window smoke test is allowed to fail until proven.
- Client-side licensing can be bypassed by someone who modifies the app; it is not DRM.
