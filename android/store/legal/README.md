# Arcalume legal pack (drafts)

These are plain-language drafts written to match what the app actually does. They are not legal
advice. Have a lawyer read them before release, especially the terms (sections 8 to 11).

| File | Where it goes | Required by Play? |
|---|---|---|
| `PRIVACY_POLICY.md` | `arcana-forensics.com/arcalume/privacy`; URL in Play Console > App content | Yes |
| `TERMS_OF_USE.md` | `arcana-forensics.com/arcalume/terms`, linked from the app | No, recommended |
| `REFUND_POLICY.md` | `arcana-forensics.com/arcalume/refunds` | No, recommended |
| `THIRD_PARTY_NOTICES.md` | `arcana-forensics.com/arcalume/notices` | Licence obligation |
| `../SUPPORT_PAGE.md` | `arcana-forensics.com/arcalume/support` (the app's Help button) | Contact page is |

The Markdown here is the source. `python3 android/store/build_pages.py` renders it into
`site/arcalume/*.html`, which Cloudflare Pages serves once merged. Re-run it after every edit.

## Fill in before publishing

- `[LEGAL NAME OF PUBLISHER]`: the person or company that owns the Play developer account (the
  seller of record). Use the same name as on the Play payments profile.
- `[POSTAL ADDRESS]`: a business address. It is shown publicly under EU trader rules.
- `[DATE OF FIRST RELEASE]`: the day the app goes live in production.
- `[STATE AND COUNTRY]` and `[COUNTY, STATE]` in the terms (section 11): governing law and courts.
- Make sure **support@arcana-forensics.com** and **privacy@arcana-forensics.com** receive mail.

## Defaults I chose (change if you want)

- **Refunds:** full refund on request within 30 days, on top of Google's 48-hour window.
- **Liability cap:** what the customer paid in the last 12 months, or US$10.
- **Age:** 18+ target audience; the privacy policy also states the app is not directed at under-13s.
- **180-day offer wording:** may restart on reinstall; can change for new installs, but never
  shortens a running period.

## Before release

- The Apache License asks that any NOTICE files shipped with a component are passed on. Check the
  release bundle with `unzip -l app-play-release.aab | grep -i notice` and add any NOTICE text found
  to `THIRD_PARTY_NOTICES.md`. Update the version table when dependencies change.
- Confirm the US export-control position (`../PLAY_CONSOLE_ANSWERS.md`, last section).
- Check that "Arcalume" is clear to use as a trademark in your main markets (a USPTO and EUIPO
  search for class 9 software).
