# Stripe alignment — premium audit-grade licensing

Payments are **not** part of the air-gapped acquire/vault/custody pipeline.
Cards never touch `arcana-acquire`, the case directory, or the field-test runner.
Checkout is hosted by Stripe. This site only links out.

A paid license is a seat/organization entitlement. It is **not** an expert-witness
report and not a chain-of-custody exhibit by itself.

Domain: https://arcana-forensics.com
Pricing: https://arcana-forensics.com/site/pricing.html
Success: https://arcana-forensics.com/site/checkout-success.html
Cancel: https://arcana-forensics.com/site/checkout-cancel.html

## Catalog

| Stripe product | List price | Who | Packet |
|---|---|---|---|
| Community Edition | $0 | researchers, OSS | `demo/opensource/` MIT |
| Professional License | **$3,500 / year / seat** | boutique labs, solo examiners | trial pack overlay + paid seat |
| Enterprise License | **$35,000 / year** | law firms, corporate security | unlimited seats in one org |
| Government / Federal | custom, **from $150,000 / year** | agencies | quote only; FedRAMP / CJIS / ITAR as required |
| Professional services | **$250–$500 / hour** | deployment, training, optional expert-witness *engagement* | billed as Stripe invoice or time entry |

## Dashboard products to create

1. **Arcana Professional** — recurring yearly, unit amount `350000` cents USD, quantity = seats.
   After-completion URL: `/site/checkout-success.html?sku=pro`.
2. **Arcana Enterprise** — recurring yearly, unit amount `3500000` cents USD, quantity 1 (org).
   Success URL: `/site/checkout-success.html?sku=ent`.
3. **Arcana Services retainer** (optional) — invoice or Payment Link; do not auto-charge hourly from the static site.
4. Government stays **Sales-led**. No public Payment Link. Button goes to `mailto:mitchell5584.dm@gmail.com?subject=Arcana%20Federal%20quote`.

Do not put `sk_live` or `sk_test` in this repository.
Paste only `https://buy.stripe.com/...` Payment Links into `site/stripe.config.js`.

## Trial overlay

Community remains free. Professional may use a Stripe **14-day subscription trial**
that matches packet AF-FT-2026-0921, then $3,500/year per seat.
Enterprise and Government are not self-serve trials.

## Air-gap contract

Stripe sees payer email and card. It does not receive vault blobs, `custody.sqlite`,
or customer evidence. Expert-witness *testimony* is a separate human engagement,
billed hourly. The binary does not testify.
