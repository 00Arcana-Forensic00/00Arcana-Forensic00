# Play Console answers: Data safety, permissions, content

These answers match the code as of this branch. If a later change adds networking,
analytics or crash reporting, these answers must change before release.

## Data safety

- **Does your app collect or share any of the required user data types?** No.
  Photos, vaults and the custody log are processed and stored only on the device, in app-private
  storage. The app has no network permission (CI enforces this), so it cannot transmit them.
- **Is all of the user data collected by your app encrypted in transit?** Not applicable (nothing is transmitted).
- **Do you provide a way for users to request that their data is deleted?** Not applicable
  (nothing is collected). Users delete vaults in the app, or uninstall.
- Purchases: Google Play handles payment. Arcalume receives only the purchase state and token
  from the Play Store app and stores a "Pro unlocked" flag locally. Google's own collection is
  covered by Google's policies, not this form.

## Permissions

| Permission | Why |
|---|---|
| `CAMERA` | Taking photos of documents in the app. Optional: import works without it. |
| `com.android.vending.BILLING` (added by Play Billing, play build only) | The one-time Pro purchase. |

No storage permission is requested: import uses the system Photo Picker and file picker, and
export uses the system "save as" dialog.

## Content rating questionnaire

Utility/productivity app. No user-generated content shared with others, no violence, no
gambling, no location, no communication between users.

## Target audience

18+ (professional users: legal, insurance, investigation, records). Not designed for children.

## Privacy policy

Play requires a public URL. Publish `restore/store/PRIVACY.md` (it covers the Android app) at `https://arcana-forensics.com/arcalume/privacy` before submission.
