# AlertDesk Specification

## 1. Purpose

AlertDesk is a web service that security analysts use to file and progress security alerts through a controlled ticket workflow.

## 2. API Resources

The main API resource is **tickets**.

A ticket contains:

- **title**
- **description**
- **severity**

Supported ticket operations include:

- Creating tickets
- Listing tickets
- Retrieving individual tickets
- Assigning tickets

Authorized roles may also change ticket status.

## 3. Severity

Severity values are client-defined.

The current sample values are:

- `low`
- `medium`
- `high`
- `critical`

The implementation must read client-defined values from configuration rather than hardcoding them in Python.

## 4. Ticket Status Workflow

The current sample workflow is:

```text
new → triaged → assigned → resolved → closed
```

The client specification is the source of truth for legal transitions. The
service must reject a transition that is not allowed by the configured
workflow; for example, a ticket cannot move directly from `new` to `resolved`.

## 5. Acceptance Criteria

- An authorized analyst can create a ticket with a title, description, and
  client-defined severity.
- An authorized analyst can list tickets and retrieve an individual ticket.
- An authorized analyst can assign a ticket to an analyst identifier.
- Analysts cannot change ticket status. Leads and admins can change status
  when the configured transition is legal.
- Illegal status transitions are rejected.
- Creating, assigning, and transitioning tickets creates append-only audit
  records that identify the actor and time.
- The client JSON specification controls supported statuses, roles, severities,
  and legal transitions without hardcoding them in Python.
- The running service exposes its API contract through OpenAPI.

## 6. Threat and Abuse Notes

- Require a valid bearer token and enforce role permissions on every protected
  operation. Reject unknown tokens and unauthorized status changes.
- Validate ticket input, reject malformed JSON, and accept only
  client-configured severities and legal workflow transitions.
- Record ticket creation, assignment, and status changes in an append-only
  audit trail so unauthorized or unexpected changes can be investigated.
- Treat the configured bearer tokens as development stubs, not production
  credentials. Do not expose them in logs, source control secrets, or public
  examples; replace the stub authentication before production use.
- Limit this scaffold to non-sensitive lab data. It does not provide SSO,
  per-user ticket isolation, or production-grade credential management.
