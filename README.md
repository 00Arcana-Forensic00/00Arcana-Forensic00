# Arcana Forensics
**Air-gapped digital evidence acquisition with a custody chain that survives its own machine.**

> Acquire. Seal. Verify. — Read-only acquisition, authenticated AES-256-GCM
> vault sealing, and a hash-chained custody ledger. A local chain proves entries agree
> with each other, not when they were written; record the final hash somewhere outside
> the case (see the roadmap note below).

## Why Arcana
| | Arcana | Typical FOSS tools |
|---|---|---|
| Air-gapped operation | ✅ zero network stack | varies |
| Vault sealing | ✅ AES-256-GCM, per-file random nonce, 100,000-round SHA-256 key stretch (Argon2id planned) | often none |
| Custody ledger | ✅ SHA-256 hash chain in a plain SQLite file (external timestamp anchoring is not in this tree) | local chain only |
| Scope | ✅ acquisition only — destructive ops permanently removed | n/a |

## Get Arcana
Community Edition source is in this repository (MIT). Paid tiers and verified binary
releases: **[arcana-forensics.com/try](https://arcana-forensics.com/try)**

## Format & verification
- Vault blob layout: `ARCN | version | salt(16) | nonce(12) | ciphertext+tag` (see [SECURITY.md](SECURITY.md))
- Ledger line hash: SHA-256 over `ts|operator|action|path|sha256|prev_hash`
- Roadmap, not shipped in this tree: a published ARCN2 spec and external timestamping
  (OpenTimestamps or RFC 3161). Until then, record the final ledger hash outside the case.
- Known gap: `verify` does not yet cross-check the ledger against `manifest.json`.

## Trust model
Community Edition source is MIT (see [LICENSE](LICENSE) and [NOTICE](NOTICE)). See [SECURITY.md](SECURITY.md)
for the product boundary and [docs/FIELD_TEST.md](docs/FIELD_TEST.md) for the automated
field-test protocol.

**Licensing:** MIT Community Edition plus paid tiers. See [LICENSE](LICENSE) and [NOTICE](NOTICE), or
[site/pricing.html](site/pricing.html).

Use only on systems and files you are authorized to examine.
