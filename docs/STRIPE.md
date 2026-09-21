# Stripe alignment

Payments are **not** part of the air-gapped acquire/vault/custody pipeline.
Cards never touch `arcana-acquire`, the case directory, or the field-test runner.
Checkout is hosted by Stripe. This site only links out.

Domain: https://arcana-forensics.com
Success: https://arcana-forensics.com/site/checkout-success.html
Cancel: https://arcana-forensics.com/site/checkout-cancel.html

## Products to create in the Stripe Dashboard

| Stripe product | Maps to | Mode | Notes |
|---|---|---|---|
| Arcana OSS | `demo/opensource/` | $0 / no SKU | MIT download only. No Payment Link. |
| Arcana Field Trial | packet AF-FT-2026-0921, `demo/trial/` | Subscription, **14-day trial**, then paid | Same window as the paperwork |
| Arcana Lab Seat | paid operator seat | Subscription or one-time | After trial. Still no cloud evidence upload. |

Do not put `sk_live` or `sk_test` in this repository. Payment Links are enough for a static GitHub Pages / Cloudflare Pages site.

## Dashboard steps

1. https://dashboard.stripe.com/payment-links
2. Create **Arcana Field Trial**: recurring price, trial period 14 days, after-completion redirect to `/site/checkout-success.html`.
3. Create **Arcana Lab Seat**: recurring or one-time, same success/cancel URLs.
4. Branding: statement descriptor `ARCANA FORENSICS`, support `mitchell5584.dm@gmail.com`.
5. Paste the two `https://buy.stripe.com/...` URLs into `site/stripe.config.js`.
6. Optional: custom domain `pay.arcana-forensics.com` in Stripe Checkout settings.

## Air-gap contract

Stripe sees payer email and card. It does **not** receive vault blobs, `custody.sqlite`, or customer evidence.
A paid receipt is a license/seat record. It is not a chain-of-custody exhibit.
