# Play Console answers: every App content form

Answers for Play Console > **Policy and programs > App content**, plus the store settings and
declarations Play asks for. They match the code on this branch. If a later change adds
networking, analytics, crash reporting, ads or a new permission, these answers must change
before that release.

## Privacy policy

URL: `https://arcana-forensics.com/arcalume/privacy`
(source: `legal/PRIVACY_POLICY.md`, page: `site/arcalume/privacy.html`). The page must be live
before you submit. The app links to it from Plan > About.

## Ads

**Does your app contain ads?** No.

## App access

**All functionality is available without special access.** No login, account or code is needed.
Paste `scripts/REVIEWER_NOTES.md` into the instructions box anyway; it tells reviewers how to
reach every screen in under a minute with the built-in sample page.

## Content rating (IARC questionnaire)

- Email for rating notices: support@arcana-forensics.com
- Category: **All other app types** (utility, productivity, communication or other).
- Violence, sexuality, language, controlled substances, crude humour, fear, gambling: **No** to
  every question.
- Does the app allow users to interact or exchange content with other users? **No.**
- Does the app share the user's current physical location with other users? **No.**
- Does the app allow users to purchase digital goods? **Yes** (one-time Pro unlock).
- Does the app contain or promote web browsing / unrestricted internet access? **No.**
- Is the app a news app or a web browser? **No.**

Expected result: Everyone / PEGI 3 / USK 0, with an "In-app purchases" notice.

## Target audience and content

- Target age groups: **18 and over** only. Arcalume is for document work (legal, insurance,
  investigations, records, personal paperwork) and is not designed for children.
- Could the app unintentionally appeal to children? **No** (no characters, games or child-oriented
  imagery).
- Because no under-13 group is selected, the Families policy does not apply.

## News app

**Is your app a news app?** No.

## Data safety

Answer the form as follows.

- **Does your app collect or share any of the required user data types?** **No.**
  Photos, vaults and the custody log are processed and stored only on the device, in app-private
  storage. The packaged app has no network permission (CI fails the build if it asks for one),
  so it cannot transmit them. Data processed only on the device is not "collected" under Play's
  definition.
- **Is all of the user data collected by your app encrypted in transit?** Not asked once you
  answer No above (nothing is transmitted).
- **Do you provide a way for users to request that their data is deleted?** Not asked once you
  answer No above. (Users delete vaults in the app, or clear storage or uninstall.)
- **Purchases**: Google Play handles payment. Arcalume receives only the purchase state and token
  from the Play Store app and stores a "Pro unlocked" flag locally. Google's own collection is
  covered by Google's disclosures, not this form.
- Optional badge: you may tick **Independent security review: No** (none has been done) and leave
  "Committed to follow the Play Families Policy" unticked.

Result shown on the listing: "No data collected" and "No data shared with third parties".

## Government apps

**Is your app developed by or on behalf of a government?** No.

## Financial features

**Does your app provide any financial features?** **My app doesn't provide any financial features.**
(Selling Pro through Play Billing is not a financial feature.)

## Health

**Does your app have health features?** No.

## Advertising ID

**Does your app use advertising ID?** **No.** The manifest declares no `AD_ID` permission. Before
release, confirm with `aapt2 dump permissions` on the release build that no library added
`com.google.android.gms.permission.AD_ID`; the CI no-network check prints the full permission list.

## Sensitive permissions and APIs

| Permission | Why | Declaration form? |
|---|---|---|
| `CAMERA` | Taking photos of documents inside the app. Optional: import works without it. | No form |
| `com.android.vending.BILLING` (added by Play Billing, play build only) | The one-time Pro purchase. | No form |

No storage, photo/video, location, contacts, SMS, call log, accessibility service, foreground
service, exact alarm or "all files access" permission is requested. Import uses the system Photo
Picker and file picker, and export uses the system "save as" dialog, so the **Photo and video
permissions** declaration does not apply.

## Store settings

- App category: **Productivity**. Tags: Document scanner, PDF & document tools.
- Contact details: email support@arcana-forensics.com, website
  `https://arcana-forensics.com/arcalume/support`. A phone number is optional, unless you declare
  trader status (below), which shows it publicly.
- Pricing: **Free** app with in-app products. In-app product `arcalume_pro`, one-time, US$5.99,
  with Play's suggested local prices.
- Countries: all where Play sells paid apps, minus any you choose to exclude. Excluding embargoed
  countries is handled by Google.

## EU Digital Services Act: trader status

Play requires every developer to declare whether they are a **trader** (acting for business
purposes) for the EU. Selling Pro means you are almost certainly a trader. Play then shows your
legal name, address, phone and email publicly on the listing in the EU. Use a business address
and phone number if you do not want your home details shown.

## Export compliance (US encryption rules)

Arcalume uses standard encryption (Argon2id, AES-256-GCM, SHA-256, Ed25519) to protect the user's
own data. Under US Export Administration Regulations this is normally mass-market software
(ECCN 5D992.c) that can be exported under licence exception ENC, and Play's distribution is
covered. Depending on the classification, an **annual self-classification report** to the US
Bureau of Industry and Security (due each February 1) may be required. Confirm this with a
qualified adviser before release; it takes a few minutes to file if needed.
