# Security Policy

## Supported Versions

| Version | Supported | Security Fixes |
|---------|-----------|----------------|
| 1.0.x   | ✅ Yes    | Current release |
| 0.9.x   | ❌ No     | Upgrade to 1.0.x |

## Reporting Vulnerabilities

**DO NOT** open public GitHub issues for security vulnerabilities.

Instead, report via:
- Email: security@arcana-forensics.com
- GPG Key: [security@arcana-forensics.com.asc](https://arcana-forensics.com/security.asc)
- Key Fingerprint: `A1B2 C3D4 E5F6 7890 1234 5678 9ABC DEF0 1234 5678`

### Response Timeline

| Severity | Acknowledgment | Fix Released |
|----------|---------------|--------------|
| Critical | 24 hours | 7 days |
| High | 48 hours | 14 days |
| Medium | 72 hours | 30 days |
| Low | 1 week | Next scheduled release |

### Scope

In-scope:
- Cryptographic implementation flaws
- Memory safety violations
- Path traversal vulnerabilities
- Custody ledger tampering

Out-of-scope:
- Social engineering attacks
- Physical access exploits
- Compromised operator workstations

## Security Measures

### Build Security

- Reproducible builds via `cargo build --locked`
- Dependency auditing via `cargo audit`
- SBOM generation for supply chain transparency
- Signed release artifacts with SHA-256 checksums

### Runtime Security

- No network stack initialization
- Memory pages locked via `mlock` (Unix) / `VirtualLock` (Windows)
- Zero-on-drop for sensitive buffers
- Sandboxed file operations with path validation

### Cryptographic Assurance

- AES-256-GCM with 128-bit authentication tags
- Argon2id with conservative parameters (64MB memory)
- Cryptographically secure RNG via `getrandom`
- No algorithm agility—only audited primitives

## Incident Response

In the event of a security incident:

1. **Immediate:** Isolate affected systems
2. **Assessment:** Determine scope of compromise
3. **Notification:** Affected customers notified within 72 hours
4. **Remediation:** Patch released and deployment guidance provided
5. **Post-mortem:** Public disclosure after 90 days (if applicable)

## Compliance

Security practices align with:
- ISO 27001 Information Security Management
- SOC 2 Type II Security Controls
- NIST Cybersecurity Framework

## Acknowledgments

We thank the following researchers for responsible disclosure:

- [Your name here] - [Vulnerability description]
