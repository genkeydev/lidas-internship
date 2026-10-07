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