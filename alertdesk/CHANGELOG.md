# Changelog

All notable changes to AlertDesk are documented here. This project follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and version numbers
follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-07

First documented release of the internship capstone service.

### Added

- Client-configured ticket severities, statuses, transitions, roles, and stub
  bearer-token mappings.
- Ticket creation, listing, retrieval, assignment, and authorized status
  transitions backed by SQLite, with audit events for ticket changes.
- Authentication, workflow, and API tests, plus an OpenAPI document and OWASP
  security assessment.
- Request logging that records method, path, status, and duration without
  logging authorization headers, query strings, or request bodies.
- A repeatable create/list latency benchmark and local deployment guidance.
- This incident playbook and release notes.

### Security and deployment notes

- The configured bearer tokens are fixed lab values and are not suitable as
  production credentials.
- The service is an internship scaffold; production identity, per-user ticket
  access, HTTPS termination, log retention, and operational alerting require
  deployment-specific design.
- SQLite stores ticket and audit data locally. Back up the database before
  maintenance, and do not remove the Compose data volume when preserving data.
