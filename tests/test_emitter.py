import io
import sys
from unittest.mock import Mock, patch, call

import pytest

from lidas.emitter import ConsoleEmitter, AuditLogEmitter, MultiEmitter
from lidas.models import Alert, Severity
from lidas.audit_log import AuditLogWriter

from datetime import datetime, timezone

def _sample_alert() -> Alert:
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


class TestConsoleEmitter:
    def test_emit_with_color(self):
        """Coloured output uses ANSI codes and reset."""
        stream = io.StringIO()
        emitter = ConsoleEmitter(use_color=True, stream=stream)
        alert = _sample_alert()
        emitter.emit(alert)
        output = stream.getvalue()
        assert "\033[31m" in output  # red for HIGH
        assert "\033[0m" in output
        assert "[HIGH    ]" in output
        assert "SSH-001" in output
        assert "test alert" in output
        assert "confidence=0.90" in output

    def test_emit_without_color(self):
        """Without color, no ANSI codes appear."""
        stream = io.StringIO()
        emitter = ConsoleEmitter(use_color=False, stream=stream)
        alert = _sample_alert()
        emitter.emit(alert)
        output = stream.getvalue()
        assert "\033[" not in output
        assert "[HIGH    ]" in output
        assert "SSH-001" in output

    def test_emit_uses_default_stdout_if_no_stream(self):
        """If no stream is provided, sys.stdout is used."""
        emitter = ConsoleEmitter()
        assert emitter.stream is sys.stdout

    def test_emit_handles_print_failure(self, monkeypatch):
        """If print fails (e.g., broken pipe), the exception is caught."""
        stream = Mock()
        stream.write = Mock(side_effect=OSError("Broken pipe"))
        stream.flush = Mock(side_effect=OSError("Broken pipe"))

        emitter = ConsoleEmitter(use_color=False, stream=stream)
        with patch("builtins.print", side_effect=OSError("Broken pipe")):
            emitter.emit(_sample_alert())  # Should not raise

    def test_emit_handles_any_exception(self):
        """General exception in print is caught."""
        stream = io.StringIO()
        emitter = ConsoleEmitter(use_color=False, stream=stream)
        alert = _sample_alert()
        with patch("builtins.print", side_effect=Exception("any error")):
            emitter.emit(alert)  # Should not raise


class TestAuditLogEmitter:
    def test_emit_writes_alert_to_audit_log(self, tmp_path):
        """AuditLogEmitter calls writer.write(alert)."""
        log_file = tmp_path / "audit.log"
        key = b"test-key-32-bytes-exactly-padded!"
        writer = AuditLogWriter(log_file, key)
        emitter = AuditLogEmitter(writer)

        alert = _sample_alert()
        emitter.emit(alert)

        lines = log_file.read_text().splitlines()
        assert len(lines) == 1
        import json
        entry = json.loads(lines[0])
        assert entry["alert"]["rule_id"] == "SSH-001"

    def test_emit_handles_write_exception(self):
        """If writer.write raises, the exception is caught."""
        mock_writer = Mock()
        mock_writer.write = Mock(side_effect=OSError("Disk full"))
        emitter = AuditLogEmitter(mock_writer)
        emitter.emit(_sample_alert())  # Should not raise
        mock_writer.write.assert_called_once()


class TestMultiEmitter:
    def test_emit_fans_out_to_all_emitters(self):
        """MultiEmitter calls each emitter's emit."""
        mock1 = Mock(spec=ConsoleEmitter)
        mock2 = Mock(spec=AuditLogEmitter)
        multi = MultiEmitter([mock1, mock2])
        alert = _sample_alert()
        multi.emit(alert)
        mock1.emit.assert_called_once_with(alert)
        mock2.emit.assert_called_once_with(alert)

    