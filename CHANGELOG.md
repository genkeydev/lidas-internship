# Changelog

## [1.0.0] - 2026-08-23

### Added
- SSH brute force detection (SSH-001): sliding window, 5 failures in 60s
- SQL injection detection (HTTP-001): 6 regex patterns
- Suspicious user agent detection (HTTP-002)
- Canary token detection (CANARY-001): paths and SSH usernames
- Directory scan detection (HTTP-003)
- Credential stuffing detection (HTTP-004)
- HMAC-SHA256 chained audit log with tamper verification
- CLI: scan, tail, verify subcommands
- Docker: distroless, non-root, read-only log mount
- CI: test (≥80% coverage), SAST (Semgrep), container scan (Trivy)

### Security
- All threat model items from docs/THREAT_MODEL.md addressed
- HMAC key file created with 0600 permissions on first run
- Audit log is append-only; no read-modify-write possible via CLI