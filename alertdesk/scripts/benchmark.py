"""Measure AlertDesk create and list request latency against a running API.

Example: python scripts/benchmark.py --base-url http://127.0.0.1:8000 --iterations 100
The service must already be running. Each run creates uniquely named tickets.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import time
import urllib.error
import urllib.request
import uuid


def request(base_url: str, path: str, token: str, payload: dict | None = None) -> tuple[int, float]:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}{path}", data=data,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST" if data is not None else "GET",
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            response.read()
            status = response.status
    except urllib.error.HTTPError as exc:
        exc.read()
        status = exc.code
    elapsed_ms = (time.perf_counter() - started) * 1000
    if not 200 <= status < 300:
        raise RuntimeError(f"{req.method} {path} returned HTTP {status}")
    return status, elapsed_ms


def percentile(values: list[float], percentile_value: float) -> float:
    ordered = sorted(values)
    index = max(0, math.ceil(percentile_value * len(ordered)) - 1)
    return ordered[index]


def summarize(values: list[float]) -> dict[str, float]:
    return {
        "count": len(values),
        "mean_ms": round(statistics.mean(values), 3),
        "median_ms": round(statistics.median(values), 3),
        "p95_ms": round(percentile(values, 0.95), 3),
        "min_ms": round(min(values), 3),
        "max_ms": round(max(values), 3),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--token", default="analyst-token")
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--warmup", type=int, default=5)
    args = parser.parse_args()
    if args.iterations < 1 or args.warmup < 0:
        parser.error("--iterations must be positive and --warmup cannot be negative")

    create_times: list[float] = []
    list_times: list[float] = []
    for index in range(args.warmup + args.iterations):
        payload = {
            "title": f"benchmark-{uuid.uuid4().hex}",
            "description": "Synthetic benchmark record",
            "severity": "low",
        }
        _, create_ms = request(args.base_url, "/tickets", args.token, payload)
        _, list_ms = request(args.base_url, "/tickets", args.token)
        if index >= args.warmup:
            create_times.append(create_ms)
            list_times.append(list_ms)

    print(json.dumps({
        "base_url": args.base_url.rstrip("/"),
        "iterations": args.iterations,
        "warmup": args.warmup,
        "units": "ms",
        "create_ticket": summarize(create_times),
        "list_tickets": summarize(list_times),
    }, indent=2))


if __name__ == "__main__":
    main()
