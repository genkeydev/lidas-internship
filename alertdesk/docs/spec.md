AlertDesk Specification

1. Purpose

AlertDesk is a web service that security analysts use to file and progress security alerts through a controlled ticket workflow.

2. API Resources

The main API resource is tickets. A ticket contains:

title

description

severity

Supported ticket operations include creating, listing, retrieving, and assigning tickets. Authorized roles may also change ticket status.

3. Severity

Severity values are client-defined. The current sample values are:

low

medium

high

critical

The implementation must read client-defined values from configuration rather than hardcoding them in Python.

4. Ticket Status Workflow

The current sample statuses are:

new -> triaged -> assigned -> resolved -> closed

Not every transition is legal. Legal transitions must come from config/client-spec.json. The application must reject transitions that are not defined as legal.

5. Roles and Permissions

Role

Create

List/Get

Assign

Change Status

Analyst

Yes

Yes

Yes

No

Lead

Yes

Yes

Yes

Yes

Admin

Yes

Yes

Yes

Yes

These permissions are client-defined and must remain configuration-driven.

6. Acceptance Criteria

An authorized analyst can create a ticket with a title, description and valid severity.

An authorized analyst can list tickets.

An authorized user can retrieve an individual ticket.

An authorized analyst can assign a ticket to an analyst identifier such as an email or handle.

Only authorized roles can change ticket status.

Illegal status transitions are rejected.

Creating, assigning and transitioning a ticket append audit records.

The running service exposes OpenAPI documentation.

7. Audit Requirements

The audit trail is append-only and records who performed important actions and when. At minimum, the following actions are audited:

ticket creation

ticket assignment

ticket status transition

8. Threat / Abuse Notes

Potential abuse cases include:

spoofed or invalid bearer tokens

attempting actions outside the authenticated user's permissions

attempting illegal ticket status transitions

exposing sensitive information through audit records

bypassing configuration-driven workflow rules through hardcoded values

9. Out of Scope for the Scaffold

Slack integration

SIEM connectors

SSO

multi-region operation

10. Configuration Rule

Statuses, roles, severity values and legal transitions must be read from the client specification/configuration. If the client changes the workflow, such as adding waiting-vendor, the configuration and tests should be updated rather than introducing hardcoded status enums in Python.
