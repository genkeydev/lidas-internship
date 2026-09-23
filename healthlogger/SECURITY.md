# Security Policy

## Overview

HealthLogger is a local health and event logging application developed as part of the GenKey Software Engineering Internship.

This security policy describes how security issues should be reported, how runtime event data should be handled, the default network exposure of the application, and the security limitations of the current project.

The policy applies to the current HealthLogger implementation and may be updated when new security requirements are introduced.

## Reporting a Vulnerability

If a security vulnerability is discovered in HealthLogger, it should be reported privately to the project maintainer rather than being disclosed publicly first.

A vulnerability report should include:

* A clear description of the security issue.
* The affected component, file, or feature, if known.
* Steps required to reproduce the issue.
* The potential security impact.
* Any suggested mitigation or fix, if available.

Do not include real credentials, passwords, secrets, personal information, medical information, or other sensitive operational data in a vulnerability report.

Until the issue has been reviewed, security vulnerabilities should not be publicly disclosed through GitHub issues, pull requests, or other public project channels.

## Event Store

HealthLogger stores runtime events as JSON Lines (JSONL) files in the `data/` directory.

The default event store is:

`data/events.jsonl`

The event store location can also be configured using the `HEALTHLOGGER_STORE` environment variable.

Runtime event files may contain operational information about the application's services and health status. These files must therefore be treated as operational data and must not be committed to the Git repository.

The repository's `.gitignore` excludes runtime files under the `data/` directory while allowing the directory structure to remain available for the application.

When developing or testing HealthLogger:

* Use sample or synthetic data whenever possible.
* Do not use real patient medical information.
* Do not commit passwords, access tokens, API keys, credentials, or other secrets.
* Do not commit runtime event files containing sensitive operational information.
* Review files before committing them to Git.

If sensitive information is accidentally committed, it should be removed from the repository and any exposed credentials or secrets should be revoked or replaced where applicable.

## HTTP Bind Address

The HealthLogger HTTP server binds to the loopback address:

`127.0.0.1`

This means that the HTTP API is intended to be accessible only from the local machine by default.

The current implementation is therefore not intended to operate as a publicly exposed network service.

The current client requirements do not require authentication or TLS for the local application.

If a future client requirement requires HealthLogger to be accessible over a network, the security requirements must be reviewed before implementation. This may include controls such as:

* Authentication and authorization.
* HTTPS/TLS.
* Secure credential management.
* Input validation and request limits.
* Secure configuration.
* Protection against unauthorized access.

Any new security requirements should be documented in the project specification and reflected in the implementation and testing requirements.

## Scope and Limitations

HealthLogger is currently designed as a local health and event logging application.

It is not intended to be:

* A Security Information and Event Management (SIEM) platform.
* A multi-tenant Software-as-a-Service (SaaS) application.
* A centralized remote observability platform.
* A replacement for enterprise security monitoring.
* A publicly exposed production API by default.
* A complete enterprise health information system.

Security controls in the current project are therefore limited to the requirements of the local application and its current client brief.

The current implementation should not be assumed to provide the security controls required for a publicly deployed production healthcare system.

Future security requirements introduced by the client must be documented in the project specification before implementation.

## Secure Development Practices

Development of HealthLogger should follow basic secure software development practices.

These include:

* Validating user-provided input before processing or storing it.
* Avoiding hard-coded passwords, API keys, tokens, and other secrets.
* Keeping runtime and sensitive data outside version control.
* Using synthetic data during development and testing.
* Reviewing changes before committing them.
* Writing tests for security-relevant validation rules.
* Recording relevant security-related events through appropriate application logging.
* Keeping dependencies and development tools reasonably up to date.
* Documenting new security requirements when the application scope changes.

## Security and Testing

Security-related requirements should be verified through testing where applicable.

Testing should include:

* Invalid and unexpected input.
* Boundary values.
* Attempts to provide missing required information.
* Validation of data before storage.
* Verification that sensitive runtime files are not committed to Git.
* Verification that the HTTP server uses the intended loopback address.
* Verification that application configuration does not expose secrets.

Security tests should use synthetic or non-sensitive information.

## Changes to This Policy

This security policy should be updated when the HealthLogger architecture, deployment model, data handling requirements, or client security requirements change.

Significant security changes should be documented, tested, and reviewed before being incorporated into the project.

---

**Project:** HealthLogger API
**Security Policy:** Week 2 Security Work
**Development Context:** GenKey Software Engineering Internship
