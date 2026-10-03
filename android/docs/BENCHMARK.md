# Android benchmark: document scanners, cleanup and evidence-capture apps

**Research date:** 2026-09-30
**Product under comparison:** Arcalume (Arcana-Forensics). An Android-first app that captures or imports photos of damaged documents and repairs glare and shadow damage (illumination flattening, contrast recovery around glare halos, and inpainting of clipped glare with a visible mask of every synthesized pixel). It maps multi-column reading order and seals the original and the result in an encrypted vault with a SHA-256 hash-chained custody log. Everything runs on the device, with no account and no telemetry. It will be distributed on Google Play as a free app with a Pro unlock through Play Billing.
**Companion document:** [the desktop benchmark](../../restore/docs/BENCHMARK.md) (same date) covers iOS, desktop and the earlier name scan. Facts from it are reused here and cited to the same URLs.

## Method and limits

- In this research environment the egress proxy blocked direct loads of `play.google.com`, `developers.google.com`, `support.microsoft.com`, `proofmode.org`, `eyewitness.global`, `f-droid.org` and `apt.izzysoft.de`. **Play install bands, ratings and Data safety summaries below are therefore quoted from search-engine extracts of the Play listing URLs**, marked **(extract)**. Ratings and review counts change daily, so re-check every figure in a browser before quoting it publicly. GitHub pages loaded directly.
- **"unverified"** means the only source was an aggregator (AppBrain, APK mirrors, review blogs), or that sources disagreed.
- **"No public statement found"** means a targeted search found nothing. It does not mean the feature or the accessibility is absent.
- Play Data safety is **self-declared by the developer** (https://support.google.com/googleplay/android-developer/answer/10787469). Where a developer's own privacy page contradicts its Data safety label, both are shown.

## Excluded or merged (not counted in the 15)

| App | Why | Source |
|---|---|---|
| Microsoft Lens (Android) | Retired. **The dates conflict with [the desktop benchmark](../../restore/docs/BENCHMARK.md).** 2026 reporting says retirement started 2026-01-09, the app left Google Play on 2026-02-09, and new scans stopped on 2026-03-09. [the desktop benchmark](../../restore/docs/BENCHMARK.md) cited 2025 dates. Treat the 2026 dates as current. | https://www.windowslatest.com/2026/01/10/microsoft-lens-just-retired-on-ios-and-android-stops-working-march-9-as-the-company-wants-to-focus-on-copilot/ ; https://www.bleepingcomputer.com/news/microsoft/microsoft-is-retiring-the-lens-scanner-app-for-ios-android/ ; https://www.ghacks.net/2026/01/13/microsoft-is-ending-support-for-office-lens-on-ios-and-android/ |
| Files by Google scanner | Merged into entry 3 because it uses the same ML Kit / Google Play services scanner as Drive. | https://www.androidpolice.com/google-files-document-scanner-rolling-out-more-widely/ |
| Truepic Vision (`com.truepic.vision`) | Still on Play (v4.1.x in 2026, per aggregators), but it is an enterprise insurance-inspection capture tool with smart-link login. Truepic's C2PA capture is sold mainly as the "Lens" SDK. It is noted here as a reference for C2PA but is not a consumer competitor. | https://apkcombo.com/vision-camera/com.truepic.vision/ (aggregator, unverified) ; https://www.truepic.com/blog/truepics-new-sdk-will-power-trusted-photo-capture-across-the-internet |
| Pixel Camera / Google Photos Content Credentials | This is an OS or OEM feature, not a Play competitor, but it resets expectations (see "Where it cannot honestly claim to"). | https://blog.google/security/pixel-android-trusted-images-c2pa-content-credentials/ |
| Accessibility-first OCR readers (KNFB Reader, Scanthing OCR) | These are text readers rather than document repair tools, and are cited only as TalkBack reference points. | https://chicagolighthouse.org/wp-content/uploads/2019/09/Tools_Android_Accessible_Apps.pdf |

---

## The 15 Android apps

### A. Mainstream scanners

#### 1. Adobe Scan (`com.adobe.scan.android`)
- **Play:** 100M+ installs. Rating about 4.6–4.8 from 2.7M–3.0M reviews; sources disagree by region **(extract)**. https://play.google.com/store/apps/details?id=com.adobe.scan.android&hl=en-GB&gl=GB
- **Price:** Free. Premium costs about US$9.99/month. https://www.techradar.com/pro/software-services/adobe-scan-2025-review
- **Glare/shadow claims:** Adobe says the app will "remove glares and shadows", and its Magic eraser removes "thumbs, shadows, stains and creases". https://acrobat.adobe.com/us/en/acrobat/mobile/scanner-app.html
- **On-device vs cloud, and account:** Scans go to Adobe Document Cloud and sign-in is used. Users report that they cannot stop the upload. https://www.adobe.com/devnet-docs/adobescan/android/en/ ; https://community.adobe.com/t5/adobe-scan/new-adobe-scan-uploads-all-to-cloud/m-p/9531371
- **Data safety (extract):** The label says the app "may share data types with third parties", collects personal info and app activity, encrypts data in transit, and allows deletion requests. https://play.google.com/store/apps/details?id=com.adobe.scan.android&hl=en_US&gl=IR. Common Sense Privacy gives it an overall score of 57%. https://privacy.commonsense.org/evaluation/Adobe-Scan-Mobile-PDF-Scanner
- **Integrity:** No public statement found on hashing, C2PA or a custody log.
- **UI worth copying:** Auto-capture with edge detection, and one-tap Magic eraser.
- **Accessibility:** An Android ACR (VPAT 2.3) exists, dated 2020-04-22. https://www.adobe.com/accessibility/compliance/adobe-scan-android-2020-04-22-acr.html. No specific TalkBack complaints were found.

#### 2. CamScanner (`com.intsig.camscanner`)
- **Play:** 500M+ installs, 4.6 from about 5.05M reviews **(extract)**. https://play.google.com/store/apps/details/CamScanner_App_PDF_Scanner?id=com.intsig.camscanner&hl=en-US
- **Price:** Freemium with a watermark on the free tier. Premium is about US$49.99/year. A competitor's blog also says an account is required for the free tier; treat that as **unverified**. https://essexsoftware.com/scaniva/camscanner-free-vs-paid/
- **Glare/shadow claims:** "No Shadow" and "Omnifix" (formerly Magic Pro), which is said to lift finger shadows and correct low light. https://www.prnewswire.com/news-releases/camscanner-upgrades-magic-pro-filter-to-omnifix-for-one-click-document-perfection-302492113.html
- **On-device vs cloud:** Has cloud sync. Where the filters run is **unverified**.
- **Data safety (extract):** The label says the app "may share device or other IDs with third parties", may collect personal and financial info, encrypts data in transit, and allows deletion requests. https://play.google.com/store/apps/details/CamScanner_App_PDF_Scanner?id=com.intsig.camscanner&hl=en-US
- **History:** In 2019 a Trojan dropper was found in its ad SDK and the app was temporarily removed from Play. https://www.xda-developers.com/camscanner-app-injecting-malware/ ; https://en.wikipedia.org/wiki/CamScanner
- **Integrity:** No public statement found.
- **UI worth copying:** A single one-tap "fix everything" filter, alongside named manual modes.
- **Accessibility:** No public statement found.

#### 3. Google Drive scanner + Files by Google scanner (ML Kit Document Scanner)
- **Play (Drive, `com.google.android.apps.docs`):** 10B+ installs, 4.3 from about 10.8M reviews **(extract)**. https://play.google.com/store/apps/details?id=com.google.android.apps.docs&hl=en_US
- **Price:** Free. Saving to Drive needs a Google account. Files by Google saves scans locally in a "Scanned" tab. https://www.androidcentral.com/apps-software/files-by-google-document-scanner-rolls-out
- **Glare/shadow claims:** "Enhance" performs "white balance correction, shadow removal, contrast enrichment, auto sharpening, light improvement". In 2026 the enhance button moved to its own pill in the toolbar. https://www.androidauthority.com/google-drive-improved-scanner-mobile-3509225/ ; https://www.androidpolice.com/google-drive-mobile-better-scans-auto-enhancements/. **No explicit glare claim found.**
- **On-device:** Google says "the entire document scanner flow operates on-device", with models delivered through Google Play services. Features include removing fingers, stains and shadows. https://android-developers.googleblog.com/2024/02/ml-kit-document-scanner-api.html ; https://developers.google.com/ml-kit/vision/doc-scanner
- **Data safety:** For the scanner specifically, no public statement found. Drive's label was not retrieved.
- **Integrity:** No public statement found.
- **UI worth copying:** Manual and Auto Capture toggles, one-tap enhance, and a single consistent scanner shared across Google apps. **This is the baseline Android users already know.**
- **Accessibility:** Google publishes a Drive **web** ACR (2025-07-22), but no Drive Android ACR was found. Google's Android ACRs for other apps (for example Messages) test with TalkBack, Switch Access, keyboard, magnification and contrast on Pixel devices. https://accessibility.google/accessibility-conformance-reports/ ; https://services.google.com/fh/files/misc/android-messages-vpat.pdf

#### 4. Microsoft OneDrive scan (`com.microsoft.skydrive`), the successor to Lens
- **Play:** 5B+ installs, 4.6 from about 7.34M reviews **(extract)**. https://play.google.com/store/apps/details?id=com.microsoft.skydrive&hl=en_US
- **Price:** Free, and a Microsoft account is required.
- **Claims:** Scans documents, whiteboards, business cards and photos to PDF from the "+" button. Reporting says OneDrive **cannot save scans locally**, only to the cloud. https://www.windowscentral.com/software-apps/microsoft-lens-is-dead-microsoft-wants-you-on-onedrive-but-it-doesnt-let-you-save-scans-locally. The Microsoft 365 Copilot app also scans (Create > Scan); users were still asking where the scanner had gone in August 2026. https://learn.microsoft.com/en-us/answers/questions/5980537/where-has-the-m365-scanner-gone-again-august-2026
- **Glare/shadow claims:** Specific to OneDrive: no public statement found.
- **Integrity:** No public statement found.
- **Accessibility:** Microsoft publishes ACRs for OneDrive (index: https://acrindex.com/microsoft/). A university-hosted OneDrive Android accessibility statement (2021-08-06) says the app partially supports WCAG 2.1 AA. https://students.hud.ac.uk/media/universityofhuddersfield/studentsx27website/hudstudy/MicrosoftOneDrive-AccessibilityStatementAndroidApp.pdf
- **Opportunity:** Lens users who were displaced lost local-only saving. That is a real audience for an offline app.

#### 5. Genius Scan (`com.thegrizzlylabs.geniusscan.free`)
- **Play:** 10M+ installs, about 4.9 from about 614K reviews **(extract)**. https://play.google.com/store/apps/details?id=com.thegrizzlylabs.geniusscan.free&hl=en_US
- **Price:** The free tier is described as fully functional. Ultra is about US$39.99/year. https://thegrizzlylabs.com/genius-scan/pricing/
- **Glare/shadow claims:** Shadow removal and defect cleanup. No glare claim found.
- **On-device:** The developer says "processed exclusively on your device" and "works 100% offline". https://help.geniusscan.com/security-and-privacy/privacy-and-security-overview ; https://android.help.thegrizzlylabs.com/article/172-scan-document-gdpr-compliance
- **Data safety (extract), which conflicts with the above:** For the consumer and Enterprise listings, the label "may share App info and performance, Device or other IDs" and "may collect Personal info, Photos and videos and 3 others". This probably reflects crash reporting and the optional cloud, but that is **unverified**. The SDK demo app declares "No data collected". https://play.google.com/store/apps/details?id=com.geniusscansdk.simpledemo
- **Integrity:** PDF encryption and app lock. No hashing.
- **Accessibility:** No public statement found.

#### 6. vFlat Scan (`com.voyagerx.scanner`)
- **Play:** 10M+ installs, 4.6 from about 177K reviews **(extract)**. Last updated 2026-09-04 (aggregator). https://play.google.com/store/apps/details?id=com.voyagerx.scanner&hl=en ; https://sourceforge.net/software/product/vFlat-Scan/
- **Price:** Free, with an OCR cap and a subscription (prices **unverified**).
- **Glare/shadow claims:** Shadow removal, perspective and curve correction, and contrast and saturation boost. **No glare-removal claim**, and a user review complains that glare causes missing text. https://justuseapp.com/en/app/1540238220/vflat-scan-pdf-scanner/reviews
- **Data safety (extract):** The label "may share personal info and photos/videos" and collects personal and financial info, while the developer says it does not collect scans without consent. https://play.google.com/store/apps/details?id=com.voyagerx.scanner&hl=en
- **UI worth copying:** Book-spread splitting and automatic finger removal.
- **Accessibility:** No public statement found.

#### 7. Clear Scan (`com.indymobileapp.document.scanner`)
- **Play:** 10M+ installs, about 4.7–4.8 from about 434K–477K reviews **(extract / AppBrain)**. https://play.google.com/store/apps/details?id=com.indymobileapp.document.scanner&hl=en ; https://www.appbrain.com/app/clear-scan-pdf-scanner-app/com.indymobileapp.document.scanner
- **Price:** Free with ads and in-app purchases (details **unverified**).
- **Claims:** "Removing shadows", edge detection, perspective correction, and filters (photo, document, clear, colour, B&W). Same Play URL.
- **Data safety (extract):** "No data shared with third parties", encrypted in transit, and **data can't be deleted**. Same Play URL.
- **Integrity:** No public statement found.
- **Accessibility:** No public statement found.

#### 8. Tiny Scanner (`com.appxy.tinyscanner`)
- **Play:** 10M+ installs, 4.6 from about 490K reviews **(extract)**. https://play.google.com/store/apps/details?id=com.appxy.tinyscanner&hl=en_US
- **Price:** Free with a subscription (prices **unverified**).
- **Claims:** Auto edge detection, PDF editing and signing. A shadow-removal claim is documented for iOS ([the desktop benchmark](../../restore/docs/BENCHMARK.md)); for Android it is **unverified**.
- **Data safety:** Not retrieved (**unverified**).
- **Accessibility:** No public statement found.

#### 9. TurboScan (`com.piksoft.turboscan.free` / Pro `com.piksoft.turboscan`)
- **Play:** The free app has 1M+ installs, rated about 4.8 from about 28.7K reviews. Pro has 100K+ installs, about 4.8 from about 20K reviews, at US$5.99 as a paid app **(extract / AppBrain)**. https://play.google.com/store/apps/details?id=com.piksoft.turboscan.free&hl=en_US ; https://play.google.com/store/apps/details?id=com.piksoft.turboscan&hl=en
- **Claims:** SureScan takes three shots and fuses them, for low light.
- **Data safety:** Not retrieved (**unverified**).
- **UI worth copying:** Multi-shot fusion. For glare this is a strong idea: several exposures or angles reduce specular clipping without synthesis.
- **Accessibility:** No public statement found.

#### 10. SwiftScan (`net.doo.snap`; formerly Scanbot, now Maple Media)
- **Play:** 5M+ installs, **3.8** from about 63.6K reviews **(extract)**. https://play.google.com/store/apps/details?id=net.doo.snap&hl=en
- **Price:** Several subscription tiers (**unverified**).
- **Claims:** Edge detection and filters. No shadow or glare claim found.
- **Integrity:** PDF password and biometric lock (iOS source in [the desktop benchmark](../../restore/docs/BENCHMARK.md); **unverified** on Android).
- **Accessibility:** No public statement found.

### B. Open-source and offline scanners

#### 11. OSS Document Scanner (`com.akylas.documentscanner`)
- **Play:** 50K+ installs **(extract)**. Also on IzzyOnDroid and GitHub. https://play.google.com/store/apps/details?id=com.akylas.documentscanner&hl=en ; https://github.com/Akylas/OSS-DocumentScanner
- **Price:** Free (MIT licence) and funded by donations.
- **Claims:** Automatic edge detection, auto-scan, filters, and **shadow/glare correction** (per the README summary; the specific algorithm is **unverified**). Offline Tesseract OCR in the open-source builds. https://firethering.com/oss-document-scanner-open-source-document-scanning-app-for-android-ios/
- **Integrity:** None found.
- **Accessibility:** No public statement found.

#### 12. MakeACopy (`de.schliweb.makeacopy`)
- **Distribution:** F-Droid and Google Play (the Play build uses PaddleOCR). Install band **unverified**. https://f-droid.org/en/packages/de.schliweb.makeacopy/ ; https://github.com/egdels/makeacopy
- **Price:** Free (Apache-2.0).
- **Claims:** "100% offline". OpenCV edge detection plus a custom ML model. Grayscale, contrast and sharpen filters. **No shadow or glare claim.** Only camera and storage permissions. https://github.com/egdels/makeacopy
- **Integrity:** None found.
- **Accessibility:** **This is the only scanner found with a dedicated Accessibility Mode**, providing "spoken and haptic feedback" and a hardware volume-key shutter, with guides in English, German and French. https://github.com/egdels/makeacopy. **Pattern to copy.**

### C. Evidence, forensic and tamper-evident capture (Android)

#### 13. ProofMode / "Proofmode Capture" (`org.witness.proofmode`; Guardian Project with WITNESS)
- **Play:** 10K+ installs, about 3.8 from about 79 reviews **(extract)**. Updated 2026-09-13, with a rebuilt viewfinder, Auto Sync to IPFS via Filebase, and beta CAWG identity assertions. https://play.google.com/store/apps/details?id=org.witness.proofmode ; https://proofmode.org/install.html
- **Price:** Free (GPL-3.0). Also on F-Droid and GitHub.
- **Integrity:** SHA-256 hashes plus OpenPGP signatures, OpenTimestamps, and Play Integrity / SafetyNet attestation. "ProofMode 3.x is now fully C2PA conformant, supporting the 2.3 specification." Proof is stored as CSV and signature files alongside the media. https://github.com/guardianproject/proofmode-android (mirror of https://gitlab.com/guardianproject/proofmode/proofmode-android). One source reports C2PA conformance as of 2026-05-08: https://proofmode.org/project/proofmode-android (extract).
- **Data safety (extract):** "No data shared with third parties", encrypted in transit, and collects Location, Photos and videos and 3 other types. https://play.google.com/store/apps/details?id=org.witness.proofmode
- **Scope:** Capture provenance for photos and video. **No document repair, no scanning pipeline and no vault.**
- **Accessibility:** No public statement found.

#### 14. eyeWitness to Atrocities (`com.camera.easy`; IBA with LexisNexis)
- **Play:** 10K+ installs, 4.6 from about 231 reviews **(extract)**. Android only. https://play.google.com/store/apps/details?id=com.camera.easy&hl=en
- **Price:** Free.
- **Integrity:** The app computes a hash "as soon as you take footage" and embeds GPS, time and device metadata. It stores media encrypted in the app and uploads to an encrypted server hosted by LexisNexis, where the upload "cannot be altered". It **refuses footage from other camera apps** because it cannot prove prior integrity. The hash algorithm is not stated in the extracts (**unverified**). https://www.eyewitness.global/Using-metadata ; https://www.eyewitness.global/documents/What-happens-when-you-upload-footage.pdf ; https://www.ibanet.org/Technology-meets-justice-marking-ten-years-of-eyewitness
- **Privacy:** Anonymity is optional. The privacy policy says the app uses no cookies, analytics tools or device identifiers. https://www.eyewitness.global/privacy-policy (extract)
- **Data safety (extract):** "No data shared with third parties", encrypted in transit. https://play.google.com/store/apps/details?id=com.camera.easy&hl=en
- **Scope:** Capture-to-custodian workflow. No document enhancement. **Refusing imports is a deliberate forensic stance, and Arcalume's import feature must answer it** (see below).
- **Accessibility:** No public statement found.

#### 15. Tella (`org.hzontal.tella`; Horizontal)
- **Play:** 100K+ installs, 4.6 from about 276 reviews **(extract)**. https://play.google.com/store/apps/details?id=org.hzontal.tella&hl=en_US
- **Price:** Free (MIT).
- **Integrity:** SQLCipher-encrypted database with passphrase management through CacheWord, and an encrypted gallery hidden from the system gallery. Captures metadata "to verify the origin of the files", and uploads to the organisation's own server. The README names no hashing algorithm. https://github.com/Horizontal-org/Tella-Android
- **UI worth copying:** An icon and name camouflage option (calculator or camera) for users at risk. https://tella-app.org/faq/
- **Accessibility:** No public statement found. The README aims for "minimal or no training".

---

## Summary matrix

Key: Y = claimed, N = not claimed or not found, ? = unverified or conflicting, (x) = extract of the Play listing.

| # | App | Installs (x) | Rating (x) | Glare | Shadow | On-device | No account | Play "no data shared" | Hash / C2PA / custody | Encrypted store | Public a11y doc |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Adobe Scan | 100M+ | 4.6–4.8 | Y | Y | N | N | N | N | ? | ACR 2020 |
| 2 | CamScanner | 500M+ | 4.6 | N | Y | ? | ? | N | N | ? | N |
| 3 | Drive / Files (ML Kit) | 10B+ (Drive) | 4.3 | N | Y | Y (scan) | Files: Y / Drive: N | ? | N | N | web ACR only |
| 4 | OneDrive scan | 5B+ | 4.6 | ? | ? | N (cloud only) | N | ? | N | N | ACR (partial WCAG 2.1) |
| 5 | Genius Scan | 10M+ | 4.9 | N | Y | Y | Y | N (label) | N | Y (PDF) | N |
| 6 | vFlat | 10M+ | 4.6 | N | Y | ? | ? | N | N | ? | N |
| 7 | Clear Scan | 10M+ | 4.7–4.8 | N | Y | ? | ? | Y | N | ? | N |
| 8 | Tiny Scanner | 10M+ | 4.6 | N | ? | ? | ? | ? | N | ? | N |
| 9 | TurboScan | 1M+ / 100K+ | 4.8 | N (multi-shot) | N | ? | ? | ? | N | ? | N |
| 10 | SwiftScan | 5M+ | 3.8 | N | N | ? | ? | ? | N | ? | N |
| 11 | OSS Doc Scanner | 50K+ | ? | ? | Y | Y | Y | ? | N | N | N |
| 12 | MakeACopy | ? | ? | N | N | Y | Y | ? | N | N | **Accessibility Mode** |
| 13 | ProofMode | 10K+ | 3.8 | N | N | Y | Y | Y | **SHA-256 + PGP + C2PA** | N | N |
| 14 | eyeWitness | 10K+ | 4.6 | N | N | capture Y; storage server | Y (anon optional) | Y | **hash + server custody** | Y | N |
| 15 | Tella | 100K+ | 4.6 | N | N | Y | Y | ? | metadata only | **Y (SQLCipher)** | N |

**Key gap:** no app on this list both **repairs** document images and **proves** what it changed. The scanners (1–12) repair without provenance. The evidence apps (13–15) prove provenance but refuse to repair or never do.

---

## Where an Android forensic recovery app can credibly beat them

1. **Repair plus provenance in one chain.** ProofMode hashes and signs captures, and eyeWitness locks them on a server, but neither edits. The scanners edit, but none records what changed. A custody log that records the SHA-256 of the original, the parameters of every operation, the mask of synthesized pixels and the SHA-256 of the result, with a verifier the user can export, fills a gap no one on this list occupies. Claim only what the verifier proves.
2. **Honesty about synthesized pixels.** Adobe's Magic eraser and ML Kit's stain and finger removal synthesize content without disclosing it. A per-pixel "inpainted" mask that is on by default in exports, and a rule that masked regions are never presented as recovered text, is defensible and distinctive.
3. **Glare as a named capability.** On Android only Adobe claims glare removal. Drive, Genius, vFlat, Clear Scan and OSS Scanner claim shadows. Glare-halo contrast recovery (which restores real, un-clipped signal) is not the same as inpainting (which synthesizes). Keeping them as separate, labelled steps is both honest and a feature. **Consider copying TurboScan's multi-shot idea:** fusing 2–3 exposures or angles recovers genuinely clipped regions without synthesis, which is better forensic practice than inpainting.
4. **A Play Data safety label that says "No data collected" and "No data shared", backed by a manifest with no `INTERNET` permission.** Among the mainstream scanners, Adobe, CamScanner, vFlat and even Genius Scan declare collection or sharing on their Play labels. Clear Scan declares no sharing but "data can't be deleted". A verifiable no-network build is rare in the top tier. Only MakeACopy and OSS Scanner, both small, come close.
5. **Local-only saving for Lens refugees.** OneDrive, Lens's official successor, cannot save scans locally.
6. **An encrypted vault without an organisation server.** Tella and eyeWitness encrypt, but both are built to upload to a custodian. Arcalume can offer the same encryption at rest for individual users (lawyers, adjusters, genealogists, investigators) with export-on-demand.
7. **Reading-order mapping for multi-column pages.** No scanner in this list claims column or reading-order detection. Keep it as an assisted, correctable feature, and expose it to TalkBack (see the checklist).
8. **Accessibility as a first-class feature.** Only MakeACopy ships a dedicated accessibility mode. Only Adobe (2020) and Microsoft (OneDrive, partial) publish Android ACRs. Shipping a spoken capture guide and publishing an Android ACR at launch would lead this tier.
9. **One-time Pro unlock.** Adobe, CamScanner, Genius, vFlat and SwiftScan all sell subscriptions. TurboScan Pro (US$5.99 paid app) shows that one-time pricing works on Play, so this is a contrast with most competitors, not a unique claim.

## Where it cannot honestly claim to

1. **"Tamper-proof", "court-admissible" or "certified".** A hash chain shows that records were not changed after they were sealed. It does not prove the photo was authentic before capture, and admissibility is decided by courts. eyeWitness relies on a third-party custodian server and refuses imported files for exactly this reason.
2. **Capture-time authenticity for imported photos.** An imported image's history before import is unknown. The custody log should state "imported; provenance before import unknown", and should never imply otherwise.
3. **C2PA or hardware attestation parity, unless it is built.** ProofMode is C2PA-conformant (spec 2.3). Pixel 10's camera signs every JPEG at C2PA Assurance Level 2 with keys held in StrongBox/Titan M2, and Google Photos adds Content Credentials to edits. https://blog.google/security/pixel-android-trusted-images-c2pa-content-credentials/ ; https://c2pa.ai/news/pixel-10. Arcalume should at minimum **preserve and verify incoming C2PA manifests** and add its edits as a C2PA ingredient/action manifest. It must not claim hardware-backed capture signing unless it uses Android Keystore/StrongBox attestation and passes conformance.
4. **Scanner-grade capture UX on day one.** The ML Kit scanner (Drive/Files) gives every Android user free, on-device auto-capture, edge detection and cleanup. Matching its polish is a large effort. Using ML Kit for capture is an option, but whether it can return the **unprocessed** frame needed for a forensic original is **unverified**. Test this before relying on it, or capture with CameraX and keep the raw frame.
5. **Shadow-removal quality superiority.** Google Enhance, CamScanner Omnifix and Adobe all ship ML models. Claim better results only with a public side-by-side benchmark.
6. **OCR breadth, book dewarping, finger removal and cloud sync.** These are competitors' strengths. Do not claim them unless they are built.
7. **Scale and trust signals.** Competitors have 10M–10B installs and hundreds of thousands of reviews. A new app should lead with verifiable properties (open verifier, no-network manifest, published ACR), not with rankings.
8. **Protection for at-risk users.** Tella's camouflage and eyeWitness's anonymous custodian model target activists under threat. Unless Arcalume adds duress features, it should not market itself to that group.

---

## Android accessibility checklist

Targets: WCAG 2.2 AA mapped to Android (EN 301 549 clause 11), then publish an ACR. References: https://developer.android.com/guide/topics/ui/accessibility/apps ; https://support.google.com/accessibility/android/answer/7101858 ; https://developer.android.com/develop/ui/compose/accessibility/testing

**TalkBack**
- [ ] Every actionable element has a label (`contentDescription` or Compose `semantics { contentDescription }`), with no "unlabeled button". Decorative images use `null` or `invisibleToUser()`.
- [ ] Capture screen: spoken edge guidance ("Page detected, 3 corners visible, move left"), auto-capture announced, and a volume-key shutter as an option (MakeACopy pattern).
- [ ] Before/after comparison: a slider with `stateDescription` ("40% original") and custom accessibility actions ("Show original", "Show recovered", "Show mask"). Adjustable by TalkBack swipe up/down, never drag-only.
- [ ] Masks and damage maps have a text summary ("Glare: 3 regions, 12% of page. 4% inpainted, not original text").
- [ ] Reading order: the reconstructed columns are exposed as a traversable list or headings (`traversalIndex`, `isTraversalGroup`, `heading()`), and a "Read recovered text" action follows the mapped order.
- [ ] The custody log appears as a list of records, each read as one unit ("Step 4, inpaint, 14:02, hash ends 9F3A, verified") using `mergeDescendants`.
- [ ] Custom actions replace hidden long-press or swipe-only gestures.

**Live regions and status**
- [ ] Batch progress, "Sealed", "Chain verified" and "Chain broken at step N" are announced through `liveRegion = Polite` (Assertive for failures) without moving focus. Progress is also shown as text, not only as an animation.
- [ ] Long jobs have no timeout, and can be cancelled or resumed.

**Switch Access and keyboard**
- [ ] Every function is reachable by Switch Access and by a hardware keyboard (Tab, arrows, Enter). The focus order is logical, there are no focus traps, and focus is visible.
- [ ] Crop handles, the mask brush and the slider have non-drag alternatives (nudge buttons, numeric entry, "auto-fit").

**Text and layout**
- [ ] Font scale 200% (Android 14+ non-linear scaling) causes no clipping or overlap. Use `sp` for text, avoid fixed heights, and test in landscape and split-screen.
- [ ] Display size set to largest, plus magnification, shows no lost controls.

**Targets and contrast**
- [ ] Touch targets are at least **48×48dp**, using padding where icons are 24dp.
- [ ] Text contrast is at least 4.5:1 (3:1 for large text), and icons, control borders and mask outlines at least 3:1, in light, dark and high-contrast-text modes.
- [ ] **No information carried by colour alone.** Mask overlays use hatch or outline patterns plus a legend, and verification states use an icon and a word, not just green or red.

**Motion, haptics and sound**
- [ ] Respect "Remove animations". No wipe animations when that setting is on.
- [ ] Haptics supplement cues but never replace them.

**Authentication**
- [ ] Vault unlock supports biometric, device credential and a passphrase that allows pasting and password managers (`autofillHints`). No cognitive puzzles.

**Testing**
- [ ] Automated: Compose `enableAccessibilityChecks()` (Compose 1.8+, ATF-based) on `AndroidComposeTestRule`, or Espresso `AccessibilityChecks.enable().setRunChecksFromRootView(true)` for Views. Fail CI on errors. https://android-developers.googleblog.com/2025/04/whats-new-in-jetpack-compose-april-25.html ; https://developer.android.com/guide/topics/ui/accessibility/views/testing-views
- [ ] Accessibility Scanner app pass on every screen, including capture, compare, vault, log and paywall. https://support.google.com/accessibility/android/faq/6376582
- [ ] Manual passes: TalkBack (latest), Switch Access, Voice Access, 200% font, dark mode, high-contrast text, and a Samsung One UI device as well as a Pixel.
- [ ] The Play Billing paywall is part of the test scope. Paywalls are a common accessibility dead end.
- [ ] Publish an Android ACR (VPAT 2.5 INT) at launch and state its date.

---

## Name conflict scan (one web search each; not legal clearance)

| Candidate | Rationale | Findings | Risk (informal) |
|---|---|---|---|
| **Arcalume** | arcana + lume (light), for illumination recovery | No exact app or software match. Near-misses are **Arclume**, an open-source desktop launcher on GitHub, and several "Arcal" apps (ARCAL ERP2 on Play, the Arcal English app), plus an "Arcanum" group-coordination app on Play. https://github.com/inaciorafael/arclume ; https://play.google.com/store/apps/details?id=erp2.biz.arcal&hl=en_US ; https://play.google.com/store/apps/details?id=at.cluefactory.arcanum&hl=en_US. The earlier scan ([the desktop benchmark](../../restore/docs/BENCHMARK.md)) also found no trademark hits. | **Low.** The one-letter gap to "Arclume" is in a different category (a desktop launcher). |
| **Arcana Revive** | Says "revival" directly | No exact match. But **"Arcana Recovery"** (a sobriety tracker) is on Play, and the "Arcana" namespace is crowded with tarot, astrology, comics and fitness apps. https://play.google.com/store/apps/details?id=com.lauSha.meh&hl=en_US&gl=US ; https://play.google.com/store/apps/details?id=net.arcanalibrary.android ; https://play.google.com/store/apps/details?id=org.arcana.mobile&hl=en_US | **Medium.** It would be hard to find in store search and easy to confuse with the recovery or esoteric genres. |
| **Arcavita** | arca (chest or vault) + vita (life): a vault that brings pages back to life | No exact match. The closest is **Arcavista Corporation**, which holds US software trademarks ("ARCAVISTA COMMUNICATOR"). https://trademark.justia.com/owners/arcavista-corporation-1829177 | **Low–Medium.** Check for similarity to "Arcavista" in class 9. |
| **Arcanima** | arcana + anima (breath or soul): reanimating a document | No app, software or trademark hit in one search. The name is generic-sounding and may collide with games or art handles that search did not surface (**unverified**). | **Low** (from this search). |

**Recommendation:** Keep **Arcalume** as the product name. It is the cleanest of the four and ties to the illumination-recovery core. Use a descriptive Play subtitle for the revival idea, for example "Arcalume: Document Revival & Proof". Note that Google Play limits app titles to 30 characters (**unverified in this session**; confirm in Play Console). Before committing, run USPTO (classes 9 and 42), EUIPO and Play Console searches. None of this is legal advice.

---

## Sources not directly loaded (re-verify in a browser)

All `play.google.com` figures, all Data safety summaries, `proofmode.org`, `eyewitness.global`, `f-droid.org`, `developers.google.com` and `support.microsoft.com` statements above come from search-result extracts, because the research proxy blocked direct loads.
