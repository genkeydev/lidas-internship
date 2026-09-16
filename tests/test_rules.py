"""Week 3 deliverable: detection rule tests.

Write at least two tests per rule (positive + negative). Start from the
pattern in LIDAS_Intern_Guide Week 3, then cover every rule in rules.py.

TODO (Week 3):
- SSHBruteForceRule (SSH-001)
- SQLInjectionRule (HTTP-001)
- SuspiciousUserAgentRule (HTTP-002)
- CanaryTokenRule (CANARY-001)
- PortScanHintRule (HTTP-003)
- RuleEngine confidence threshold and error isolation
"""

from datetime import datetime, timedelta, timezone
from typing import List

import pytest

from lidas.models import Alert, Severity
from lidas.parser import LogEvent
from lidas.rules import (
    SSHBruteForceRule, 
    SQLInjectionRule, 
    SuspiciousUserAgentRule, 
    CanaryTokenRule, 
    PortScanHintRule,
    HTTP401CredentialStuffingRule,
    RuleEngine
    )


FIXED_TS = datetime(2026, 6, 30, 9, 0, 0, tzinfo=timezone.utc)


def _ssh_failed(ip: str, offset_secs: int = 0) -> LogEvent:
    return LogEvent(
        raw="...",
        timestamp=FIXED_TS + timedelta(seconds=offset_secs),
        source="ssh",
        source_ip=ip,
        status="failed",
        user="admin",
    )
    
def _ssh_accepted(ip: str, offset_secs: int = 0, user: str = "admin") -> LogEvent:
    return LogEvent(
        raw="...",
        timestamp=FIXED_TS + timedelta(seconds=offset_secs),
        source="ssh",
        source_ip=ip,
        status="accepted",
        user=user,
    )
    
def _http_event(
    ip: str,
    path: str,
    status: str,
    user_agent: str | None = None,
    offset_secs: int = 0,
) -> LogEvent:
    return LogEvent(
        raw="...",
        timestamp=FIXED_TS + timedelta(seconds=offset_secs),
        source="http",
        source_ip=ip,
        status=status,
        path=path,
        user_agent=user_agent,
    )


def _http_404(ip: str, path: str = "/notfound", offset_secs: int = 0) -> LogEvent:
    return _http_event(ip, path, "404", offset_secs=offset_secs)


def _http_200(ip: str, path: str = "/", offset_secs: int = 0) -> LogEvent:
    return _http_event(ip, path, "200", offset_secs=offset_secs)    



def test_ssh_brute_force_positive():
    rule = SSHBruteForceRule(threshold=5, window=timedelta(seconds=60))
    alerts = []
    for i in range(5):
        alerts.extend(rule.process(_ssh_failed("10.0.0.5", offset_secs=i * 2)))
    assert len(alerts) == 1
    assert alerts[0].rule_id == "SSH-001"
    assert alerts[0].confidence >= 0.5


def test_ssh_brute_force_negative():
    """Example negative test — extend with below-threshold and accepted-login cases."""
    rule = SSHBruteForceRule(threshold=5, window=timedelta(seconds=60))
    alerts = []
    for i in range(4):
        alerts.extend(rule.process(_ssh_failed("10.0.0.5", offset_secs=i * 2)))
    assert len(alerts) == 0
    
def test_ssh_brute_force_does_not_fire_after_accepted_login():
    """Successful login resets the window for that IP."""
    rule = SSHBruteForceRule(threshold=5, window=timedelta(seconds=60))
    # 4 failed attempts
    for i in range(4):
        rule.process(_ssh_failed("10.0.0.5", i * 2))
    # One accepted login (should not trigger)
    alerts = rule.process(_ssh_accepted("10.0.0.5", offset_secs=8))
    assert len(alerts) == 0
    alerts = rule.process(_ssh_failed("10.0.0.5", offset_secs=10))
    assert len(alerts) == 1
    pass

def test_ssh_brute_force_suppresses_duplicate_alerts_within_window():
    """Once an alert fires, additional failures within the window are suppressed."""
    rule = SSHBruteForceRule(threshold=5, window=timedelta(seconds=60))
    # Fire at 5th attempt
    for i in range(5):
        rule.process(_ssh_failed("10.0.0.5", i * 2))
    # Now send a 6th failure at t=12 (still within 60s)
    alerts = rule.process(_ssh_failed("10.0.0.5", offset_secs=12))
    assert len(alerts) == 0  # suppressed
    # After window expires (t=70), a new failure should fire again
    alerts = rule.process(_ssh_failed("10.0.0.5", offset_secs=70))
    pass 

def test_sql_injection_positive():
    """Test SQL injection detection."""
    rule = SQLInjectionRule()
    event = _http_event("10.0.0.1", "/search?q='; DROP TABLE users; --", "200")
    alerts = rule.process(event)
    assert len(alerts) == 1
    assert alerts[0].rule_id == "HTTP-001"
    assert alerts[0].confidence >= 0.5
    
def test_sql_injection_does_not_fire_on_clean_path():
    rule = SQLInjectionRule()
    event = _http_event("10.0.0.5", "/api/v1/pets", "200")
    alerts = rule.process(event)
    assert len(alerts) == 0
    
def test_sql_injection_detects_union_select():
    rule = SQLInjectionRule()
    event = _http_event("10.0.0.5", "/api?q=UNION SELECT password FROM users", "200")
    alerts = rule.process(event)
    assert len(alerts) == 1
    assert alerts[0].rule_id == "HTTP-001"
    assert alerts[0].confidence >= 0.5
    

def test_sql_injection_negative():
    """Test normal request passes SQL injection check."""
    rule = SQLInjectionRule()
    event = _http_200("10.0.0.1", "/search?q=harmless")
    alerts = rule.process(event)
    assert len(alerts) == 0
    
def test_sql_injection_does_not_fire_on_unrelated_http_event():
    rule = SQLInjectionRule()
    event = _ssh_failed("10.0.0.5")  
    alerts = rule.process(event)
    assert len(alerts) == 0


def test_suspicious_user_agent_positive():
    """Test suspicious user agent detection."""
    rule = SuspiciousUserAgentRule()
    event = _http_event("10.0.0.1", "/", "200", user_agent="sqlmap/1.0")
    alerts = rule.process(event)
    assert len(alerts) == 1
    assert alerts[0].rule_id == "HTTP-002"

def test_suspicious_user_agent_detects_sqlmap():
    rule = SuspiciousUserAgentRule()
    event = _http_event("10.0.0.5", "/", "200", user_agent="sqlmap/1.6")
    alerts = rule.process(event)
    assert len(alerts) == 1
    assert alerts[0].rule_id == "HTTP-002"
    assert alerts[0].confidence == 0.7


def test_suspicious_user_agent_detects_nikto():
    rule = SuspiciousUserAgentRule()
    event = _http_event("10.0.0.5", "/", "200", user_agent="Nikto/2.1.6")
    alerts = rule.process(event)
    assert len(alerts) == 1
    
def test_suspicious_user_agent_does_not_fire_on_normal_browser():
    rule = SuspiciousUserAgentRule()
    event = _http_event(
        "10.0.0.5",
        "/",
        "200",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    alerts = rule.process(event)
    assert len(alerts) == 0


def test_suspicious_user_agent_does_not_fire_on_non_http():
    rule = SuspiciousUserAgentRule()
    event = _ssh_failed("10.0.0.5")
    alerts = rule.process(event)
    assert len(alerts) == 0


def test_suspicious_user_agent_negative():
    """Test normal user agent passes check."""
    rule = SuspiciousUserAgentRule()
    event = _http_event("10.0.0.1", "/", "200", user_agent="Mozilla/5.0")
    alerts = rule.process(event)
    assert len(alerts) == 0


def test_canary_token_positive():
    """Test canary token detection."""
    rule = CanaryTokenRule()
    event = _http_event("10.0.0.1", "/admin/backup.zip", "200")
    alerts = rule.process(event)
    assert len(alerts) == 1
    assert alerts[0].rule_id == "CANARY-001"


def test_canary_token_negative():
    """Test normal path passes canary token check."""
    rule = CanaryTokenRule()
    event = _http_event("10.0.0.1", "/", "200")
    alerts = rule.process(event)
    assert len(alerts) == 0
    
def test_canary_user_does_not_fire_on_normal_user():
    rule = CanaryTokenRule(canary_users=["svc-monitoring-readonly"])
    event = _ssh_failed("10.0.0.5", offset_secs=0)
    alerts = rule.process(event)
    assert len(alerts) == 0

def test_canary_path_access_triggers_with_confidence_1():
    rule = CanaryTokenRule(canary_paths=["/admin/backup.zip"])
    event = _http_event("10.0.0.5", "/admin/backup.zip", "200")
    alerts = rule.process(event)
    assert len(alerts) == 1
    assert alerts[0].rule_id == "CANARY-001"
    assert alerts[0].confidence == 1.0


def test_canary_handles_both_http_and_ssh_in_same_event():
    """An event can't be both HTTP and SSH, but rule processes both sources."""
    rule = CanaryTokenRule(canary_paths=["/secret"], canary_users=["canary"])
    # HTTP canary
    event1 = _http_event("1.1.1.1", "/secret", "200")
    alerts = rule.process(event1)
    assert len(alerts) == 1
    # SSH canary
    event2 = _ssh_failed("2.2.2.2", offset_secs=0)
    alerts = rule.process(event2)
    assert len(alerts) == 0


def test_port_scan_hint_positive():
    """Test port scan hint detection."""
    rule = PortScanHintRule(threshold=5, window=timedelta(seconds=60))
    alerts = []
    for i in range(5):
        alerts.extend(rule.process(_http_404("10.0.0.1", offset_secs=i * 2)))
    assert len(alerts) == 1
    assert alerts[0].rule_id == "HTTP-003"


def test_port_scan_hint_negative():
    """Test below-threshold 404s pass port scan check."""
    rule = PortScanHintRule(threshold=5, window=timedelta(seconds=60))
    alerts = []
    for i in range(3):
        alerts.extend(rule.process(_http_404("10.0.0.1", offset_secs=i * 2)))
    assert len(alerts) == 0

def test_port_scan_hint_does_not_fire_on_200_responses():
    rule = PortScanHintRule(threshold=10, window=timedelta(seconds=30))
    alerts = []
    for i in range(10):
        alerts.extend(rule.process(_http_200("10.0.0.5", f"/page{i}", i * 2)))
    assert len(alerts) == 0
    
    
def test_ruleengine_filters_by_confidence_threshold():
    """Alerts with confidence below min_confidence are dropped."""
    # Create a rule that always returns a low-confidence alert
    class LowConfidenceRule(SSHBruteForceRule):
        def process(self, event):
            return [
                Alert(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    severity=self.severity,
                    timestamp=event.timestamp,
                    source_ip=event.source_ip,
                    confidence=0.3,
                    summary="low",
                    evidence=[],
                )
            ]

    engine = RuleEngine(rules=[LowConfidenceRule()], min_confidence=0.5)
    event = _ssh_failed("10.0.0.5")
    alerts = engine.process_event(event)
    assert len(alerts) == 0


def test_ruleengine_passes_high_confidence_alerts():
    """Alerts with confidence >= min_confidence are passed."""
    class HighConfidenceRule(SSHBruteForceRule):
        def process(self, event):
            return [
                Alert(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    severity=self.severity,
                    timestamp=event.timestamp,
                    source_ip=event.source_ip,
                    confidence=0.9,
                    summary="high",
                    evidence=[],
                )
            ]

    engine = RuleEngine(rules=[HighConfidenceRule()], min_confidence=0.5)
    event = _ssh_failed("10.0.0.5")
    alerts = engine.process_event(event)
    assert len(alerts) == 1


def test_ruleengine_isolates_rule_exceptions():
    """If one rule raises an exception, others still run."""
    class BrokenRule(SSHBruteForceRule):
        def process(self, event):
            raise RuntimeError("simulated bug")

    class GoodRule(SSHBruteForceRule):
        def process(self, event):
            return [
                Alert(
                    rule_id="GOOD",
                    rule_name="good",
                    severity=Severity.MEDIUM,
                    timestamp=event.timestamp,
                    source_ip=event.source_ip,
                    confidence=1.0,
                    summary="good",
                    evidence=[],
                )
            ]

    engine = RuleEngine(rules=[BrokenRule(), GoodRule()])
    event = _ssh_failed("10.0.0.5")
    alerts = engine.process_event(event)
    # Only GoodRule produces an alert
    assert len(alerts) == 1
    assert alerts[0].rule_id == "GOOD"


def test_ruleengine_state_persists_across_events():
    """Sliding window state should persist across process_event calls."""
    engine = RuleEngine(rules=[SSHBruteForceRule(threshold=5, window=timedelta(seconds=60))])
    # Send 4 failures individually
    for i in range(4):
        engine.process_event(_ssh_failed("10.0.0.5", i * 2))
    # Now 5th failure triggers
    alerts = engine.process_event(_ssh_failed("10.0.0.5", offset_secs=8))
    assert len(alerts) == 1
    assert alerts[0].rule_id == "SSH-001"
    
def _http_401(ip: str, offset_secs: int = 0, status: str = "401") -> LogEvent:
    """Helper to generate an HTTP 401 event."""
    return LogEvent(
        raw="dummy line",
        timestamp=FIXED_TS + timedelta(seconds=offset_secs),
        source="http",
        source_ip=ip,
        status=status,
        user=None,
        path="/login",
        user_agent="Mozilla/5.0",
    )

def test_http401_triggers_after_threshold():
    """10 401s from the same IP within 60s → alert."""
    rule = HTTP401CredentialStuffingRule(threshold=10, window=timedelta(seconds=60))
    ip = "10.0.0.5"
    # Send 10 events spaced by 5 seconds (total 45s, all within window)
    events = [_http_401(ip, offset_secs=i*5) for i in range(10)]
    alerts = []
    for e in events:
        alerts.extend(rule.process(e))
    assert len(alerts) == 1
    assert alerts[0].rule_id == "HTTP-004"
    assert alerts[0].source_ip == ip

def test_http401_does_not_fire_below_threshold():
    """9 401s from same IP → no alert."""
    rule = HTTP401CredentialStuffingRule(threshold=10, window=timedelta(seconds=60))
    ip = "10.0.0.5"
    events = [_http_401(ip, offset_secs=i*5) for i in range(9)]
    alerts = []
    for e in events:
        alerts.extend(rule.process(e))
    assert len(alerts) == 0

def test_http401_different_ips_count_separately():
    """401s from different IPs should not accumulate together."""
    rule = HTTP401CredentialStuffingRule(threshold=10, window=timedelta(seconds=60))
    # 5 from IP A, 5 from IP B → neither reaches threshold
    events = [_http_401("10.0.0.5", i*5) for i in range(5)]
    events += [_http_401("10.0.0.6", i*5) for i in range(5)]
    alerts = []
    for e in events:
        alerts.extend(rule.process(e))
    assert len(alerts) == 0

def test_http401_200_responses_ignored():
    """HTTP 200 responses should not be counted."""
    rule = HTTP401CredentialStuffingRule(threshold=10, window=timedelta(seconds=60))
    ip = "10.0.0.5"
    # Send 10 200 responses (status not 401)
    events = [_http_401(ip, i*5, status="200") for i in range(10)]
    alerts = []
    for e in events:
        alerts.extend(rule.process(e))
    assert len(alerts) == 0

def test_http401_cooldown_prevents_alert_spam():
    """After an alert, the same IP is suppressed for a window."""
    rule = HTTP401CredentialStuffingRule(threshold=5, window=timedelta(seconds=60))
    ip = "10.0.0.5"
    # Send 5 401s (alert triggers)
    events = [_http_401(ip, i*5) for i in range(5)]
    alerts = []
    for e in events:
        alerts.extend(rule.process(e))
    assert len(alerts) == 1

    # Send 5 more immediately (should be suppressed)
    events = [_http_401(ip, 30 + i*5) for i in range(5)]  # still within 60s window
    for e in events:
        alerts.extend(rule.process(e))
    assert len(alerts) == 1   # still only one alert

    # Send 5 more after cooldown expires (after +60s)
    events = [_http_401(ip, 120 + i*5) for i in range(5)]  # after cooldown
    for e in events:
        alerts.extend(rule.process(e))
    assert len(alerts) == 2   # second alert fires

def test_http401_eviction_removes_old_entries():
    """Entries older than the window are evicted."""
    rule = HTTP401CredentialStuffingRule(threshold=5, window=timedelta(seconds=60))
    ip = "10.0.0.5"
    # Send 5 events over 65 seconds (first one is older than 60s by the end)
    events = [
        _http_401(ip, 0),
        _http_401(ip, 10),
        _http_401(ip, 20),
        _http_401(ip, 30),
        _http_401(ip, 65),  # 65s after first, so first is evicted
    ]
    alerts = []
    for e in events:
        alerts.extend(rule.process(e))
    # Only 4 recent events (10,20,30,65) remain, threshold 5 not reached
    assert len(alerts) == 0