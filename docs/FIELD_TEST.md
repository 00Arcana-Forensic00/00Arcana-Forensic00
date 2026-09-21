# Field test authorization and confirmation

**Packet ID:** AF-FT-2026-0921  
**Issued:** 21 September 2026  
**Repository:** https://github.com/mitchell5584dm-tech/00Arcana-Forensic00  
**Domain:** https://arcana-forensics.com

## License that travels with the code

Community Edition source is MIT. See `/LICENSE` and `/NOTICE`.

Paid overlay (does not replace MIT on the public tree):

| Tier | Price |
|---|---|
| Community Edition | Free |
| Professional License | $3,500 / year / seat |
| Enterprise License | $35,000 / year (unlimited seats, one org) |
| Government / Federal | custom from $150,000 / year |
| Professional services | $250–$500 / hour |

Checkout: https://arcana-forensics.com/site/pricing.html  
Stripe sees payer email and card only. It does not receive vault blobs or `custody.sqlite`.
A payment receipt is not a custody exhibit. Expert-witness work is a separate human engagement.

## Field-test overlay (does not replace MIT)

- Synthetic files only (`demo/` or other authorized lab samples)
- Trial window: 21 September 2026 through 5 October 2026 unless extended
- Trial pack cap: 5 files, 1 MiB each
- Published demo passphrase: `trial-pack-passphrase`
- No disk wipe, no live customer data, no card data in the CLI

## Automated field test

Workflow: `.github/workflows/field-test.yml`

On each push to `main`, on pull requests, nightly at 11:17 UTC, and via
workflow_dispatch the job:

1. `cargo test --workspace`
2. `cargo build -p arcana-acquire`
3. `python3 demo/scripts/make_evidence.py`
4. `arcana-acquire acquire` on the open-source demo evidence
5. `arcana-acquire verify` with the published passphrase
6. Uploads `field-test-confirmation.txt` as a workflow artifact

A green `field-test` check on the commit is the machine confirmation.
Attach that log to this worksheet when you file a human confirmation.

## Human confirmation block

```
Tester: ______________________   Date: __________
Lab:    ______________________   Commit: ________
Result: PASS / FAIL / PASS-WITH-NOTES
```
