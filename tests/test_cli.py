
import argparse
import os
from unittest.mock import MagicMock, Mock, call, patch

import pytest

from lidas import cli
from lidas.rules import CONFIDENCE_THRESHOLD_DEFAULT


class TestBuildEngine:
    def test_default_confidence(self, monkeypatch):
        monkeypatch.delenv("LIDAS_MIN_CONFIDENCE", raising=False)
        with patch("lidas.cli.RuleEngine") as mock_engine_cls:
            cli._build_engine()
            mock_engine_cls.assert_called_once_with(
                min_confidence=CONFIDENCE_THRESHOLD_DEFAULT
            )

    def test_confidence_from_env(self, monkeypatch):
        monkeypatch.setenv("LIDAS_MIN_CONFIDENCE", "0.75")
        with patch("lidas.cli.RuleEngine") as mock_engine_cls:
            cli._build_engine()
            mock_engine_cls.assert_called_once_with(min_confidence=0.75)

    def test_invalid_confidence_falls_back_to_default(self, monkeypatch):
        monkeypatch.setenv("LIDAS_MIN_CONFIDENCE", "not-a-float")
        with patch("lidas.cli.RuleEngine") as mock_engine_cls:
            cli._build_engine()
            mock_engine_cls.assert_called_once_with(
                min_confidence=CONFIDENCE_THRESHOLD_DEFAULT
            )

class TestBuildEmitter:
    def test_creates_dirs_and_wires_emitters(self, tmp_path, monkeypatch):
        audit_path = tmp_path / "sub1" / "audit.log"
        key_path = tmp_path / "sub2" / "hmac.key"
        monkeypatch.setenv("LIDAS_AUDIT_LOG_PATH", str(audit_path))
        monkeypatch.setenv("LIDAS_KEY_PATH", str(key_path))

        fake_key = b"k" * 32
        with patch("lidas.cli.load_or_create_key", return_value=fake_key) as mock_load_key, \
             patch("lidas.cli.AuditLogWriter") as mock_writer_cls, \
             patch("lidas.cli.ConsoleEmitter") as mock_console_cls, \
             patch("lidas.cli.AuditLogEmitter") as mock_audit_emitter_cls, \
             patch("lidas.cli.MultiEmitter") as mock_multi_cls:

            mock_writer = mock_writer_cls.return_value
            emitter, writer = cli._build_emitter()

            assert audit_path.parent.is_dir()
            assert key_path.parent.is_dir()
            mock_load_key.assert_called_once_with(key_path)
            mock_writer_cls.assert_called_once_with(audit_path, fake_key)
            mock_audit_emitter_cls.assert_called_once_with(mock_writer)
            mock_multi_cls.assert_called_once_with(
                [mock_console_cls.return_value, mock_audit_emitter_cls.return_value]
            )
            assert writer is mock_writer
            assert emitter is mock_multi_cls.return_value

    def test_uses_default_paths_when_env_unset(self, monkeypatch, tmp_path):
        monkeypatch.delenv("LIDAS_AUDIT_LOG_PATH", raising=False)
        monkeypatch.delenv("LIDAS_KEY_PATH", raising=False)
        monkeypatch.chdir(tmp_path)

        with patch("lidas.cli.load_or_create_key", return_value=b"k" * 32), \
             patch("lidas.cli.AuditLogWriter"), \
             patch("lidas.cli.ConsoleEmitter"), \
             patch("lidas.cli.AuditLogEmitter"), \
             patch("lidas.cli.MultiEmitter"):
            cli._build_emitter()
            assert (tmp_path / "data").is_dir()


class TestCmdScan:
    def test_processes_all_lines_and_emits_alerts(self, tmp_path, capsys):
        log_file = tmp_path / "input.log"
        log_file.write_text("line1\nline2\nline3\n")

        mock_engine = Mock()
        mock_emitter = Mock()
        alert_a, alert_b = Mock(), Mock()
        mock_engine.process_event.side_effect = [[alert_a], [], [alert_b]]

        with patch("lidas.cli._build_engine", return_value=mock_engine), \
             patch("lidas.cli._build_emitter", return_value=(mock_emitter, Mock())), \
             patch("lidas.cli.parse_line", side_effect=[Mock(), Mock(), Mock()]):
            result = cli.cmd_scan(argparse.Namespace(logfile=str(log_file)))

        assert result == 0
        assert mock_engine.process_event.call_count == 3
        mock_emitter.emit.assert_has_calls([call(alert_a), call(alert_b)])
        assert mock_emitter.emit.call_count == 2
        assert "Processed 3 lines, raised 2 alerts." in capsys.readouterr().err

    def test_no_alerts_raised(self, tmp_path, capsys):
        log_file = tmp_path / "input.log"
        log_file.write_text("clean line\n")

        mock_engine = Mock()
        mock_engine.process_event.return_value = []
        mock_emitter = Mock()

        with patch("lidas.cli._build_engine", return_value=mock_engine), \
             patch("lidas.cli._build_emitter", return_value=(mock_emitter, Mock())), \
             patch("lidas.cli.parse_line", return_value=Mock()):
            result = cli.cmd_scan(argparse.Namespace(logfile=str(log_file)))

        assert result == 0
        mock_emitter.emit.assert_not_called()
        assert "raised 0 alerts" in capsys.readouterr().err

    def test_handles_undecodable_bytes(self, tmp_path):
        log_file = tmp_path / "binary.log"
        log_file.write_bytes(b"good line\n\xff\xfe bad bytes\n")

        mock_engine = Mock()
        mock_engine.process_event.return_value = []
        mock_emitter = Mock()

        with patch("lidas.cli._build_engine", return_value=mock_engine), \
             patch("lidas.cli._build_emitter", return_value=(mock_emitter, Mock())), \
             patch("lidas.cli.parse_line", return_value=Mock()):
            result = cli.cmd_scan(argparse.Namespace(logfile=str(log_file)))

        assert result == 0


class TestCmdTail:
    def test_sleeps_when_no_new_data(self):
        fake_file = MagicMock()
        fake_file.__enter__.return_value = fake_file
        fake_file.__exit__.return_value = False
        fake_file.readline.side_effect = ["", "", KeyboardInterrupt]

        fake_path = Mock()
        fake_path.open.return_value = fake_file

        with patch("lidas.cli.Path", return_value=fake_path), \
             patch("lidas.cli._build_engine", return_value=Mock()), \
             patch("lidas.cli._build_emitter", return_value=(Mock(), Mock())), \
             patch("lidas.cli.time.sleep", return_value=None) as mock_sleep:
            result = cli.cmd_tail(argparse.Namespace(logfile="whatever.log"))

        assert result == 0
        assert mock_sleep.call_count == 2
        mock_sleep.assert_called_with(0.5)


class TestCmdVerify:
    def test_ok_when_chain_intact(self, tmp_path, capsys, monkeypatch):
        key_path = tmp_path / "hmac.key"
        monkeypatch.setenv("LIDAS_KEY_PATH", str(key_path))
        fake_key = b"k" * 32

        with patch("lidas.cli.load_or_create_key", return_value=fake_key) as mock_load_key, \
             patch("lidas.cli.AuditLogVerifier") as mock_verifier_cls:
            mock_verifier_cls.return_value.verify.return_value = (True, None)
            result = cli.cmd_verify(argparse.Namespace(auditlog="audit.log"))

        assert result == 0
        mock_load_key.assert_called_once_with(key_path)
        mock_verifier_cls.assert_called_once_with(fake_key)
        mock_verifier_cls.return_value.verify.assert_called_once_with("audit.log")
        assert "OK: audit log chain is intact" in capsys.readouterr().out

    def test_tamper_detected(self, tmp_path, capsys, monkeypatch):
        monkeypatch.setenv("LIDAS_KEY_PATH", str(tmp_path / "hmac.key"))

        with patch("lidas.cli.load_or_create_key", return_value=b"k" * 32), \
             patch("lidas.cli.AuditLogVerifier") as mock_verifier_cls:
            mock_verifier_cls.return_value.verify.return_value = (False, 3)
            result = cli.cmd_verify(argparse.Namespace(auditlog="audit.log"))

        assert result == 1
        assert "TAMPER DETECTED: chain broken at line 3" in capsys.readouterr().err


class TestMain:
    def test_dispatches_to_scan(self):
        with patch("lidas.cli.cmd_scan", return_value=0) as mock_cmd:
            result = cli.main(["scan", "file.log"])
        assert result == 0
        called_args = mock_cmd.call_args.args[0]
        assert called_args.logfile == "file.log"
        assert called_args.command == "scan"

    def test_dispatches_to_tail(self):
        with patch("lidas.cli.cmd_tail", return_value=0) as mock_cmd:
            result = cli.main(["tail", "file.log"])
        assert result == 0
        mock_cmd.assert_called_once()

    def test_dispatches_to_verify(self):
        with patch("lidas.cli.cmd_verify", return_value=1) as mock_cmd:
            result = cli.main(["verify", "audit.log"])
        assert result == 1
        mock_cmd.assert_called_once()

    def test_missing_command_exits(self):
        with pytest.raises(SystemExit):
            cli.main([])

    def test_unknown_command_exits(self):
        with pytest.raises(SystemExit):
            cli.main(["bogus"])