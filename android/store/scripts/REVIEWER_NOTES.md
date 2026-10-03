# Notes for Google Play review

Paste the block below into **App content > App access > Instructions** (choose "All
functionality is available without special access"), and keep it handy for any policy question
from Play.

```
No login, account or code is needed. Everything works offline.

To see every feature in under a minute:
1. Open the app and tap "Try a sample page". The built-in sample photo is processed on the
   device (a few seconds).
2. Recover tab: drag the compare slider, turn on "Show filled areas" (magenta hatching marks
   pixels the app had to fill) and "Show reading order". Scroll to "What Arcalume found and did".
3. Tap "Seal as evidence". Enter any passphrase of 12 or more characters twice, tick the box and
   tap Seal. Sealing takes a few seconds on purpose (Argon2id key derivation).
4. Vault tab: the sealed vault is listed. Tap "Check the log" to verify the custody log.
5. Plan tab: new installs have Pro free for 180 days, so all Pro features are unlocked for review.
   The one-time Pro product is "arcalume_pro".

Permissions: CAMERA is used only for the in-app document camera and is optional (import uses the
system Photo Picker). The app declares no internet permission and collects no data.
```

## If Play asks about the "forensics" wording

Arcalume is a document repair and record-keeping utility. It does not access other apps' data,
recover deleted files, bypass security or monitor anyone. "Forensic" refers to marking every
change it makes and keeping a tamper-evident log of what the user sealed.
