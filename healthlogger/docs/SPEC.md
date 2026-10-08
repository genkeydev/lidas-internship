# HealthLogger API — Specification

**GenKey Software Engineering Internship — Week 1**

**Project:** HealthLogger
**Client:** Harbor Logistics
**Version:** 1.0.0

---

## 1. Purpose

HealthLogger is a local health and event logging tool designed to record service health events on a user's laptop or lab environment.

The system provides a command-line interface (CLI) for recording and querying events and a small HTTP interface for recording events and checking process liveness.

Health events are stored locally as JSON Lines (JSONL), with one JSON object per line. The system does not use a remote database in version 1.

The logger must be configurable so that client-defined required fields and allowed status values can be changed through a JSON specification without requiring changes to the Java event model.

---

## 2. Scope

### 2.1 In Scope

The following functionality is included in version 1:

* Recording health events locally.
* Storing events as JSONL.
* Validating required fields.
* Validating allowed status values.
* Mapping event statuses to log severities.
* Querying events by service.
* Providing a CLI with:

  * `record`
  * `query`
  * `serve`
* Providing a local HTTP API with:

  * `POST /events`
  * `GET /health`
* Writing structured logs to stdout as JSON Lines.
* Loading client requirements from a JSON specification file.

### 2.2 Out of Scope

The following are not included in version 1:

* Authentication.
* TLS.
* Remote databases.
* Multi-node deployment.
* Prometheus exporters.
* Browser or web user interfaces.
* Full monitoring dashboards.
* Centralized observability infrastructure.

Authentication or other excluded features may be added later if a future client brief requires them.

---

## 3. System Requirements

### 3.1 Event Format

A health event shall be represented as a JSON object.

Each accepted event shall be stored as exactly one JSON object per line in the configured JSONL event store.

The current client specification requires the following fields:

* `service`
* `status`
* `timestamp`

The currently allowed status values are:

* `ok`
* `degraded`
* `down`

### 3.2 Validation

Before an event is stored, the system shall validate it against the active client specification.

The system shall:

1. Reject an event when a required field is missing.
2. Reject an event when a required field is present but has a null value.
3. Reject an event when its status is not one of the allowed status values.
4. Accept valid events that satisfy the active specification.
5. Preserve additional fields supplied in an event rather than requiring a Java field or class for each new field.

### 3.3 Status Severity Mapping

The active client specification defines the following severity mapping:

| Status     | Severity |
| ---------- | -------- |
| `ok`       | `info`   |
| `degraded` | `warn`   |
| `down`     | `error`  |

The severity is used when structured event information is written to stdout.

---

## 4. CLI Requirements

HealthLogger shall provide three primary CLI commands.

### 4.1 `record`

The `record` command shall accept a health event in JSON form and validate it against the active client specification.

#### Acceptance Criteria

The command is considered successful when:

* A valid JSON event is provided.
* All required fields are present and non-null.
* The status value is allowed by the active specification.
* The event is appended to the configured JSONL store.
* The event is written as one JSON object on one line.
* A structured JSON log is written to stdout.

The command shall reject invalid events and shall not store them.

---

### 4.2 `query`

The `query` command shall retrieve previously stored events.

The initial client requirement is to filter events by `service`.

#### Acceptance Criteria

The command is considered successful when:

* A service value is provided.
* Previously stored events matching that service are returned.
* Events belonging to other services are not returned.
* If no matching events exist, the command returns an empty result rather than creating an error condition.

---

### 4.3 `serve`

The `serve` command shall start the local HTTP interface.

The server shall listen on localhost using the configured HTTP port.

#### Acceptance Criteria

The command is considered successful when:

* The server starts using the configured port.
* The server is bound to localhost.
* `POST /events` is available for recording events.
* `GET /health` is available for checking process liveness.

---

## 5. HTTP API Requirements

### 5.1 `POST /events`

The endpoint shall accept a JSON health event.

The event shall be parsed and validated using the active client specification.

#### Successful Request

For a valid event:

1. The request body is parsed.
2. The event is validated.
3. The event is stored in the JSONL event store.
4. A structured log is written to stdout.
5. The server returns HTTP `201 Created`.

#### Invalid Request

For an invalid event:

* The event shall not be stored.
* The server shall return HTTP `400 Bad Request`.
* The response shall contain information describing the validation issues.

---

### 5.2 `GET /health`

The endpoint shall provide process liveness information only.

For a valid `GET` request:

* The server shall return HTTP `200`.
* The response shall indicate that the process is running.

This endpoint shall not act as a complete service health dashboard.

---

## 6. Local Storage Requirements

HealthLogger shall use a local JSONL file as its event store.

The default runtime store is:

`data/events.jsonl`

Events shall be appended to the store rather than replacing existing events.

Runtime data files shall not be committed to version control.

No remote database is required for version 1.

---

## 7. Structured Logging Requirements

HealthLogger shall write structured logs to stdout as JSON Lines.

Each logged event shall include:

* A timestamp generated by the logger.
* The appropriate severity based on the configured status mapping.
* The event data.

The structured logging format should allow the logs to be shipped to a centralized observability system in the future.

---

## 8. Client Specification and Extensibility

The client requirements shall be defined through the JSON specification file rather than hardcoded into Java event fields.

The current specification defines:

* Required field names.
* Allowed status values.
* Status-to-severity mappings.
* HTTP port configuration.

### Adding a New Required Field

If the client later requires a field such as `region`, the client specification JSON shall be updated to include the new required field.

For example:

```json
{
  "requiredFields": [
    "service",
    "status",
    "timestamp",
    "region"
  ]
}
```

The Java `HealthEvent` model shall not need a new Java field or a new Java class for `region`.

The event remains an open JSON object, allowing the logger to accept and store additional fields defined by the client specification.

Therefore, the process is:

**Client requirement → Updated specification JSON → Existing Java validation/storage logic**

rather than:

**Client requirement → New Java field/class → Code change**

If the client brief itself is replaced by the mentors, this specification shall be updated to reflect the current brief and obsolete client-specific requirements shall not be retained.

---

## 9. Error Handling

The system shall handle invalid input without storing invalid events.

Expected error conditions include:

* Missing required fields.
* Null required fields.
* Unsupported status values.
* Malformed JSON.
* Invalid CLI usage.
* Unsupported CLI commands.
* Invalid HTTP methods for available endpoints.

Errors shall produce an appropriate response or exit status while preventing invalid events from being written to the event store.

---

## 10. Acceptance Summary

The HealthLogger version 1 implementation shall satisfy the following high-level acceptance criteria:

* A valid health event can be recorded through the CLI.
* A valid health event can be recorded through `POST /events`.
* Events are stored locally as JSONL.
* Invalid events are rejected before storage.
* Events can be queried by service through the CLI.
* `GET /health` confirms process liveness.
* Structured logs are emitted as JSON Lines.
* Client-defined required fields are controlled by the JSON specification.
* A new required field can be introduced by updating the specification JSON without creating a new Java event field or class.
* Runtime event data is not committed to version control.
* Version 1 does not require authentication, TLS, a remote database, multi-node support, Prometheus exporters, or a browser UI.

---

## 11. Source of Requirements

This specification is derived from the current client brief:

`docs/client/BRIEF.md`

The active client configuration is defined in:

`config/client-spec.json`

If the client brief is replaced, this specification shall be reviewed and updated to match the new requirements.
