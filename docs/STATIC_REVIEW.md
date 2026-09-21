# Static review policy

Inspection of this pack is **source-level**. Do not open live case directories,
vault blobs, or customer files to “test” the product.

## Allowed

- Read the raw crates under `crates/*/src/`
- Run `cargo test --workspace` (unit tests use synthetic byte strings only)
- Run `arcana-acquire` against `demo/opensource/` or `demo/trial/` only
- GitHub Actions `field-test` job, which is hard-wired to `demo/opensource/01-acquire/evidence`

## Not allowed

- Uploading `vault/`, `custody.sqlite`, or a real case directory as a CI artifact
- Pointing acquire at an operator workstation, phone dump, or customer share
- Printing passphrases, full host paths, or plaintext evidence in logs
- Network clients, telemetry, or cloud connectors (none exist in these crates)

## What the raw code guarantees

| Check | Where |
|---|---|
| No `reqwest` / `ureq` / sockets | crate sources |
| `WalkDir::follow_links(false)` | `arcana-acquire` |
| Symlinks and device nodes skipped | `reject_special_file` |
| Output confined with `strip_prefix` | `confined_path` |
| Unique nonce per seal | `arcana-vault` |
| CI input path is demo-only | `.github/workflows/field-test.yml` |
