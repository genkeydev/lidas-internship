# HealthLogger — Architecture

**Week 6**

**Project:** HealthLogger
**Client:** Harbor Logistics
**Version:** 1.0.0

---

## 1. Purpose

HealthLogger is a local health and event logging tool designed for use on developer laptops and small lab environments.

The application provides:

* A command-line interface (CLI).
* A small HTTP API.
* Local JSON Lines (JSONL) event storage.
* Validation based on a client-defined JSON specification.
* Separate storage for rejected HTTP submissions.
* Structured JSON logs written to standard output.

HealthLogger does not use a remote database in version 1.

The architecture is intentionally small so that it can run locally without requiring a central observability platform.

---

## 2. Architecture Overview

The system follows a simple processing pipeline:

```text
                    Client / User
                         |
              +----------+----------+
              |                     |
             CLI                   HTTP
              |                     |
              v                     v
     HealthLoggerCli        HealthHttpServer
              |                     |
              +----------+----------+
                         |
                         v
                   Parse JSON
                         |
                         v
                   HealthEvent
                         |
                         v
                    Validate
                         |
              +----------+----------+
              |                     |
            Valid                Invalid
              |                     |
              v                     v
         JsonlStore          RejectedEventStore
              |                     |
              v                     v
      data/events.jsonl    data/rejected-events.jsonl
              |
              v
      StructuredLogger
              |
              v
            stdout
```

The active client requirements are loaded from:

```text
config/client-spec.json
```

This allows the validation rules to change without requiring a new Java field for every client-defined event field.

---

## 3. Main Components

### 3.1 HealthLoggerCli

`HealthLoggerCli` is the command-line entry point.

It supports:

* `record`
* `query`
* `serve`

The CLI loads the client specification, creates the event store, and starts the appropriate operation.

For the `serve` command, it creates the HTTP server and keeps the process running.

---

### 3.2 HealthHttpServer

`HealthHttpServer` provides the local HTTP API.

The server exposes:

```text
GET  /health
POST /events
```

The server listens on localhost using the port defined by the client specification.

The current default port is:

```text
8088
```

`GET /health` is a process-liveness endpoint. It does not provide a complete service monitoring dashboard.

`POST /events` accepts a JSON event, parses it, validates it, and either stores or rejects it.

---

### 3.3 HealthEvent

`HealthEvent` represents an event as an open JSON object:

```java
Map<String, Object>
```

It intentionally does not define fixed Java fields such as:

```text
service
status
timestamp
```

as individual Java properties.

This design allows the client to introduce additional fields without requiring a Java model change.

The current implementation provides helper methods for commonly used fields such as:

* `service`
* `status`

All other event fields remain available through the underlying map.

---

### 3.4 ClientSpec

`ClientSpec` represents the client-defined configuration loaded from:

```text
config/client-spec.json
```

The specification currently controls:

* schema version
* client name
* required fields
* allowed statuses
* status-to-severity mappings
* HTTP port

Example:

```json
{
  "requiredFields": [
    "service",
    "status",
    "timestamp"
  ],
  "allowedStatuses": [
    "ok",
    "degraded",
    "down"
  ]
}
```

The application therefore keeps client-specific validation rules outside the Java event model.

---

### 3.5 Json

The `Json` class provides JSON-related operations.

It is responsible for:

* Loading the client specification.
* Parsing incoming event JSON.
* Serializing Java objects to JSON.
* Validating events against the active `ClientSpec`.

Validation checks include:

* Missing required fields.
* Null required fields.
* Unsupported status values.

---

### 3.6 JsonlStore

`JsonlStore` provides persistent local storage for valid health events.

The default event store is:

```text
data/events.jsonl
```

Each event is stored as exactly one JSON object per line.

The store uses append-only writes for new events.

The CLI query operation can read the stored events and filter them by service.

---

### 3.7 RejectedEventStore

`RejectedEventStore` stores rejected HTTP submissions separately from valid events.

The current file is:

```text
data/rejected-events.jsonl
```

A rejected entry records information such as:

* rejection timestamp
* original input
* validation or parsing reason

This keeps invalid submissions separate from valid health events while preserving information useful for troubleshooting.

---

### 3.8 StructuredLogger

`StructuredLogger` writes structured event information to standard output as JSON Lines.

A valid event log contains:

```text
ts
severity
event
```

The severity is obtained from the status-to-severity mapping in the client specification.

For the current client:

```text
ok       -> info
degraded -> warn
down     -> error
```

The logs are written to stdout so they can potentially be collected by a future centralized logging system.

---

## 4. CLI Data Flow

### 4.1 `record`

The CLI record flow is:

```text
healthlogger record
        |
        v
Read JSON input
        |
        v
Parse JSON
        |
        v
Create HealthEvent
        |
        v
Validate against ClientSpec
        |
     +--+--+
     |     |
   valid invalid
     |     |
     v     v
 JsonlStore
     |
     v
StructuredLogger
     |
     v
   stdout
```

A valid event is appended to:

```text
data/events.jsonl
```

Invalid CLI events are rejected and are not written to the valid event store.

---

### 4.2 `query`

The query flow is:

```text
healthlogger query
        |
        v
JsonlStore
        |
        v
Read JSONL events
        |
        v
Filter by service
        |
        v
Print matching events
```

The query operation does not modify the event store.

---

### 4.3 `serve`

The serve flow is:

```text
healthlogger serve
        |
        v
Load ClientSpec
        |
        v
Create JsonlStore
        |
        v
Create RejectedEventStore
        |
        v
Start HealthHttpServer
        |
        v
Listen on localhost
```

The HTTP server then waits for incoming requests.

---

## 5. HTTP Data Flow

### 5.1 Valid `POST /events`

```text
POST /events
     |
     v
Read request body
     |
     v
Check request size
     |
     v
Parse JSON
     |
     v
Validate event
     |
     v
JsonlStore
     |
     v
events.jsonl
     |
     v
StructuredLogger
     |
     v
HTTP 201 Created
```

A valid event is stored and logged.

---

### 5.2 Invalid or Malformed `POST /events`

```text
POST /events
     |
     v
Read request body
     |
     v
Parse
```
