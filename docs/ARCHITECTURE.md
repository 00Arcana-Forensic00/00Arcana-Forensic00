# Architecture Deep-Dive

## Design Principles

1. **Zero Trust:** No component trusts another without cryptographic verification
2. **Fail Secure:** Any error condition defaults to safe state (no acquisition)
3. **Auditability:** Every operation is logged with hash-chain verification
4. **Minimalism:** Fewest dependencies possible, all audited

## Component Interactions

### Acquisition Flow

┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Source │────▶│ Path Conf │────▶│ Hasher │
│ Filesystem │ │ Canonicalize│ │ Blake3/SHA │
└─────────────┘ └─────────────┘ └──────┬──────┘
│
┌─────────────┐ ┌─────────────┐ ┌──────▼──────┐
│ Ledger │◀────│ Custody │◀────│ Vault │
│ SQLite │ │ Chain │ │ AES-256 │
└─────────────┘ └─────────────┘ └─────────────┘

### Verification Flow
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Vault │────▶│ Decrypt │────▶│ Extract │
│ Blob │ │ AES-256-GCM│ │ Files │
└─────────────┘ └─────────────┘ └──────┬──────┘
│
┌─────────────┐ ┌─────────────┐ ┌──────▼──────┐
│ Report │◀────│ Verify │◀────│ Hash │
│ Match/Fail│ │ Chain │ │ Compare │
└─────────────┘ └─────────────┘ └─────────────┘

## Data Flow Security

### Path Confinement

All paths undergo canonicalization before any filesystem operation:

```rust
// Pseudo-code representation
fn safe_open(base: &Path, user_input: &str) -> Result<File> {
    let canonical = base.join(user_input).canonicalize()?;
    if !canonical.starts_with(base) {
        return Err(PathError::TraversalAttempt);
    }
    File::open(canonical)
}
