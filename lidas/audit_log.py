"""HMAC-chained append-only audit log.

Each entry stores the HMAC of the previous entry alongside its own HMAC.
This forms a chain: you cannot compute a valid HMAC for entry N without
knowing the valid HMAC of entry N-1. If any entry is modified, deleted, or
reordered, all subsequent HMACs are invalidated and verification fails.

Comparable ideas: certificate transparency logs and git commit trees (each
node binds the previous hash). Key limitation: if the HMAC key leaks, an
attacker can forge a new consistent chain — the key must be treated like a
credential.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Iterator

from .models import Alert

# The sentinel HMAC for the first entry's prev_hmac field.
# Using 64 zeros makes the chain origin explicit and auditable — a verifier
# knows the chain started from scratch when it sees this value.
GENESIS_HMAC = "0" * 64


def _alert_to_dict(alert: Alert) -> dict:
    """Convert Alert to a plain dict suitable for JSON serialisation.

    We convert before hashing because canonical JSON needs consistent types:
    datetime and Enum are not JSON-native; hashing mixed Python types would
    be non-reproducible across processes.
    """
    data = asdict(alert)
    data["timestamp"] = alert.timestamp.isoformat()
    data["severity"] = alert.severity.value
    return data


def _compute_hmac(key: bytes, prev_hmac: str, payload: dict) -> str:
    """HMAC-SHA256 over f"{prev_hmac}|{canonical_json}".

    prev_hmac is included IN the message (not just stored alongside). That
    is what makes this a chain rather than a collection of independent
    HMACs: changing entry N-1 changes prev_hmac for entry N, so entry N's
    digest no longer verifies even if its own payload is untouched.
    """
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    message = f"{prev_hmac}|{canonical}".encode("utf-8")
    return hmac.new(key, message, hashlib.sha256).hexdigest()


class AuditLogWriter:
    """Append one JSON line per alert.

    Append-only format means no seek-and-modify is needed or possible through
    this API. Each line is a complete JSON object with prev_hmac, alert, and
    entry_hmac.
    """

    def __init__(self, path: str | Path, key: bytes) -> None:
        self.path = Path(path)
        self.key = key
        self._prev_hmac = self._load_last_hmac()

    def _load_last_hmac(self) -> str:
        if not self.path.exists() or self.path.stat().st_size == 0:
            return GENESIS_HMAC
        try:
            last_line = ""
            with self.path.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        last_line = line
            if not last_line.strip():
                return GENESIS_HMAC
            entry = json.loads(last_line)
            return entry["entry_hmac"]
        except (json.JSONDecodeError, KeyError, OSError):
            # A verifier run will catch the corruption; we do not silently
            # fix it here
            return GENESIS_HMAC

    def write(self, alert: Alert) -> dict:
        alert_dict = _alert_to_dict(alert)
        entry_hmac = _compute_hmac(self.key, self._prev_hmac, alert_dict)
        entry = {
            "prev_hmac": self._prev_hmac,
            "alert": alert_dict,
            "entry_hmac": entry_hmac,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as f:
            # sort_keys=True so the stored JSON matches what the verifier
            # recomputes when it re-serialises the alert payload
            f.write(json.dumps(entry, sort_keys=True) + "\n")
        self._prev_hmac = entry_hmac
        return entry


class AuditLogVerifier:
    """Re-walk the file, recomputing each HMAC from scratch.

    Does not trust the stored entry_hmac — recomputes and compares. Uses
    hmac.compare_digest to prevent timing attacks.
    """

    def __init__(self, key: bytes) -> None:
        self.key = key

    def verify(self, path: str | Path) -> tuple[bool, int]:
        path = Path(path)
        if not path.exists() or path.stat().st_size == 0:
            return (True, -1)

        prev_hmac = GENESIS_HMAC
        with path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=0):
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    return (False, line_no)

                if entry.get("prev_hmac") != prev_hmac:
                    return (False, line_no)

                expected = _compute_hmac(self.key, prev_hmac, entry["alert"])
                # constant-time comparison prevents timing side-channel attacks
                if not hmac.compare_digest(expected, entry.get("entry_hmac", "")):
                    return (False, line_no)

                prev_hmac = entry["entry_hmac"]

        return (True, -1)

    def iter_entries(self, path: str | Path) -> Iterator[dict]:
        """Yield each parsed JSON entry. Does not verify — inspection only."""
        path = Path(path)
        if not path.exists():
            return
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield json.loads(line)


def load_or_create_key(key_path: str | Path) -> bytes:
    """Load an existing HMAC key or create a new 32-byte secret.

    - os.urandom: cryptographically secure RNG (not random.random).
    - 0o600: owner read/write only — no group or other access.
    - Key limitation: this is a symmetric key; if compromised, an attacker
      can forge a consistent-looking chain. Treat like a password.
    - The key must never be committed to version control (see .gitignore).
    """
    key_path = Path(key_path)
    if key_path.exists():
        return key_path.read_bytes()

    key_path.parent.mkdir(parents=True, exist_ok=True)
    key = os.urandom(32)
    key_path.write_bytes(key)
    try:
        os.chmod(key_path, 0o600)
    except OSError:
        # Windows may not support POSIX mode bits the same way; best-effort
        pass
    return key