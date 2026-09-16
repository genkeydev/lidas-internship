"""Detection rules for LIDAS.

Each rule is a self-contained class with a single process() method. This
design means each rule is independently unit-testable. Every rule must have
two test cases: positive (attack detected) and negative (legitimate traffic
not flagged).

CONFIDENCE_THRESHOLD_DEFAULT and the "threshold guard" concept: the engine
suppresses alerts whose confidence is below a configurable floor so operators
can tune noise globally without rewriting rules.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from datetime import datetime, timedelta

from .models import Alert, Severity
from .parser import LogEvent

# Alerts below this confidence level are suppressed at the engine level.
# Operators can tune this globally via LIDAS_MIN_CONFIDENCE without touching
# rule code.
CONFIDENCE_THRESHOLD_DEFAULT = 0.5


class Rule(ABC):
    """Base class for all detection rules.

    The ABC enforces the contract: every rule exposes id/name/severity and
    implements process(). Subclasses that forget process() fail at import
    time rather than silently doing nothing at runtime.
    """

    rule_id: str
    rule_name: str
    severity: Severity

    @abstractmethod
    def process(self, event: LogEvent) -> list[Alert]:
        """Consume one event, return zero or more alerts. Must never raise —
        exceptions propagate to the engine which catches them per-rule.
        """


class SSHBruteForceRule(Rule):
    """Detect rapid failed SSH logins from one IP (sliding window).

    We keep a deque of failure timestamps per IP. deque.popleft() is O(1),
    so evicting expired entries from the left of the window stays cheap under
    sustained attack. Burst suppression: once we alert for an IP, further
    alerts from that IP are suppressed until the window expires, so a
    sustained attack generates one alert not thousands.
    """

    rule_id = "SSH-001"
    rule_name = "SSH brute force"
    severity = Severity.HIGH

    def __init__(
        self,
        threshold: int = 5,
        window: timedelta = timedelta(seconds=60),
    ) -> None:
        self.threshold = threshold
        self.window = window
        # keyed by IP — timestamps of failed attempts still inside the window
        self._attempts: dict[str, deque] = defaultdict(deque)
        # keyed by IP — suppress further alerts until this time
        self._already_alerted_until: dict[str, datetime] = {}

    def process(self, event: LogEvent) -> list[Alert]:
        if event.source != "ssh" or event.status != "failed" or event.source_ip is None:
            return []

        ip = event.source_ip
        bucket = self._attempts[ip]
        bucket.append(event.timestamp)

        # evict entries older than the sliding window from the left
        cutoff = event.timestamp - self.window
        while bucket and bucket[0] < cutoff:
            bucket.popleft()

        if len(bucket) < self.threshold:
            return []

        until = self._already_alerted_until.get(ip)
        if until is not None and event.timestamp < until:
            return []

        self._already_alerted_until[ip] = event.timestamp + self.window
        count = len(bucket)
        window_secs = int(self.window.total_seconds())
        return [
            Alert(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                severity=self.severity,
                timestamp=event.timestamp,
                source_ip=ip,
                confidence=min(1.0, 0.5 + 0.1 * count),
                summary=(
                    f"{count} failed SSH logins from {ip} "
                    f"within {window_secs}s"
                ),
                evidence=[event.raw],
            )
        ]


class SQLInjectionRule(Rule):
    """Signature-based SQL injection detector on HTTP paths.

    Signature matching has false-positive risk (legitimate apps with
    SQL-like query params) and false-negative risk (obfuscated payloads).
    Confidence is therefore 0.85, not 1.0, to reflect that uncertainty.
    """

    rule_id = "HTTP-001"
    rule_name = "Possible SQL injection"
    severity = Severity.CRITICAL

    # Multiple patterns are needed because SQLi comes in many syntactic
    # forms; one regex cannot cover auth bypass, UNION, comments, and
    # time-based blinds. Expand this list over time as new payloads appear.
    _PATTERNS: list[re.Pattern[str]] = [
        re.compile(
            r"(\bOR\b|\bAND\b)\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+",
            re.I,
        ),
        re.compile(r"UNION(\s+ALL)?\s+SELECT", re.I),
        re.compile(r"--\s*$", re.I),
        re.compile(r";\s*DROP\s+TABLE", re.I),
        re.compile(r"'\s*OR\s*'1'\s*=\s*'1", re.I),
        re.compile(r"SLEEP\(\d+\)", re.I),
    ]

    def process(self, event: LogEvent) -> list[Alert]:
        if event.source != "http" or event.path is None:
            return []

        for pattern in self._PATTERNS:
            if pattern.search(event.path):
                return [
                    Alert(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        severity=self.severity,
                        timestamp=event.timestamp,
                        source_ip=event.source_ip,
                        confidence=0.85,
                        summary=f"Possible SQL injection in path from {event.source_ip}",
                        evidence=[event.raw],
                    )
                ]
        return []


class SuspiciousUserAgentRule(Rule):
    """Flag known security-scanning tools by self-identifying User-Agent.

    Sophisticated attackers spoof their UA, so this complements but does
    not replace behavioural rules. Confidence is 0.7.
    """

    rule_id = "HTTP-002"
    rule_name = "Suspicious user agent"
    severity = Severity.MEDIUM

    # Extend this list as new tools are encountered. Keep entries lowercase —
    # we match against ua.lower().
    _SUSPICIOUS: tuple[str, ...] = (
        "sqlmap",
        "nikto",
        "nmap",
        "masscan",
        "dirbuster",
        "wpscan",
        "hydra",
        "burpsuite",
        "metasploit",
        "gobuster",
    )

    def process(self, event: LogEvent) -> list[Alert]:
        if event.source != "http" or event.user_agent is None:
            return []

        ua_lower = event.user_agent.lower()
        for tool in self._SUSPICIOUS:
            if tool in ua_lower:
                return [
                    Alert(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        severity=self.severity,
                        timestamp=event.timestamp,
                        source_ip=event.source_ip,
                        confidence=0.7,
                        summary=(
                            f"Suspicious user agent '{tool}' from "
                            f"{event.source_ip}"
                        ),
                        evidence=[event.raw],
                    )
                ]
        return []


class CanaryTokenRule(Rule):
    """Canary tokens: resources with no legitimate use that attract attackers.

    A canary is a path, credential, or file that exists only as bait. Any
    access is therefore unambiguously malicious, so confidence = 1.0 (the
    highest possible). Place canaries where attackers probe (/.env.bak,
    credential files, backup archives). SSH canary usernames work because
    an admin who knows the canary username exists would never accidentally
    use it in production — so any login attempt for that user is hostile.
    """

    rule_id = "CANARY-001"
    rule_name = "Canary token accessed"
    severity = Severity.CRITICAL

    def __init__(
        self,
        canary_paths: list[str] | None = None,
        canary_users: list[str] | None = None,
    ) -> None:
        # sets for O(1) lookup; defaults are examples — production should customise
        self.canary_paths = set(canary_paths or ["/admin/backup.zip", "/.env.bak"])
        self.canary_users = set(canary_users or ["svc-monitoring-readonly"])

    def process(self, event: LogEvent) -> list[Alert]:
        alerts: list[Alert] = []

        if event.source == "http" and event.path is not None:
            if event.path in self.canary_paths:
                alerts.append(
                    Alert(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        severity=self.severity,
                        timestamp=event.timestamp,
                        source_ip=event.source_ip,
                        confidence=1.0,
                        summary=f"Canary path {event.path} accessed from {event.source_ip}",
                        evidence=[event.raw],
                    )
                )

        if event.source == "ssh" and event.user is not None:
            if event.user in self.canary_users:
                alerts.append(
                    Alert(
                        rule_id=self.rule_id,
                        rule_name=self.rule_name,
                        severity=self.severity,
                        timestamp=event.timestamp,
                        source_ip=event.source_ip,
                        confidence=1.0,
                        summary=(
                            f"Canary SSH user '{event.user}' from "
                            f"{event.source_ip}"
                        ),
                        evidence=[event.raw],
                    )
                )

        return alerts


class PortScanHintRule(Rule):
    """Sliding-window detector for many HTTP 404s from one IP.

    Same algorithm as SSHBruteForceRule but applied to 404 responses. Many
    404s in a short window suggests dirbuster/gobuster-style enumeration.
    Confidence is 0.6 (lower than brute force) because a legitimate user
    clicking many broken links could also trigger this.
    """

    rule_id = "HTTP-003"
    rule_name = "Possible directory/path scan"
    severity = Severity.MEDIUM

    def __init__(
        self,
        threshold: int = 10,
        window: timedelta = timedelta(seconds=30),
    ) -> None:
        self.threshold = threshold
        self.window = window
        self._hits: dict[str, deque] = defaultdict(deque)
        self._alerted_until: dict[str, datetime] = {}
        self._seen_ips: set[str] = set()

    def process(self, event: LogEvent) -> list[Alert]:
        if event.source != "http" or event.status != "404" or event.source_ip is None:
            return []
        
        ip = event.source_ip
        
        bucket = self._hits[ip]
        
        if ip not in self._seen_ips:
            self._seen_ips.add(ip)
            bucket.append(event.timestamp)
            return []
        
        bucket.append(event.timestamp)

        cutoff = event.timestamp - self.window
        while bucket and bucket[0] < cutoff:
            bucket.popleft()    
            
        until = self._alerted_until.get(ip)
        if until is not None and event.timestamp < until:
            return []
        
        if len(bucket) < self.threshold:
            return []

        self._alerted_until[ip] = event.timestamp + self.window
        return [
            Alert(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                severity=self.severity,
                timestamp=event.timestamp,
                source_ip=ip,
                confidence=0.6,
                summary=(
                    f"{len(bucket)} HTTP 404s from {ip} within "
                    f"{int(self.window.total_seconds())}s"
                ),
                evidence=[event.raw],
            )
        ]

class HTTP401CredentialStuffingRule(Rule):
    """HTTP-004: Credential stuffing via repeated 401 Unauthorized responses.

    Tracks 401 responses per IP within a sliding time window. Fires when
    the number of 401s from a single IP exceeds threshold within the window.
    """

    def __init__(self, threshold: int = 10, window: timedelta = timedelta(seconds=60)):
        super().__init__()
        self.rule_id = "HTTP-004"
        self.rule_name = "Repeated 401 responses (credential stuffing)"
        self.severity = Severity.HIGH
        self.threshold = threshold
        self.window = window
        self._attempts: dict[str, deque] = {}
        self._alerted_until: dict[str, datetime] = {}
        self._seen_ips: set[str] = set()   # optimization: new IPs skip eviction

    def process(self, event: LogEvent) -> list[Alert]:
        if event.source != "http" or event.status != "401" or event.source_ip is None:
            return []

        ip = event.source_ip

        # Get or create the deque for this IP
        bucket = self._attempts.setdefault(ip, deque())

        # Optimisation: first time seeing this IP → no eviction needed
        if ip not in self._seen_ips:
            self._seen_ips.add(ip)
            bucket.append(event.timestamp)
            return []

        # Known IP: append timestamp
        bucket.append(event.timestamp)

        # Evict entries older than the window
        cutoff = event.timestamp - self.window
        while bucket and bucket[0] < cutoff:
            bucket.popleft()

        # Cooldown check (after eviction so bucket stays fresh)
        until = self._alerted_until.get(ip)
        if until is not None and event.timestamp < until:
            return []

        # Threshold check
        if len(bucket) < self.threshold:
            return []

        # Alert! Update cooldown and return Alert
        self._alerted_until[ip] = event.timestamp + self.window
        return [
            Alert(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                severity=self.severity,
                timestamp=event.timestamp,
                source_ip=ip,
                confidence=0.9,
                summary=(
                    f"{len(bucket)} HTTP 401 responses from {ip} within "
                    f"{int(self.window.total_seconds())}s"
                ),
                evidence=[event.raw],
            )
        ]


# Add new rule classes here to include them in the default engine. Order
# matters only if rules share state, which the current rules do not.
DEFAULT_RULES: list[type[Rule]] = [
    SSHBruteForceRule,
    SQLInjectionRule,
    SuspiciousUserAgentRule,
    CanaryTokenRule,
    PortScanHintRule,
    HTTP401CredentialStuffingRule,
]


class RuleEngine:
    """Orchestrator: instantiate rules, feed events, apply confidence guard.

    Error isolation: a bug in one rule must never stop the others from
    running. Each rule.process() is wrapped so an exception is swallowed
    for that rule only and the remaining rules still execute.
    """

    def __init__(
        self,
        rules: list[Rule] | None = None,
        min_confidence: float = CONFIDENCE_THRESHOLD_DEFAULT,
    ) -> None:
        # rules defaults to None so tests can pass pre-instantiated rules with
        # custom config, while production uses DEFAULT_RULES instances.
        if rules is None:
            self.rules = [cls() for cls in DEFAULT_RULES]
        else:
            self.rules = list(rules)
        self.min_confidence = min_confidence

    def process_event(self, event: LogEvent) -> list[Alert]:
        alerts: list[Alert] = []
        for rule in self.rules:
            try:
                alerts.extend(rule.process(event))
            except Exception:
                # a buggy rule must not take down detection for the whole pipeline
                continue
        return [a for a in alerts if a.confidence >= self.min_confidence]

    def process_events(self, events) -> list[Alert]:
        # Convenience method for batch processing; the engine's state
        # (sliding windows, suppression) persists across calls.
        all_alerts: list[Alert] = []
        for event in events:
            all_alerts.extend(self.process_event(event))
        return all_alerts
