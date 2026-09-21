# Arcana Forensics demo packs

Two packs ship with the open-source tree:

| Pack | Path | Who it is for | What it contains |
|---|---|---|---|
| Open source | `demo/opensource/` | anyone building from source | sample evidence, vault format card, custody SQL, site copy |
| Trial (14-day) | `demo/trial/` | evaluation before a paid license | capped case, known trial passphrase, sealed vault samples, enterprise schema preview |

Neither pack includes live customer data. All files are synthetic.

## Trial rules (content policy, not DRM)

- 14-day evaluation window from first `acquire` on a trial case id
- Max **5** regular files per case
- Max **1 MiB** per file
- Passphrase for the pre-sealed trial vault is published below on purpose
- No disk imaging, no device wipe, no cloud connectors

Published trial passphrase (synthetic only):

```
trial-pack-passphrase
```

## Generate a live sealed case from these packs

```bash
cargo build -p arcana-acquire
export ARCANA_VAULT_PASSWORD='trial-pack-passphrase'
python3 demo/scripts/make_evidence.py
python3 demo/scripts/seal_demo.py demo/trial/02-vault-trial/plaintext/ticket.txt demo/trial/02-vault-trial/sealed/ticket.arcv "$ARCANA_VAULT_PASSWORD"

./target/debug/arcana-acquire acquire \
  --path demo/opensource/01-acquire/evidence \
  --out demo/generated-oss-case \
  --operator 'oss-demo' \
  --case-id oss-demo-001 \
  --max-bytes 1048576
```
