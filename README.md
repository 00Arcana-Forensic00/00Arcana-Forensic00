# Arcana Forensics
**Air-gapped digital evidence acquisition with a custody chain that survives its own machine.**

> Acquire. Seal. Anchor. Verify. — Read-only acquisition, authenticated AES-256-GCM
> vault isolation, a hash-chained custody ledger, and timestamp anchoring that lets an
> independent verifier prove your ledger existed *when you said it did* — without
> trusting us.

## Why Arcana
| | Arcana | Typical FOSS tools |
|---|---|---|
| Air-gapped operation | ✅ zero network stack | varies |
| Vault sealing | ✅ AES-256-GCM + Argon2id | often none |
| Custody ledger | ✅ SHA-256 hash chain + **external timestamp anchoring** | local chain only |
| Scope | ✅ acquisition only — destructive ops permanently removed | n/a |

## Get Arcana
The engine is developed in a private workspace and distributed as **verified binary
releases**. Download and verification instructions: **[arcana-forensics.com/try](https://arcana-forensics.com/try)**

## Format & verification (open)
- [ARCN2 Vault Format Specification](docs/ARCN2-SPEC.md) — open format, independently implementable
- [Custody Anchoring](docs/ANCHORING.md) — Merkle manifests, OpenTimestamps bridge, RFC 3161 option

## Document reconstruction (Python)
[`recon/`](recon/README.md) repairs lighting-damaged document photos (shadow
flattening, glare handling), maps multi-column reading order, and seals the
result in ARCN v1 vault blobs readable by `arcana-vault`. Its README lists
what is implemented and what is still aspirational.

## Trust model
Open format and KDF parameters. Closed implementation. See [SECURITY.md](SECURITY.md)
for the product boundary and [docs/FIELD_TEST.md](docs/FIELD_TEST.md) for the automated
field-test protocol.

**Licensing:** Commercial. See [LICENSE](LICENSE) and [NOTICE](NOTICE), or
[site/pricing.html](site/pricing.html).

Use only on systems and files you are authorized to examine.
