"""Starter tests for lidas/parser.py (Week 1 scaffold).

Week 3 tasks: extend these with fuzz cases (null bytes, 1 MB lines, mixed
unicode, empty/whitespace) and add tests/test_rules.py and
tests/test_audit_log.py. See LIDAS_Intern_Guide for the full checklist.
"""

from lidas.parser import parse_line
from datetime import datetime, timezone


def test_parses_valid_ssh_failed_login():
    line = (
        "Jun 30 09:00:02 webhost sshd[1234]: Failed password for invalid "
        "user admin from 10.0.0.5 port 51514 ssh2"
    )
    event = parse_line(line)
    assert event.source == "ssh"
    assert event.status == "failed"
    assert event.source_ip == "10.0.0.5"
    assert event.user == "admin"


def test_parses_valid_ssh_accepted_login():
    line = (
        "Jun 30 09:00:01 webhost sshd[1233]: Accepted password for samuel "
        "from 192.168.1.10 port 51000 ssh2"
    )
    event = parse_line(line)
    assert event.source == "ssh"
    assert event.status == "accepted"
    assert event.user == "samuel"


def test_parses_valid_http_line_with_user_agent():
    line = (
        '203.0.113.7 - - [30/Jun/2026:09:01:00 +0000] '
        '"GET /login?user=admin HTTP/1.1" 401 128 "-" "sqlmap/1.6.12"'
    )
    event = parse_line(line)
    assert event.source == "http"
    assert event.source_ip == "203.0.113.7"
    assert event.status == "401"
    assert "user=admin" in (event.path or "")
    assert event.user_agent == "sqlmap/1.6.12"


def test_parses_http_line_without_user_agent():
    line = (
        '10.0.0.20 - - [30/Jun/2026:09:00:01 +0000] '
        '"GET /api/v1/pets HTTP/1.1" 200 512'
    )
    event = parse_line(line)
    assert event.source == "http"
    assert event.status == "200"
    assert event.user_agent is None


def test_unrecognized_line_returns_unknown_not_exception():
    event = parse_line("This is not a valid log line at all")
    assert event.source == "unknown"

def test_fuzz_1mb_line():
    line = "A" * 1_000_000
    event = parse_line(line)
    assert event.source == "unknown"

def test_fuzz_null_bytes():
    line = "\x00" * 500
    event = parse_line(line)
    assert event.source == "unknown"

def test_fuzz_mixed_unicode():
    line = "".join(chr(i) for i in range(0x110000) if 0x0 < i < 0x110000)  # all Unicode categories
    event = parse_line(line)
    assert event.source == "unknown"

def test_fuzz_empty():
    event = parse_line("")
    assert event.source == "unknown"

def test_fuzz_whitespace_only():
    event = parse_line("   \t\n\r   ")
    assert event.source == "unknown"

def test_fuzz_newlines_only():
    event = parse_line("\n\n\n\n")
    assert event.source == "unknown"

def test_timestamp_without_timezone_is_assumed_utc():
    """
    If the parsed timestamp lacks a timezone, it is replaced with UTC.
    For SSH logs, the format is e.g. "Jun 30 09:00:02" (no timezone).
    """
    line = (
        "Jun 30 09:00:02 webhost sshd[1234]: Failed password for invalid "
        "user admin from 10.0.0.5 port 51514 ssh2"
    )
    event = parse_line(line)
    # The timestamp should be timezone-aware with UTC
    assert event.timestamp.tzinfo == timezone.utc
    # Check the actual value: year is defaulted (we can't hardcode year),
    # but we can check hour/minute/second.
    assert event.timestamp.hour == 9
    assert event.timestamp.minute == 0
    assert event.timestamp.second == 2


def test_timestamp_with_timezone_keeps_its_timezone():
    """
    If the parsed timestamp already has a timezone (e.g., HTTP logs with +0000),
    it should keep that timezone, not be overridden.
    """
    line = (
        '203.0.113.7 - - [30/Jun/2026:09:01:00 +0000] '
        '"GET /login?user=admin HTTP/1.1" 401 128 "-" "sqlmap/1.6.12"'
    )
    event = parse_line(line)
    # The HTTP parser uses datetime.strptime with '%d/%b/%Y:%H:%M:%S %z',
    # which yields a timezone-aware datetime.
    assert event.timestamp.tzinfo is not None
    # It should be UTC (since +0000 is UTC)
    assert event.timestamp.tzinfo == timezone.utc
    # Check the value
    assert event.timestamp.year == 2026
    assert event.timestamp.month == 6
    assert event.timestamp.day == 30
    assert event.timestamp.hour == 9
    assert event.timestamp.minute == 1
    assert event.timestamp.second == 0
    
def test_timestamp_parsing_error_falls_back_to_current_utc():
    """
    If the timestamp cannot be parsed (ValueError), fallback to datetime.now(timezone.utc).
    This is a safety net to prevent crashes on malformed lines.
    """
    # Create a line that is otherwise valid but with an invalid date format
    line = (
        "InvalidDate 99:99:99 webhost sshd[1234]: Failed password for invalid "
        "user admin from 10.0.0.5 port 51514 ssh2"
    )
    event = parse_line(line)
    # The fallback sets timestamp to current UTC time.
    # We cannot assert an exact value, but we can check it's timezone-aware UTC
    # and that it's close to the current time (within a few seconds).
    assert event.timestamp.tzinfo == timezone.utc
    # Also check that it's not the default epoch (1970) – likely current time.
    now = datetime.now(timezone.utc)
    diff = now - event.timestamp
    # Allow a few seconds difference (since test execution is fast)
    assert abs(diff.total_seconds()) < 10