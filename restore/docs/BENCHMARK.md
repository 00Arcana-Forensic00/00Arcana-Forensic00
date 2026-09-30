# Competitive benchmark: document scanning and page-cleanup apps

**Research date:** 2026-09-30
**Scope:** 15 apps currently on sale or in active distribution (mobile scanners plus desktop cleanup and OCR tools), benchmarked against a planned offline desktop app that recovers pages damaged by glare and shadow, seals the originals and results in an encrypted vault, and records custody in a hash-chained ledger.

## How this was researched, and its limits

- Each claim below has a URL. Most facts come from web-search extracts of the cited pages. In this research environment the network proxy blocked direct page loads of `apps.apple.com`, `adobe.com`, `readdle.com`, `thegrizzlylabs.com` and `help.geniusscan.com`. The App Store privacy-label contents are therefore quoted from search extracts of the listing pages and are marked **(extract; not loaded directly)**. Before publishing any comparison, re-check them in a browser.
- **"unverified"** means the only source found was a third-party aggregator, a mod/APK site or an unclear listing, or that sources disagreed.
- **"No public statement found"** means a targeted search turned up no accessibility statement, VPAT/ACR or similar document. It does not mean the app is inaccessible.
- Prices change often and differ by region. Treat all prices as US list prices seen on or before 2026-09-30.

## Retired or excluded (not counted in the 15)

| App | Status | Source |
|---|---|---|
| Microsoft Lens (iOS/Android) | Retirement began 2025-09-15. New installs were disabled around mid-October 2025, the app was removed from the stores on 2025-11-15, and new scans stopped working on 2025-12-15. Microsoft points users to the scan feature in the Microsoft 365 Copilot app. | https://www.elevenforum.com/t/microsoft-lens-mobile-app-will-be-retired-starting-september-15-2025.38634/ ; https://techcrunch.com/2025/08/08/rip-microsoft-lens-a-simple-little-app-thats-getting-replaced-by-ai/ ; https://borncity.com/win/2025/08/09/microsoft-lens-app-is-being-discontinued/ |
| Microsoft 365 Copilot app scan (Lens replacement) | Left out as a standalone entry because it is a feature of a broader app. Reported to have a single scan mode, no dedicated whiteboard mode, and none of Lens's Read Aloud or Immersive Reader integration. | https://windowsforum.com/threads/microsoft-lens-retirement-2025-copilot-migration-timeline-and-guidance.377075/ ; https://www.pdfgear.com/scan-pdf/microsoft-lens-alternatives.htm |
| ABBYY FineScanner / FineReader PDF Mobile for Android, TextGrabber | ABBYY announced end of life on 2023-09-18. The iOS FineReader PDF app is still supported, but its Book Scanner feature was discontinued. FineScanner's current form is **FineReader PDF for iOS**, which is covered under ABBYY below. | https://support.abbyy.com/hc/en-us/articles/19657953214867-End-of-Life-ABBYY-Mobile-Apps-September-18-2023 ; https://apkpure.com/finereader-pdf-discontinued/com.abbyy.mobile.finescanner.free |

---

## The 15 apps

### 1. Adobe Scan (iOS, Android)
- **Price:** Free to download. Premium is about US$9.99/month with a 7-day trial on the yearly plan. Premium adds combining files (up to 20), OCR up to 100 pages, compression and more cloud storage. Sources: https://www.techradar.com/pro/software-services/adobe-scan-2025-review ; https://play.google.com/store/apps/details?id=com.adobe.scan.android&hl=en_US
- **Glare/shadow claims:** Adobe says the app uses AI to "correct perspective, sharpen handwritten or printed text, and remove glares and shadows". Its "Magic eraser" removes "thumbs, shadows, stains and creases". Source: https://acrobat.adobe.com/us/en/acrobat/mobile/scanner-app.html
- **Batch:** Multi-page capture into one PDF. Source: https://www.adobe.com/devnet-docs/adobescan/android/en/scan.html
- **Processing location, account and privacy:** Scans are saved to Adobe Document Cloud, and a sign-in (Adobe ID, Google, Facebook or Apple) is used. Adobe community threads report that users cannot stop cloud upload, which is used for OCR and storage. Sources: https://www.adobe.com/devnet-docs/adobescan/android/en/ ; https://community.adobe.com/t5/adobe-scan/new-adobe-scan-uploads-all-to-cloud/m-p/9531371
  - App Store privacy label **(extract; not loaded directly):** "Data Linked to You" covers Purchases, Contact Info, User Content, Search History, Identifiers and Usage Data. The listed purposes include Third-Party Advertising (User ID, Device ID). Source: https://apps.apple.com/us/app/adobe-scan-pdf-doc-scanner/id1199564834
  - A community thread titled "Adobe Scan app full of trackers" exists at https://community.adobe.com/questions-517/adobe-scan-app-full-of-trackers-12242. Its contents are unverified.
- **Integrity/forensic:** No public statement found on hashing or an audit trail. Password protection exists in the Acrobat ecosystem but is **unverified** for Scan specifically.
- **UI patterns worth copying:** Auto-capture with edge detection, one-tap Magic eraser, and filter presets. Source: https://acrobat.adobe.com/us/en/acrobat/mobile/scanner-app.html
- **Accessibility:** Published ACRs for iOS and Android, both dated 2020-04-22, on VPAT 2.3 covering WCAG 2.0 A/AA, Section 508 and EN 301 549. They are six years old. Sources: https://adobe.com/accessibility/compliance/adobe-scan-iOS-2020-04-22-acr.html ; https://www.adobe.com/accessibility/compliance/adobe-scan-android-2020-04-22-acr.html. Per-criterion results were not reviewed because the page load was blocked.

### 2. CamScanner (iOS, Android; INTSIG)
- **Price:** Free tier with a "Scanned with CamScanner" footer on exports. Premium was reported at US$4.99/month or US$49.99/year. The weekly price was also reported, but that figure is **unverified**. Premium removes the watermark, enables full OCR and full-resolution export, and raises cloud storage to 10 GB. Source: https://essexsoftware.com/scaniva/camscanner-free-vs-paid/ (a competitor's blog, so treat with caution)
- **Glare/shadow claims:** "No Shadow", "Lighten", "Magic Color" and "B&W" enhancement modes. In 2025 the "Magic Pro" filter was renamed "Omnifix", which is claimed to lift finger shadows and balance low-light brightness. Sources: https://www.prnewswire.com/news-releases/camscanner-upgrades-magic-pro-filter-to-omnifix-for-one-click-document-perfection-302492113.html ; https://www.globenewswire.com/news-release/2024/02/22/2833742/0/en/CamScanner-Launches-Magic-Pro-Filter-to-Make-Scanned-Documents-Perfect-with-Just-One-Click.html
- **Processing location, account and privacy:** Offers cloud sync. Whether filters run on the device or in the cloud is **unverified**.
  - App Store privacy label **(extract; not loaded directly):** "Data Used to Track You" lists Identifiers and Usage Data. Source: https://apps.apple.com/us/app/camscanner-pdf-scanner-app/id388627783
  - In August 2019, Kaspersky found a Trojan dropper (Necro.n) in an ad SDK inside the Android app, and Google removed the app from Play. It returned in September 2019 with its ad SDKs removed. Sources: https://www.xda-developers.com/camscanner-app-injecting-malware/ ; https://www.infosecurity-magazine.com/news/trojanized-camscanner-100m-google/
  - Privacy policy: https://static.intsig.net/r/terms/PP_CamScanner_en-us.html
- **Integrity/forensic:** No public statement found.
- **UI patterns worth copying:** A single one-tap "auto-fix" filter (Omnifix) plus named manual modes.
- **Accessibility:** No public statement found.

### 3. Genius Scan (iOS, Android; The Grizzly Labs)
- **Price:** The free tier is described as "fully functional", with unlimited scans and no watermark. **Ultra** costs about US$39.99/year and adds OCR, cloud export, smart renaming, document encryption and Genius Cloud backup. Sources: https://thegrizzlylabs.com/genius-scan/pricing/ ; https://play.google.com/store/apps/details?id=com.thegrizzlylabs.geniusscan.free&hl=en_US
- **Glare/shadow claims:** "Shadow removal and defect cleanup", "distortion correction" and batch scanning of "dozens of pages in seconds". No specific glare claim was found. Source: https://apps.apple.com/us/app/scanner-app-genius-scan/id377672876 **(extract)**
- **Processing location, account and privacy:** "OCR, PDF generation, and image processing are processed exclusively on your device". No account is needed; documents are uploaded only if the user creates a Genius Cloud account. Sources: https://help.geniusscan.com/security-and-privacy/privacy-and-security-overview ; https://help.geniusscan.com/security-and-privacy/privacy-policy
  - App Store label **(extract; not loaded directly):** "Data Not Linked to You" covers Usage Data. The extract also mentions data linked to you for app functionality (contact info, user content, diagnostics). Source: https://apps.apple.com/us/app/scanner-app-genius-scan/id377672876
- **Integrity/forensic:** PDF encryption, Face ID/Touch ID/password app lock. No hashing or audit trail. Source: https://help.geniusscan.com/security-and-privacy/privacy-and-security-overview
- **UI patterns worth copying:** Auto-detect, crop and clean in one pass; batch mode; filter presets (B&W, whiteboard, photo).
- **Accessibility:** No public statement found.
- **Note:** Its SDK publishes a privacy/security statement at https://geniusscansdk.com/legal/privacy-security/

### 4. Apple built-in scanner (Notes, Files; Continuity Camera to Mac)
- **Price:** Included with iOS, iPadOS and macOS.
- **Glare/shadow claims:** Apple's support pages describe auto-capture on edge detection and filters (colour, grayscale, B&W, photo). In iOS 26, flash and filter options can be set before capture. No explicit glare or shadow claim was found. Sources: https://support.apple.com/guide/iphone/scan-text-and-documents-iph653f28965/ios ; https://support.apple.com/en-us/108963
- **Batch:** Multi-page capture into one PDF. Same sources as above.
- **Mac path:** Finder > Import from iPhone or iPad > Scan Documents uses Continuity Camera and requires the same Apple ID. Source: https://support.apple.com/en-sa/guide/imac-pro/apd1c059dc3b/mac
- **Processing location, account and privacy:** Whether processing happens on the device is **unverified** (no Apple statement found). Notes sync via iCloud when enabled.
- **Integrity/forensic:** Notes supports locked notes. No hashing or audit trail was found.
- **Accessibility:** The OS has VoiceOver and Dynamic Type (https://www.apple.com/accessibility/features/). An AppleVis user thread reports that VoiceOver speaks positioning hints ("move camera slightly up") during capture, but that reading the captured result was difficult: https://www.applevis.com/forum/ios-ipados/how-accessible-document-scanner-ios-notes-app-voice-over-someone-who-completely. No per-feature ACR was found.

### 5. Google Drive scanner (Android, iOS)
- **Price:** Included with Google Drive, which needs a Google account.
- **Glare/shadow claims:** The "Enhance" feature, from December 2024, performs "white balance correction, shadow removal, contrast enrichment, auto sharpening, light improvement". Sources: https://9to5google.com/2024/12/15/google-drive-scanner-enhance/ ; https://www.androidauthority.com/google-drive-improved-scanner-mobile-3509225/
- **Processing location, account and privacy:** On Android the scanner is built on the ML Kit Document Scanner, and Google says "the entire document scanner flow operates on-device". Its features include removing fingers, stains and blemishes. The finished scan is saved to Drive, which is cloud storage. Sources: https://android-developers.googleblog.com/2024/02/ml-kit-document-scanner-api.html ; https://developers.google.com/ml-kit/vision/doc-scanner
- **Integrity/forensic:** No public statement found.
- **UI patterns worth copying:** A single "sparkle" auto-enhance button, and a consistent scanner UI shared across Drive, Files by Google and Pixel Camera.
- **Accessibility:** Google Workspace publishes VPATs for Drive, but none specific to the scanner was found. For the scanner: no public statement found.

### 6. Scanner Pro (iOS, iPadOS; Readdle)
- **Price:** Freemium. Scanner Pro Plus was US$19.99/year when it launched in 2020; the current price is **unverified**. The free tier watermarks shared documents. Plus adds on-device OCR (26 languages), full-text search and password protection. Sources: https://9to5mac.com/2020/12/10/scanner-pro-for-iphone-gets-ocr-new-design/ ; https://readdle.com/blog/scanner-pro-8
- **Glare/shadow claims:** The 2026 update claims better shadow removal, including coloured shadows, multiple overlapping shadows and shadows on patterned backgrounds. It runs automatically, "all processed on-device", and basic shadow removal is available to all users. Source: https://readdle.com/blog/why-scanner-pro-scans-look-better-than-ever
- **Processing location, account and privacy:** On-device processing (same source). iCloud sync. App Store privacy label: **unverified**.
- **Integrity/forensic:** App passcode and PDF password on Plus. No hashing.
- **Accessibility:** No public statement found.

### 7. vFlat Scan (iOS, Android; VoyagerX)
- **Price:** Free, with OCR capped at 100 pages before credits or ads. Reported subscription prices vary between sources (**unverified**). Sources: https://play.google.com/store/apps/details?id=com.voyagerx.scanner&hl=en_US ; https://sourceforge.net/software/product/vFlat-Scan/
- **Glare/shadow claims:** Flattens curved book pages, removes fingers automatically, and captures two-page spreads that are split automatically. **No dedicated glare-removal claim found**; one user review complains that glare causes light or missing text. Sources: https://www.vflat.com/en ; https://justuseapp.com/en/app/1540238220/vflat-scan-pdf-scanner/reviews
- **Processing location, account and privacy:** **unverified**.
- **UI patterns worth copying:** Automatic splitting of two-page spreads, finger removal, and interval (timer) capture for books (the timer is **unverified**).
- **Accessibility:** No public statement found.

### 8. TurboScan (iOS, Android; Piksoft)
- **Price:** One-time purchase of about US$5.99 to US$6.99 (sources disagree, so **unverified**). There is also a free Android version. Sources: https://apps.apple.com/us/app/turboscan-document-scanner/id1017559099 ; https://play.google.com/store/apps/details?id=com.piksoft.turboscan.free&hl=en_US&gl=US
- **Glare/shadow claims:** "SureScan" takes three shots of the same page and combines them into a sharper result, which it says helps in low light. Auto-detect and perspective correction. Same sources.
- **Processing location, account and privacy:** **unverified**.
- **UI patterns worth copying:** Multi-shot fusion, and one-tap "Email to myself".
- **Accessibility:** No public statement found.

### 9. SwiftScan (iOS, Android; Maple Media, formerly Scanbot)
- **Price:** Several tiers, including VIP at US$5.99/month or US$34.99/year and Plus at US$7.99–9.99/month or US$59.99/year (from the in-app purchase list, **unverified**). Sources: https://apps.apple.com/us/app/scanner-qr-code-automatic/id834854351 ; https://appadvice.com/app/swiftscan-ai-document-scanner/834854351
- **Glare/shadow claims:** Automatic edge detection and colour/grey/B&W filters. **No shadow/glare claim found.**
- **Integrity/forensic:** PDF password encryption and Face ID/Touch ID lock. Same sources.
- **Privacy:** Cloud integrations (iCloud, Dropbox, Google Drive). AI summarise and translate features are advertised; whether they use the cloud is **unverified**. Android package `net.doo.snap`: https://play.google.com/store/apps/details?id=net.doo.snap&hl=en_US
- **Accessibility:** No public statement found.

### 10. Tiny Scanner (iOS, Android; Appxy)
- **Price:** Tiny Scanner Pro was a US$4.99 one-time purchase on iOS. The subscription version is reported at US$3.99/month or US$19.99/year (**unverified**). Sources: https://itunes.apple.com/us/app/tiny-scanner-pro/id556500145 ; https://www.educationalappstore.com/app/tinyscan-pdf-scanner-to-scan-document-receipt-notes
- **Glare/shadow claims:** Automatic edge detection, "shadow removal" and text enhancement. Source: https://apps.apple.com/us/app/tiny-scanner-pdf-scanner-app/id595563753 **(extract)**
- **Privacy:** **unverified**.
- **Accessibility:** No public statement found.

### 11. ABBYY FineReader PDF (Windows, macOS; plus FineReader PDF for iOS, the successor to FineScanner)
- **Price:** Windows Standard US$99/year (or US$16/month), Corporate US$165/year, Mac US$69/year. Source: https://pdf.abbyy.com/pricing/ (via https://www.capterra.com/p/65868/ABBYY-FineReader/pricing/)
- **Cleanup claims:** An OCR editor with image preprocessing. The detailed feature list is at https://pdf.abbyy.com/media/3denzynd/brochure-finereaderpdf-full-feature-list-en.pdf (revision 2025-12-16). Specific glare or shadow claims are **unverified**.
- **Processing location:** Desktop OCR runs locally. Whether activation needs to be online, and what telemetry is sent, is **unverified**.
- **Integrity/forensic:** PDF passwords, redaction and digital signatures (per the feature list above; **unverified** at item level).
- **Accessibility:** **A VPAT is published**: https://support.abbyy.com/hc/en-us/articles/21406269069586-Voluntary-Product-Accessibility-Template-VPAT-for-FineReader-PDF, linked from https://pdf.abbyy.com/specifications/. Of all 15, this is the only desktop competitor with a published ACR.

### 12. ScanTailor Advanced (Windows, macOS, Linux; open source)
- **Price:** Free, GPL. Repositories: https://github.com/4lex4/scantailor-advanced (original fork) and https://github.com/ScanTailor-Advanced/scantailor-advanced. v1.1.1 is listed at https://scantailor.net/download/
- **Cleanup claims:** "Normalize illumination" before binarization and in colour areas, Sauvola/Wolf adaptive binarization, fill zones, despeckle, and auto, marginal and manual dewarping. Multi-threaded batch processing. Sources: https://github.com/4lex4/scantailor-advanced ; https://github.com/scantailor/scantailor/wiki/C.-Output-Tabs:-Despeckling-&-Fill-zones
- **Processing location, account and privacy:** Fully local. No account needed.
- **Integrity/forensic:** None.
- **UI patterns worth copying:** A staged pipeline (fix orientation > split pages > deskew > select content > margins > output) where each stage can be applied to all pages, and a thumbnail filmstrip.
- **Accessibility:** No public statement found.
- **Related:** "ScanTailor Spectre" is a newer fork for Apple silicon: https://github.com/abandoned-industries/scantailor-spectre

### 13. NAPS2 (Windows, macOS, Linux; open source)
- **Price:** Free and open source, with no ads. Source: https://naps2.net/ ; https://github.com/cyanfish/naps2
- **Cleanup claims:** Auto-deskew, crop, brightness and contrast. OCR in 100+ languages. Batch scanning with ADF and duplex. Command-line interface. Aimed at flatbed and ADF scanners rather than camera photos. Source: https://naps2.net/
- **Processing location, account and privacy:** Local, no account. A telemetry statement is **unverified**.
- **Integrity/forensic:** PDF encryption options are **unverified**.
- **Accessibility:** The changelog records fixes for "missing screen reader text for some buttons" and more default keyboard shortcuts. Shortcuts are configurable through appsettings.xml. Sources: https://github.com/cyanfish/naps2/blob/master/CHANGELOG.md ; https://github.com/cyanfish/naps2/issues/61. No VPAT.

### 14. VueScan (Windows, macOS, Linux; Hamrick Software)
- **Price:** Standard US$39.95 and Professional US$79.95 one-time, with one year of updates; lifetime updates ended for new Professional buyers in 2021. Subscriptions are also offered. One licence covers up to four computers. Sources: https://photoinfos.com/Fotosoftware/Vuescan/htm/vuescan-02-en.htm ; https://www.hamrick.com/purchase-vuescan-multiuser-license.html
- **Cleanup claims:** Scanner-driver-level colour, infrared dust removal and OCR. Its role is hardware scanning, not photo recovery. Specific glare claims: none found.
- **Processing location:** Local.
- **Accessibility:** No public statement found.

### 15. Readiris 17 (Windows, macOS; IRIS, a Canon company)
- **Price:** One-time purchase from about US$89–99 (Pro), Corporate about US$199. Sources: https://www.capterra.ca/software/177869/readiris-17 ; https://www.irislink.com/EN-US/c2436/Compare---Software---Readirs-17.aspx
- **Claims:** OCR in 138 languages, PDF compression and passwords, read-aloud, and voice annotations. Sources: https://www.irislink.com/EN-US/c1730/Readiris-17--the-PDF-and-OCR-solution-for-MAC-.aspx ; https://www.globenewswire.com/news-release/2018/04/30/1490392/0/en/Readiris-17-PDF-and-OCR-solution-for-Windows-and-Mac.html
- **Note:** Version 17 dates from 2018, so the product line is old.
- **Accessibility:** Read-aloud of PDFs is a feature. No VPAT was found.

---

## Summary matrix

Key: Y = claimed, N = not claimed or not found, ? = unverified.

| # | App | Desktop | Glare claim | Shadow claim | On-device claim | Account optional | Hash/audit trail | Encryption | Public ACR/VPAT |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Adobe Scan | N | Y | Y | N (cloud) | N | N | ? | Y (2020) |
| 2 | CamScanner | N (web ?) | N | Y | ? | ? | N | ? | N |
| 3 | Genius Scan | N | N | Y | Y | Y | N | Y | N |
| 4 | Apple Notes/Files | via Continuity | N | N | ? | Apple ID | N | locked notes | OS-level only |
| 5 | Google Drive scanner | N | N | Y | Y (scan) / cloud (save) | N | N | N | N (scanner) |
| 6 | Scanner Pro | N | N | Y | Y | ? | N | Y (Plus) | N |
| 7 | vFlat | N | N | ? | ? | ? | N | ? | N |
| 8 | TurboScan | N | N | N | ? | ? | N | ? | N |
| 9 | SwiftScan | N | N | N | ? | ? | N | Y | N |
| 10 | Tiny Scanner | N | N | Y | ? | ? | N | ? | N |
| 11 | ABBYY FineReader PDF | Y | ? | ? | Y (OCR) | ? | N | Y | **Y** |
| 12 | ScanTailor Advanced | Y | N | Y (illumination) | Y | Y | N | N | N |
| 13 | NAPS2 | Y | N | N | Y | Y | N | ? | N |
| 14 | VueScan | Y | N | N | Y | Y | N | N | N |
| 15 | Readiris 17 | Y | N | N | Y | ? | N | Y (PDF pw) | N |

None of the 15 claims SHA-256 hashing of originals, an append-only or hash-chained custody log, or a vault that seals the source image with its derivative.

---

## Where a desktop recovery and integrity app can credibly beat them

1. **Integrity and forensics.** None of the 15 publishes hashing, custody logs or before/after provenance. A hash-chained ledger with a verifier that can be exported would be a real difference. Claim only what the verifier proves.
2. **Privacy.** Only Genius Scan, Scanner Pro, Google's scan step (not its storage), and the desktop tools state local processing. Adobe Scan uploads to the cloud, and CamScanner's App Store label lists tracking identifiers. Being fully offline, with no account and no telemetry, is defensible if the app's App Store privacy label actually reads "Data Not Collected" and the code has no network calls. Publish that.
3. **Glare specifically.** Among the mobile apps, only Adobe claims glare removal. The others claim shadow removal. Inpainting of clipped glare, and contrast recovery around glare halos, are unoccupied as named features. To stay honest, show the recovered pixels as a mask or overlay, and never present inpainted content as original text.
4. **Desktop accessibility.** Among the desktop competitors, only ABBYY has a published VPAT. ScanTailor, NAPS2 and VueScan have none, and NAPS2's changelog shows screen-reader labels being fixed piecemeal. Publishing a WCAG 2.2 AA ACR at launch would put the app ahead of every desktop tool except ABBYY, and the mobile ACR from Adobe is from 2020.
5. **Before/after transparency.** None of the tools reviewed documents a side-by-side or slider comparison with an exportable diff. That is a pattern worth building and marking as a first-class control.
6. **Price model.** A one-time or lifetime price would contrast with Adobe, CamScanner and ABBYY subscriptions. TurboScan, VueScan and Readiris already sell one-time, so "no subscription" alone is not unique.

## Where it cannot honestly claim to beat them

1. **Capture.** No live camera capture, auto-capture or edge-guided shutter at launch. The mobile apps and Apple's Continuity Camera own capture.
2. **OCR and search.** If there is no OCR, it cannot compete with ABBYY (desktop), Readiris (138 languages), NAPS2 (100+ languages), Scanner Pro, Adobe or Genius Scan on searchable PDFs.
3. **Book dewarping and finger removal.** vFlat and ScanTailor Advanced (dewarp) and the ML Kit scanner used by Google Drive (finger removal) have these. Do not claim them unless they are built.
4. **Scanner hardware (TWAIN/WIA/SANE, ADF, duplex).** NAPS2 and VueScan cover these.
5. **Cloud sync and cross-device use.** Being offline by design means no sync. Present that as a trade-off, not an advantage, for users who want sync.
6. **Established OCR accuracy and scale.** ABBYY's engine is the long-standing benchmark. Do not compare recognition accuracy without a published test set.
7. **Shadow removal quality.** Scanner Pro (2026 model), Google Drive Enhance and CamScanner Omnifix all ship ML shadow removal. Claim superiority only with a public side-by-side benchmark on a shared image set.

---

## Accessibility checklist (WCAG 2.2 AA, desktop app with an HTML UI)

Target: meet all of these, then publish a VPAT 2.5 (INT edition) ACR covering WCAG 2.2, Section 508 and EN 301 549.

**Keyboard**
- [ ] 2.1.1 Keyboard: every function (open, recover, compare slider, mask toggle, vault seal, ledger verify, export) works without a pointer.
- [ ] 2.1.2 No keyboard trap, including in canvas and image viewers and in modal dialogs.
- [ ] 2.1.4 Character key shortcuts: single-key shortcuts can be turned off or remapped, or are active only while a component has focus.
- [ ] 2.4.3 Focus order is logical, and focus returns to the invoking control when a dialog closes.
- [ ] Before/after slider: arrow keys move it, Home and End jump to the ends, and it has `role="slider"` with `aria-valuenow` and `aria-valuetext` ("40% original").

**Focus and visibility**
- [ ] 2.4.7 Focus visible on every control.
- [ ] 2.4.11 Focus not obscured (minimum): sticky toolbars and toasts never fully cover the focused item.
- [ ] Focus indicator of at least 3:1 contrast against adjacent colours (supports 1.4.11).

**Contrast, colour and text**
- [ ] 1.4.3 Text contrast of at least 4.5:1 (3:1 for large text) in light, dark and high-contrast themes.
- [ ] 1.4.11 Non-text contrast of at least 3:1 for control boundaries, icons, focus rings and chart or mask outlines.
- [ ] 1.4.1 Colour is not the only signal: glare and inpaint masks, ledger "verified" or "broken" states and error states also use pattern, icon or text.
- [ ] 1.4.4 Resize text to 200% without loss. 1.4.10 Reflow at 320 CSS px width (roughly 400% zoom) without two-dimensional scrolling, except for the image canvas.
- [ ] 1.4.12 Text spacing overrides do not break the layout.
- [ ] Respect the OS text scale, Windows High Contrast / `forced-colors`, and `prefers-color-scheme`.

**Pointer and targets**
- [ ] 2.5.8 Target size (minimum): at least 24×24 CSS px, or enough spacing.
- [ ] 2.5.7 Dragging movements: the slider, crop handles and mask brush have a non-drag alternative (buttons or numeric input).
- [ ] 2.5.3 Label in name: the visible label text is contained in the accessible name.

**Motion and timing**
- [ ] 2.3.3 (AAA, recommended) and `prefers-reduced-motion`: no animated wipes or zooms when reduced motion is set.
- [ ] 2.2.1 / 2.2.2: long operations (batch recovery, sealing) do not time out and can be paused or cancelled. Progress is not conveyed only by animation.

**Screen reader**
- [ ] 4.1.2 Name, role and value on all custom controls. Use native elements first, ARIA only where needed.
- [ ] 4.1.3 Status messages: batch progress, "Sealed: SHA-256 …", verification results and errors are announced through `aria-live="polite"` (or `assertive` for errors) without moving focus.
- [ ] 1.1.1 Text alternatives: page thumbnails and before/after images get names such as "Page 3, recovered". Masks get a text summary ("Glare region 12% of page, inpainted").
- [ ] 1.3.1 Info and relationships: headings and landmarks in the HTML UI, and ledger rendered as a real `<table>` with header cells.
- [ ] 2.4.2 Page or window titles reflect the current document.
- [ ] 3.3.1 / 3.3.3 Error identification and suggestions (for example a bad vault passphrase).
- [ ] 3.3.8 Accessible authentication (minimum): vault unlock allows paste and password managers, and has no cognitive-test puzzles.
- [ ] 3.2.6 Consistent help: the help link sits in the same place on every screen.

**Testing matrix**
- [ ] NVDA and JAWS with Chromium/WebView2 on Windows, Narrator on Windows, VoiceOver on macOS, Orca on Linux (WebKitGTK or Chromium, depending on the shell).
- [ ] Keyboard-only pass, 200%/400% zoom pass, Windows contrast themes, macOS "Increase contrast" and "Reduce motion".
- [ ] Automated checks with axe-core in CI. Manual checks cannot be skipped.

---

## Candidate product-name conflict scan (one web search each; not legal clearance)

| Candidate | Findings | Risk (informal) |
|---|---|---|
| **Arcana Lumen** | No product with this exact name found. Separately, **LUMEN** is a registered US/EU trademark of Lumen Technologies (formerly CenturyLink), with registrations that cover software. "Arcana" marks exist, for example Arcana, LLC (US Reg. 87538457) and Arcana.io, a crypto-asset company. Sources: https://uspto.report/TM/90676976 ; https://uspto.report/TM/88642330 ; https://www.lumen.com/en-us/about/legal/digital-platform.html ; https://uspto.report/TM/87538457 ; https://www.arcana.io/terms-of-service | Medium: "Lumen" is a heavily used and litigated mark (see Lumen21 v. Lumen Technologies: https://news.bloomberglaw.com/ip-law/lumen21-files-trademark-suit-over-rivals-2020-lumen-rebrand) |
| **Arclight** | Many existing users: an "Arclight" App Store app (Distributor Software Solutions), ArcLight Software LLC (App Store developer), **Stanford's ArcLight**, which is software for discovering archival collections (an adjacent domain), ArcLight Capital (USPTO 76380384), ArcLight Cinemas, and ArcLight Strategy Systems, which has software trademarks. Sources: https://apps.apple.com/us/app/arclight/id1334635359 ; https://apps.apple.com/by/developer/arclight-software-llc/id1597801911 ; https://arclight.sites.stanford.edu/ ; https://uspto.report/TM/76380384 ; https://trademarks.justia.com/owners/arclight-strategy-systems-limited-1037232 | High: crowded, including in software and in the archives/documents domain |
| **Arcalume** | No software, app or trademark hits. Only incidental matches (a YouTube horror-fiction channel credit; the similar "Arcalune" is a music track). Sources: https://www.youtube.com/shorts/AsfIA0X34TI ; https://open.spotify.com/track/5Roj6LItrRv3Z3qG7uzimf | Low (from this search) |
| **Lumen by Arcana** | Same "Lumen" issue as above. It is also close in sound to **Lumin PDF**, a PDF app with scanning on the App Store and Google Play. Sources: https://apps.apple.com/us/app/lumin-view-edit-share-pdf/id1367372862 ; https://www.luminpdf.com/pdf-editor/scan-pdf | Medium–High: "Lumin" is in the same product category |
| **Arcana Clarity** | No exact match. The store namespace "Arcana" is crowded with tarot and astrology apps (for example Arcana AI Companion, Arcana: Personalized Astrology, Arcana Tarot) that use "clarity" language. Sources: https://play.google.com/store/apps/details?id=com.vbliss.auratarot&hl=en_US ; https://play.google.com/store/apps/details?id=com.beachheadapps.arcana&hl=en ; https://play.google.com/store/apps/details?id=com.arcana.app&hl=en_US | Low–Medium legally. Risk of confusion with the esoteric genre in store search. |
| **Arcanum Scan** | **Arcanum (Hungary)** is a company that digitises books and documents. Separately, **Arcanum** is an Android encrypted-vault app (VeraCrypt-compatible) on F-Droid and GitHub, updated 2026-09-14. There is also Arcanum Cyber (vulnerability scanning) and an arcanum.app®. Sources: https://www.arcanum.com/en/technology/digitizing-of-books/ ; https://en.wikipedia.org/wiki/Arcanum_(company) ; https://f-droid.org/en/packages/zip.arcanum/ ; https://github.com/Esdex/Arcanum ; https://arcanum-cyber.com/vulnerability-scanning/ ; https://arcanum.app/ | High: direct overlap in both domains (document digitisation and encrypted vaults) |

**Next step before choosing a name:** a formal clearance search in USPTO TESS (classes 9 and 42), EUIPO eSearch, UKIPO and CIPO, plus searches of the Microsoft Store, Mac App Store and Google Play. None of the above is legal advice.
