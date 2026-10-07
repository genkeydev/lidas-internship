# Week 5 performance baseline and observability

## Benchmark

`scripts/benchmark.py` measures end-to-end HTTP latency for ticket creation and
listing against a running AlertDesk instance. It performs five warm-up pairs by
default, then records 100 measured create/list pairs. Results report mean,
median, p95, minimum, and maximum latency in milliseconds as JSON. The script
uses Python's standard library and the analyst bearer token configured by the
sample client spec.

Start the service in one terminal with `python -m alertdesk.cli`, then run
`python scripts/benchmark.py` in another. Options include `--base-url`, `--token`,
`--iterations`, and `--warmup`. Benchmark records use unique synthetic titles
and are persisted by the target service; use a disposable database for repeatable
runs. Listing time naturally rises as the table grows because the endpoint returns
all tickets. Results depend on machine load, database size, and whether the API
is local, so compare runs only under similar conditions.

## Baseline

No latency target is specified in the client brief. Capture a baseline on the
intended development environment and append the command, date, database size,
iteration count, and emitted JSON summary here. Do not treat measurements from a
single developer machine as a production service-level objective.

## Request logging

The API emits one JSON log event per HTTP request with timestamp, method, URL
path, status code, and elapsed milliseconds. The logger intentionally excludes
headers, bearer tokens, query strings, request bodies, and ticket data. These
fields are enough to identify slow routes and error rates without copying alert
contents into general application logs. Logs go to stderr through Python's
standard logging handler and can be collected by the process supervisor or
container runtime.

## Operational notes

- The benchmark includes HTTP client, API, SQLite, and response serialization time.
- The list endpoint has no pagination, so its latency and response size grow with
  the number of stored tickets.
- The benchmark creates records and does not clean them up; point it at a
  disposable database when measuring repeatedly.
- This is a local development baseline, not a capacity or concurrency test.
