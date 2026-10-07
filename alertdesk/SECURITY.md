# Security Policy

## Reporting a vulnerability

If you find a vulnerability in AlertDesk, report it privately to the
maintainer:

- **Name:** George
- **Email:** baningeorge@gmail.com

Do not publicly disclose vulnerabilities or include sensitive information
in public issues.

## Authentication (scaffold vs Month 4)

The current lab uses stub bearer tokens for authentication.

The lab tokens and their associated roles are defined in:

`config/client-spec.json`

These tokens are intended for the internship lab environment only and
must not be reused as production credentials.

Proper authentication is planned for Month 4.

## Database and audit log

AlertDesk stores ticket data in the configured SQLite database.

The database location is controlled by the `ALERTDESK_DB` environment
variable.

Security-relevant actions are recorded in the append-only
`audit_events` table. At minimum, ticket creation, assignment, and
status transitions are audited.

Audit logs must not contain passwords, bearer tokens, or other sensitive
secrets.

Database backups should be performed according to the deployment
environment's backup and recovery requirements.

## Scope limitations

This security policy applies to the AlertDesk internship/scaffold
environment.

AlertDesk is **not a SOAR (Security Orchestration, Automation and
Response) platform or a SIEM (Security Information and Event Management)
platform**.

The scaffold uses stub tokens for testing only and should not be used
for real security incidents or production security operations.

The following are outside the current scaffold scope:

- Slack integration
- SIEM connectors
- SSO
- Multi-region operation 