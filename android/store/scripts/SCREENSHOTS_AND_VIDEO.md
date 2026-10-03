# Screenshots, captions and promo video

## Screenshots

`android/tools/beta_smoke.sh` drives the app on an Android emulator and saves eight screenshots
at 1080x1920 with a clean status bar (09:30, full battery), named in this order. They use only the
app's built-in sample page, so no real document or competitor imagery appears. Play needs 2 to 8
phone screenshots; use all eight in this order. The caption is an optional text band to add above
each screenshot in a design tool (keep it to the wording here, which matches what the app does).

| File | Caption (max ~30 characters) | Shows |
|---|---|---|
| `01-start.png` | Damaged page? Start here | Empty state, camera, import and sample |
| `02-recovered.png` | Light and shadow, evened out | Compare slider on the sample page |
| `03-filled-areas.png` | Every filled pixel marked | Magenta hatching on filled glare cores |
| `04-findings.png` | Plain-language findings | "What Arcalume found and did" |
| `05-sealed.png` | Sealed, with a fingerprint | Sealed dialog with the log fingerprint |
| `06-vault.png` | Your vault, on your phone | Vault list |
| `07-log-checked.png` | Check the chain any time | "Chain intact" after Check the log |
| `08-plan.png` | 180 days of Pro, free | Plan tab with the free Pro period |

Do not add claims to captions that are not in `LISTING.md`'s claim map (for example
"court-ready", "AI" or "tamper-proof").

## Feature graphic (1024x500)

Dark navy background (#1B2A3A), the Arcalume icon on the left, and the line "Revive the page.
Prove every change." on the right. No device frame, no price, no "free" or "best" wording (Play
rejects those in graphics).

## Promo video script (30 seconds, optional YouTube link)

Screen recording of the sample flow on a phone, with on-screen text and optional voice-over.

| Time | Picture | Voice-over / on-screen text |
|---|---|---|
| 0-4 s | A photo of a page with a bright glare spot | "Glare. Shadows. A page you can't read." |
| 4-10 s | Tap "Try a sample page"; the compare slider sweeps across | "Arcalume evens out the light and brings back faded text that's still in the photo." |
| 10-15 s | "Show filled areas" on; magenta hatching appears | "Where nothing was left, it fills smoothly and marks every filled pixel. It never invents text." |
| 15-21 s | Seal as evidence, passphrase, Sealed dialog | "Seal the original and the recovered copy into an encrypted vault." |
| 21-26 s | Vault tab, Check the log, "Chain intact" | "Every sealing is chained in a custody log you can check any time." |
| 26-30 s | Icon and name on navy | "Arcalume. No internet, no account. On Google Play." |

Record it from the beta build on a real phone, or from the emulator with
`adb shell screenrecord /sdcard/promo.mp4` while running the same steps.
