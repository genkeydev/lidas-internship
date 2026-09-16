"""Week 3 deliverable: HMAC audit log chain tests.

Implement clean-chain verification and tamper detection. See the guide's
tests/test_audit_log.py examples (clean chain verifies, tampered entry
caught at the correct line).

TODO (Week 3):
- test_chain_verifies_clean_log
- test_chain_detects_tampered_entry
- test_first_entry_prev_hmac_is_genesis
- test_different_key_fails_verification
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest

from lidas.audit_log import AuditLogVerifier, AuditLogWriter, GENESIS_HMAC
from lidas.models import Alert, Severity
from lidas.audit_log import load_or_create_key

KEY = b"test-key-32-bytes-exactly-padded!"


def _alert():
    return Alert(
        rule_id="SSH-001",
        rule_name="SSH brute force",
        severity=Severity.HIGH,
        timestamp=datetime(2026, 6, 30, 9, 0, 0, tzinfo=timezone.utc),
        source_ip="10.0.0.5",
        confidence=0.9,
        summary="test alert",
        evidence=["raw line"],
    )


def test_get_last_hmac_returns_genesis_on_empty_file(tmp_path):
    """When the audit log is empty, _get_last_hmac returns GENESIS_HMAC."""
    log_file = tmp_path / "empty.log"
    log_file.touch()  # empty file

    writer = AuditLogWriter(log_file, KEY)
    # Access the private method (if it's not exposed, we can test indirectly,
    # but we'll assume it's a method we can call for testing)
    last_hmac = writer._load_last_hmac()
    # GENESIS_HMAC is likely bytes, we need to compare to its hex representation
    expected = GENESIS_HMAC.hex() if isinstance(GENESIS_HMAC, bytes) else GENESIS_HMAC
    assert last_hmac == expected


def test_get_last_hmac_returns_genesis_on_invalid_json(tmp_path):
    """If the last line is not valid JSON, return GENESIS_HMAC."""
    log_file = tmp_path / "corrupt.log"
    # Write a line that is not JSON
    log_file.write_text("This is not JSON\n")

    writer = AuditLogWriter(log_file, KEY)
    last_hmac = writer._load_last_hmac()
    expected = GENESIS_HMAC.hex() if isinstance(GENESIS_HMAC, bytes) else GENESIS_HMAC
    assert last_hmac == expected


def test_get_last_hmac_returns_genesis_on_missing_entry_hmac(tmp_path):
    """If the JSON object lacks the 'entry_hmac' key, return GENESIS_HMAC."""
    log_file = tmp_path / "missing_key.log"
    # Write a JSON line without the "entry_hmac" field
    entry = {"prev_hmac": "abc", "alert": {}}  # no "entry_hmac"
    log_file.write_text(json.dumps(entry) + "\n")

    writer = AuditLogWriter(log_file, KEY)
    last_hmac = writer._load_last_hmac()
    expected = GENESIS_HMAC.hex() if isinstance(GENESIS_HMAC, bytes) else GENESIS_HMAC
    assert last_hmac == expected


def test_get_last_hmac_returns_actual_hmac_on_valid_entry(tmp_path):
    """With a valid entry, return the actual entry_hmac."""
    log_file = tmp_path / "valid.log"
    writer = AuditLogWriter(log_file, KEY)
    # Write one alert; this populates the file
    writer.write(_alert())

    # Now read the last HMAC directly via the method
    last_hmac = writer._load_last_hmac()

    # Read the file to know the expected value
    lines = log_file.read_text().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    expected = entry["entry_hmac"]
    assert last_hmac == expected


def test_get_last_hmac_returns_genesis_on_oserror(tmp_path, monkeypatch):
    """If an OSError occurs (e.g., file can't be opened), return GENESIS_HMAC."""
    log_file = tmp_path / "unreadable.log"
    # Make the file unreadable by removing permissions (on Unix) or using a mock
    log_file.touch()
    log_file.chmod(0o000)  # no read permission

    writer = AuditLogWriter(log_file, KEY)
    last_hmac = writer._load_last_hmac()
    expected = GENESIS_HMAC.hex() if isinstance(GENESIS_HMAC, bytes) else GENESIS_HMAC
    assert last_hmac == expected

    # Restore permissions so the test cleanup doesn't fail
    log_file.chmod(0o644)

def test_chain_verifies_clean_log(tmp_path):
    log_file = tmp_path / "audit.log"
    writer = AuditLogWriter(log_file, KEY)
    writer.write(_alert())
    writer.write(_alert())

    verifier = AuditLogVerifier(KEY)
    valid, bad = verifier.verify(log_file)
    assert valid is True
    assert bad == -1


def test_chain_detects_tampered_entry(tmp_path):
    log_file = tmp_path / "audit.log"
    writer = AuditLogWriter(log_file, KEY)
    writer.write(_alert())
    writer.write(_alert())

    # Tamper with the first entry (line 0)
    lines = log_file.read_text().splitlines()
    entry = json.loads(lines[0])
    entry["alert"]["source_ip"] = "99.99.99.99"  # attacker changes the IP
    lines[0] = json.dumps(entry)
    log_file.write_text("\n".join(lines) + "\n")

    verifier = AuditLogVerifier(KEY)
    valid, bad = verifier.verify(log_file)
    assert valid is False
    assert bad == 0  # first entry is tampered (0-based)


def test_first_entry_prev_hmac_is_genesis(tmp_path):
    log_file = tmp_path / "audit.log"
    writer = AuditLogWriter(log_file, KEY)
    writer.write(_alert())

    lines = log_file.read_text().splitlines()
    assert len(lines) >= 1
    entry = json.loads(lines[0])
    assert "prev_hmac" in entry

    # The audit log stores the genesis HMAC as a hex string.
    # Compare to the hex representation of the GENESIS_HMAC constant.
    expected = GENESIS_HMAC.hex() if isinstance(GENESIS_HMAC, bytes) else GENESIS_HMAC
    assert entry["prev_hmac"] == expected


def test_different_key_fails_verification(tmp_path):
    log_file = tmp_path / "audit.log"
    writer = AuditLogWriter(log_file, KEY)
    writer.write(_alert())
    writer.write(_alert())

    wrong_key = b"wrong-key-32-bytes-long-here!!"
    verifier = AuditLogVerifier(wrong_key)
    valid, bad = verifier.verify(log_file)
    assert valid is False
    # The first entry's HMAC will not match, so bad should be 0 (first line)
    assert bad == 0
    
def test_verify_handles_corrupt_log_by_returning_genesis(tmp_path):
    log_file = tmp_path / "corrupt.log"
    log_file.write_text("Bad data\n")
    verifier = AuditLogVerifier(KEY)
    valid, bad = verifier.verify(log_file)
    # Since the log is corrupt, the chain cannot be validated; but we expect no crash.
    assert valid is False
    # Additionally, the first entry is corrupt, so bad should be 0 (line 0)
    assert bad == 0

def test_iter_entries_returns_nothing_for_nonexistent_file(tmp_path):
    """If the path doesn't exist, iter_entries yields nothing (no error)."""
    verifier = AuditLogVerifier(KEY)
    missing_file = tmp_path / "does_not_exist.log"
    entries = list(verifier.iter_entries(missing_file))
    assert entries == []


def test_iter_entries_yields_valid_json_lines(tmp_path):
    """Each non‑empty line that is valid JSON is yielded as a dict."""
    log_file = tmp_path / "valid.log"
    lines = [
        '{"prev_hmac": "a", "alert": {}, "entry_hmac": "b"}',
        '{"prev_hmac": "c", "alert": {}, "entry_hmac": "d"}',
    ]
    log_file.write_text("\n".join(lines) + "\n")

    verifier = AuditLogVerifier(KEY)
    entries = list(verifier.iter_entries(log_file))
    assert len(entries) == 2
    assert entries[0]["prev_hmac"] == "a"
    assert entries[1]["prev_hmac"] == "c"


def test_iter_entries_skips_empty_and_whitespace_lines(tmp_path):
    """Blank lines (empty, spaces, tabs) are ignored."""
    log_file = tmp_path / "with_blanks.log"
    lines = [
        '{"prev_hmac": "a"}',
        "",
        "   ",
        "\t\t",
        '{"prev_hmac": "b"}',
    ]
    log_file.write_text("\n".join(lines) + "\n")

    verifier = AuditLogVerifier(KEY)
    entries = list(verifier.iter_entries(log_file))
    assert len(entries) == 2
    assert entries[0]["prev_hmac"] == "a"
    assert entries[1]["prev_hmac"] == "b"


def test_iter_entries_raises_on_invalid_json(tmp_path):
    """If a non‑empty line is not valid JSON, json.loads raises JSONDecodeError."""
    log_file = tmp_path / "invalid.log"
    log_file.write_text('{"valid": true}\nThis is not JSON\n{"also": "valid"}')

    verifier = AuditLogVerifier(KEY)
    with pytest.raises(json.JSONDecodeError):
        list(verifier.iter_entries(log_file))


def test_iter_entries_handles_trailing_newline_only(tmp_path):
    """A file that ends with a newline but has no content yields nothing."""
    log_file = tmp_path / "empty_with_newline.log"
    log_file.write_text("\n")

    verifier = AuditLogVerifier(KEY)
    entries = list(verifier.iter_entries(log_file))
    assert entries == []


def test_iter_entries_yields_large_entries_without_issue(tmp_path):
    """A single large JSON entry can be parsed (no memory explosion)."""
    log_file = tmp_path / "large.log"
    big_entry = {
        "prev_hmac": "a" * 10000,
        "alert": {"summary": "x" * 50000},
        "entry_hmac": "b" * 10000,
    }
    line = json.dumps(big_entry)
    log_file.write_text(line + "\n")

    verifier = AuditLogVerifier(KEY)
    entries = list(verifier.iter_entries(log_file))
    assert len(entries) == 1
    assert entries[0]["prev_hmac"] == big_entry["prev_hmac"]
    assert entries[0]["alert"]["summary"] == big_entry["alert"]["summary"]
    
def test_load_or_create_key_loads_existing(tmp_path):
    """If the key file already exists, its bytes are returned unchanged."""
    key_path = tmp_path / "hmac.key"
    expected_key = b"existing-key-32-bytes-long!!!"
    key_path.write_bytes(expected_key)

    key = load_or_create_key(key_path)
    assert key == expected_key
    # Ensure file is not rewritten (modification time doesn't change)
    assert key_path.read_bytes() == expected_key