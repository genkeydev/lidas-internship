# AlertDesk Security Assessment


## Summary

AlertDesk checks bearer tokens against role mappings in `config/client-spec.json` and applies role checks to ticket actions. The tokens are fixed lab values, so they identify a configured role rather than securely verifying a real user's identity. This is suitable only for the stated lab scaffold.

Do not deploy this authentication setup for real users or sensitive data. Before production use, replace stub tokens with an authentication system that supports identity, token expiry and revocation, and secure transport.

## Findings by relevant OWASP Top 10:2025 categories

### A01:2025 — Broken Access Control

**Current safeguards:** Routes require role permissions for create, list, get, assign, and transition actions. Status changes are checked against the configured transition rules.

**Risk:** Every role allowed to list or get tickets can access all tickets. The current code does not show per-user, team, or tenant restrictions. This may be acceptable for the lab, but would expose tickets if users should only see records within their assigned scope.

**Next step:** Define the intended ticket visibility rules and enforce them on list, get, assign, and transition operations before adding real users.

### A02:2025 — Security Misconfiguration

**Current safeguards:** The project describes its tokens as lab stubs, and the API documents its purpose.

**Risk:** OpenAPI and Swagger documentation are enabled by default. The sample tokens are stored in the repository's client specification. This is convenient for the lab but should not be treated as safe production configuration.

**Next step:** For any deployment with real data, review documentation exposure and move credentials to an appropriate secret-management mechanism.

### A03:2025 — Software Supply Chain Failures

**Observation:** The project specifies minimum dependency versions in `pyproject.toml`. This assessment did not verify a lock file, dependency scanning, or the integrity of installed packages.

**Next step:** Add dependency review and update checks to the project workflow before production use.

### A04:2025 — Cryptographic Failures

**Risk:** Bearer tokens are credentials. Anyone who obtains a token can use its associated role. The application code does not configure transport encryption; HTTPS must be provided by the deployment environment.

**Next step:** Require HTTPS wherever tokens are sent, and replace the fixed lab tokens with credentials that can be rotated and revoked.

### A05:2025 — Injection

**Current safeguard:** Database operations shown in the application use SQL parameters for user-controlled values, which reduces SQL injection risk in those queries.

**Limit:** This is a code review of the visible queries, not a complete security test.

**Next step:** Keep using parameterized queries for all database operations.

### A06:2025 — Insecure Design

**Risk:** The authentication design intentionally maps static shared tokens directly to roles. It does not provide individual user identity, token expiry, or revocation. This limits accountability and incident response.

**Next step:** Treat the scaffold as lab-only and design production identity, authorization, and credential lifecycle requirements before expanding deployment.

### A07:2025 — Authentication Failures

**Risk:** The tokens in `config/client-spec.json` are fixed sample values. The code checks whether a supplied token appears in that file, but the tokens do not expire or have a revocation mechanism. The HTTP Bearer scheme documents how clients send credentials; it does not make the tokens cryptographically secure.

**Next step:** Do not reuse the sample tokens outside the lab. Replace them with an authentication system that supports individual identities, expiration, rotation, and revocation.

### A09:2025 — Security Logging and Alerting Failures

**Current safeguards:** Ticket creation, assignment, and status transitions write audit rows.

**Risks:** Audit rows record the actor's role rather than a distinct user identity. Event details include ticket titles, assignees, and status changes, which may contain sensitive information. The table schema does not enforce append-only behavior, and this review did not verify log access controls, retention, or alerting.

**Next step:** Define what information may be logged, minimize sensitive details, and add appropriate access, retention, and integrity controls before production use.

### A10:2025 — Mishandling of Exceptional Conditions

**Current safeguards:** The application returns explicit responses for several expected conditions, including missing or unknown tokens, insufficient role permissions, missing tickets, invalid severities, and illegal status transitions.

**Limit:** This assessment did not evaluate every unexpected database or runtime failure.

**Next step:** Review error handling for unexpected failures and ensure responses do not expose internal details.

## Scope and limitations

This assessment covers the current code scaffold and its documented lab configuration. It does not verify deployment settings, HTTPS termination, host security, dependency integrity, or operational monitoring. AlertDesk is an internship project scaffold, not a production security platform.

## OWASP reference

- [OWASP Top 10:2025](https://top10.owasp.org/2025/)
- [A01:2025 — Broken Access Control](https://top10.owasp.org/2025/A01_2025-Broken_Access_Control/)
- [A07:2025 — Authentication Failures](https://top10.owasp.org/2025/A07_2025-Authentication_Failures/)
- [A09:2025 — Security Logging and Alerting Failures](https://top10.owasp.org/2025/A09_2025-Security_Logging_and_Alerting_Failures/) 