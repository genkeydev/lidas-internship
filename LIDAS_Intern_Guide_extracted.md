LIDAS
Lightweight Intrusion Detection System
Intern Step-by-Step Build Guide · Year 1 Cybersecurity Capstone
2-Month · 8-Week · Python 3.12+
ℹ
This guide walks you through building LIDAS week by week, from empty repo to a fully tested, HMAC-chained, containerised IDS. Code scaffolding has already been provided — your job is to read, understand, extend, and test each component before moving to the next.

⚑
Tasks marked with ⚑ are security-specific. These are not optional extras — they are the point of this capstone. Treat them as the highest-priority tasks in each week.

Project overview
LIDAS is a log-parsing intrusion detection system written in Python. It reads SSH and HTTP access logs line-by-line, runs each log event through a set of detection rules, emits colour-coded alerts to the console, and writes every alert to a tamper-evident HMAC-chained audit log on disk.

By the end of Month 2, you will have:
• A working IDS that detects SSH brute force, SQL injection, suspicious user agents, canary token access, and directory scanning
• A HMAC-chained audit log whose integrity can be verified cryptographically
• A test suite with ≥80% coverage including positive, negative, and fuzz cases
• A Dockerised deployment with a hardened, non-root, distroless image
• A GitHub Actions CI pipeline running SAST, Trivy, and the full test suite on every push

Repository layout (provided scaffold)
lidas/
├── lidas/
│   ├── __init__.py       # package entry, version
│   ├── parser.py         # raw log line → LogEvent dataclass
│   ├── models.py         # Alert, Severity dataclasses
│   ├── rules.py          # Rule base class + 5 detection rules + RuleEngine
│   ├── audit_log.py      # HMAC-chained AuditLogWriter / Verifier
│   ├── emitter.py        # ConsoleEmitter, AuditLogEmitter, MultiEmitter
│   └── cli.py            # `python -m lidas.cli scan|tail|verify`
├── tests/
│   ├── test_parser.py    # starter parser tests (extend in Week 3)
│   ├── test_rules.py     # stub with one example — Week 3 deliverable
│   └── test_audit_log.py # stub — Week 3 deliverable
├── fixtures/
│   ├── sample_ssh.log    # mixed legit + brute-force SSH lines
│   └── sample_http.log   # mixed legit + SQLi + canary + scan lines
├── docs/                 # your documentation goes here (Week 1+)
├── scripts/              # Week 5 benchmark script goes here
├── data/
│   └── .gitkeep          # HMAC key + audit log created at runtime (gitignored)
├── .github/workflows/ci.yml  # test + SAST scaffold; Trivy runs after Week 7 Dockerfile
├── .gitignore
├── pyproject.toml
├── README.md
└── SECURITY.md           # Week 2 template — replace placeholders before committing

Tech stack
• Python 3.12+ — standard library only (no third-party runtime deps)
• pytest + pytest-cov — test runner and coverage measurement
• Semgrep — SAST in CI
• Trivy — container image vulnerability scan in CI
• Docker (distroless base) — containerisation in Month 2 Week 7
• GitHub Actions — CI pipeline in Month 2 Week 7

Before you start
Tools to install on your machine
• Python 3.12 or later — python.org
• Git — git-scm.com
• Docker Desktop — docker.com/products/docker-desktop
• A code editor — VS Code with the Python extension is recommended
• GitHub account — github.com (free)

Concepts to read before Week 1
You do not need to master these before starting — you will encounter them in context. But a quick read now will make Week 1 move faster.
• What is an IDS vs IPS? (Wikipedia, 15 min)
• OWASP Top 10 — specifically A03 Injection and A07 Identification & Authentication Failures (owasp.org, 30 min)
• What is HMAC? — read the Wikipedia article and understand why HMAC-SHA256 is used instead of plain SHA-256 (20 min)
• Python dataclasses — docs.python.org/3/library/dataclasses.html (20 min)
• pytest basics — pytest.org/en/stable/getting-started.html (20 min)

📖
Keep a learning journal. After each week, write 3–5 sentences: what you built, what confused you, and what you would do differently. Your mentor will review this at the end of each month.


  MONTH 1 — Spec · Secure Repo · Testing · Docs
Goal: understand every line of the scaffold, write tests for it, harden the repo, and produce a threat model.
Week 1 — Spec & threat modeling
Duration: ~8–10 hours across the week

This week is about reading before writing. Do not touch the code yet — understand what it does and what threats it needs to address.

Day 1–2 · Read the scaffold
• Open each file in lidas/ and read every docstring and comment
• Draw the data flow on paper: log file → parser → LogEvent → RuleEngine → Alert → emitter → audit log
• Write down every question you have about the code in your learning journal

Day 2–3 · Write the project spec
Create docs/SPEC.md with the following sections:
• Purpose — one paragraph on what problem LIDAS solves
• Scope — what log formats are supported, what is explicitly out of scope
• Detection categories — list each rule (SSH-001, HTTP-001, HTTP-002, CANARY-001, HTTP-003) and what it detects
• Acceptance criteria — for each rule, what input should trigger it and what should not

⚑
Acceptance criteria are the security contract for the system. Write them before touching any code. Example: SSH-001 MUST fire after 5 failed logins from the same IP within 60 seconds. It MUST NOT fire for 4 failed logins. It MUST NOT fire for a successful login regardless of prior failures from the same IP.

Day 3–5 · Run the STRIDE threat model
STRIDE stands for: Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege. Apply it to the data flow you drew on Day 1.

Create docs/THREAT_MODEL.md. For each STRIDE category, answer:
⚑ Spoofing: Can an attacker fake a log source to avoid detection?
⚑ Tampering: Can an attacker modify the log file before LIDAS reads it? What happens to the audit log?
⚑ Repudiation: Can an attacker deny that an attack happened? What does the HMAC chain protect against?
⚑ Information Disclosure: Does the audit log leak sensitive information (e.g., full request bodies with passwords)?
⚑ Denial of Service: Can a malformed log line crash the IDS and stop detection?
⚑ Elevation of Privilege: If LIDAS runs as root, what happens if an attacker exploits a bug in it?

Week 1  ·  Spec & threat modeling  ⚑
Engineering
Read every file in the scaffold — understand the data flow before touching code
Engineering
Draw the data flow diagram on paper: log → parser → engine → emitter → audit log
Engineering
Write docs/SPEC.md covering purpose, scope, detection categories, acceptance criteria
⚑ Security
Write docs/THREAT_MODEL.md using STRIDE across the full data flow
⚑ Security
Document trust boundaries: who can write logs, who can read the audit log, where the HMAC key lives
✓  Deliverable: docs/SPEC.md and docs/THREAT_MODEL.md committed

Week 2 — Secure Git setup
Duration: ~6–8 hours across the week

This week you set up the repository security controls that protect the project itself — not just the code it produces.

Step 1 · Fork the upstream scaffold
• Open https://github.com/YOUR_ORG/lidas (mentor will give you the real org name)
• Click Fork — fork into your own GitHub account (or the assigned org)
• The fork already includes the scaffold .gitignore — do not replace it
• Licence: keep/verify LICENSE from upstream; if none exists, add an MIT LICENSE on your fork
git clone https://github.com/YOUR_USERNAME/lidas.git
cd lidas
# Confirm origin points at your fork
git remote -v
# Optional but recommended: track upstream so you can pull mentor updates
git remote add upstream https://github.com/YOUR_ORG/lidas.git
git fetch upstream

Where do PRs go? (hybrid workflow — learn this now, use it every week)
• Weekly / day-to-day work: open a PR into your fork’s main (origin). Branch
  protection and fork CI are your gate — merge only when Checks pass.
• Milestone handoffs (end of Month 1, Week 6 architecture deliverable, Week 8
  handoff): after work is on your fork’s main, open a PR into upstream base
  branch intern/YOUR_USERNAME on YOUR_ORG/lidas — never into upstream main.
  Example: base repo YOUR_ORG/lidas, base branch intern/alice, head = your fork.
• Upstream main is mentors only. Do not open PRs targeting it.
• Mentor creates intern/YOUR_USERNAME on upstream once (from upstream main)
  before your first milestone PR. Confirm the exact branch name with them.
• CI: fork Actions = intern gate for weekly merges. The same ci.yml also runs
  on upstream for pushes to intern/** and PRs into intern/** (org/mentor gate).
  First milestone PR from a fork may need a mentor to click “Approve and run
  workflows” on the upstream repo.

Step 2 · Protect the main branch
• GitHub → Settings → Branches → Add rule → Branch name pattern: main
• Tick: Require a pull request before merging
• Tick: Require status checks to pass before merging (leave the list empty for now — CI comes in Month 2)
• Tick: Do not allow bypassing the above settings

Step 3 · Enable secret scanning
• GitHub → Settings → Security → Code security → Secret scanning → Enable
• Also enable: Push protection — this blocks pushes containing detected secrets

⚑
Secret scanning matters for LIDAS specifically because config files may contain your HMAC key path or GeoIP API keys. Push protection catches accidental commits before they reach the remote.

Step 4 · Add a pre-commit hook (gitleaks)
• Install gitleaks — follow gitleaks.io/getting-started
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/sh
gitleaks detect --source . --no-git --exit-code 1
EOF
chmod +x .git/hooks/pre-commit

Step 5 · Write SECURITY.md
The scaffold ships SECURITY.md as a template with TODO placeholders. Replace
every placeholder section with your policy before committing. Include:
• How to report a vulnerability in LIDAS itself
• The HMAC key file location and that it must never be committed
• The fact that the audit log is append-only and must not be modified

Week 2  ·  Secure Git setup  ⚑
Engineering
Fork YOUR_ORG/lidas, clone your fork, confirm remotes (origin = fork; optional upstream)
Engineering
Add or verify licence on the fork — keep the scaffold .gitignore (do not replace it)
Engineering
Enable branch protection on main — require PR before merge
⚑ Security
Enable GitHub secret scanning + push protection
⚑ Security
Install gitleaks and add pre-commit hook that blocks secret commits
⚑ Security
Complete SECURITY.md template: reporting, HMAC key handling, audit log immutability
⚑ Security
Verify .gitignore: `git check-ignore -v data/hmac.key data/audit.log` must show matches; `data/.gitkeep` must NOT be ignored
Engineering
Confirm you know the hybrid PR rules: weekly → fork main; milestones → upstream intern/YOUR_USERNAME; never upstream main
✓  Deliverable: Hardened fork on GitHub, completed SECURITY.md committed

Week 3 — TDD: write the test suite
Duration: ~12–15 hours across the week — this is the heaviest week

The scaffold already has tests/test_parser.py (starter happy-path tests) plus stub files
tests/test_rules.py (two example SSH-001 tests) and tests/test_audit_log.py (skipped
placeholder). This week you extend those stubs into a full suite for the rules, the
audit log chain, and the rule engine — before reading the implementation in detail.
This is test-driven understanding: the tests are your specification in code.

Setup — install test dependencies
pip install pytest pytest-cov
# Verify the existing starter tests pass
cd lidas && pytest tests/ -v

Extend tests/test_rules.py
Replace/expand the example tests. Write at least two tests per rule: one positive case (attack detected) and one negative case (legitimate traffic not flagged). Here is the pattern to follow:

from datetime import datetime, timezone, timedelta
from lidas.parser import LogEvent
from lidas.rules import SSHBruteForceRule

FIXED_TS = datetime(2026, 6, 30, 9, 0, 0, tzinfo=timezone.utc)

def _ssh_failed(ip, offset_secs=0):
    return LogEvent(
        raw='...',
        timestamp=FIXED_TS + timedelta(seconds=offset_secs),
        source='ssh', source_ip=ip, status='failed', user='admin',
    )

def test_ssh_brute_force_triggers_after_threshold():
    rule = SSHBruteForceRule(threshold=5, window=timedelta(seconds=60))
    events = [_ssh_failed('10.0.0.5', i*2) for i in range(5)]
    alerts = []
    for e in events:
        alerts.extend(rule.process(e))
    assert len(alerts) == 1
    assert alerts[0].rule_id == 'SSH-001'

def test_ssh_brute_force_does_not_fire_below_threshold():
    rule = SSHBruteForceRule(threshold=5, window=timedelta(seconds=60))
    events = [_ssh_failed('10.0.0.5', i*2) for i in range(4)]
    alerts = []
    for e in events:
        alerts.extend(rule.process(e))
    assert len(alerts) == 0

Write equivalent tests for: SQLInjectionRule, SuspiciousUserAgentRule, CanaryTokenRule, PortScanHintRule. Also write:
• A test that a successful SSH login from the same IP does not trigger SSH-001
• A test that legitimate HTTP 200 responses do not trigger HTTP-003
• A test that a canary path access always returns confidence=1.0

Extend tests/test_audit_log.py
Remove the pytest.mark.skip placeholder and implement the tests below.
These are the most important tests in the project from a security perspective.

import json, tempfile, os
from pathlib import Path
from datetime import datetime, timezone
from lidas.models import Alert, Severity
from lidas.audit_log import AuditLogWriter, AuditLogVerifier

KEY = b'test-key-32-bytes-exactly-padded!'

def _alert():
    return Alert(
        rule_id='SSH-001', rule_name='SSH brute force',
        severity=Severity.HIGH,
        timestamp=datetime(2026,6,30,9,0,0,tzinfo=timezone.utc),
        source_ip='10.0.0.5', confidence=0.9,
        summary='test alert', evidence=['raw line'],
    )

def test_chain_verifies_clean_log():
    with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as f:
        path = f.name
    writer = AuditLogWriter(path, KEY)
    writer.write(_alert())
    writer.write(_alert())
    verifier = AuditLogVerifier(KEY)
    valid, bad = verifier.verify(path)
    assert valid is True
    assert bad == -1

def test_chain_detects_tampered_entry():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        path = f.name
    writer = AuditLogWriter(path, KEY)
    writer.write(_alert())
    writer.write(_alert())
    # Tamper with line 1
    lines = Path(path).read_text().splitlines()
    entry = json.loads(lines[0])
    entry['alert']['source_ip'] = '99.99.99.99'  # attacker changes the IP
    lines[0] = json.dumps(entry)
    Path(path).write_text('\n'.join(lines) + '\n')
    verifier = AuditLogVerifier(KEY)
    valid, bad = verifier.verify(path)
    assert valid is False
    assert bad == 1

Fuzz tests — malformed log lines
Add these to tests/test_parser.py or a new tests/test_fuzz.py:
• A 1 MB line of repeating 'A' characters
• A line of null bytes: '\x00' * 500
• A line with every unicode category mixed together
• An empty string, a string of only whitespace, a string of only newlines
All of these should return source='unknown' without raising any exception.

Run coverage and check the gate
# After the full suite is written, uncomment fail_under = 80 in pyproject.toml
pytest tests/ -v --cov=lidas --cov-report=term-missing
# Target: 80%+ coverage on lidas/ before end of week
# Also restore --cov-fail-under=80 in .github/workflows/ci.yml (see Week 7)

Week 3  ·  TDD — write the full test suite  ⚑
Engineering
Extend tests/test_rules.py: positive + negative test for every rule (10+ tests)
⚑ Security
Write test: a successful SSH login never triggers SSH-001 even after many prior failures
⚑ Security
Write test: legitimate HTTP 200 responses never trigger HTTP-003 (path scan rule)
⚑ Security
Write test: canary token access always returns confidence=1.0 (no threshold)
⚑ Security
Extend tests/test_audit_log.py: clean chain verifies, tampered entry is caught at correct line
⚑ Security
Extend tests/test_parser.py (or add tests/test_fuzz.py): 1MB line, null bytes, mixed unicode, empty — all return 'unknown', no crash
Engineering
Uncomment fail_under = 80 in pyproject.toml; run pytest --cov and reach ≥80% before committing
✓  Deliverable: Full test suite committed, ≥80% coverage passing

Week 4 — Tamper-evident logging & documentation
Duration: ~8–10 hours across the week

This week you run the system end-to-end for the first time, verify the HMAC chain manually, and write the documentation that an operator would use in production.

Step 1 · Run LIDAS against the fixture logs
mkdir -p data
python -m lidas.cli scan fixtures/sample_ssh.log
python -m lidas.cli scan fixtures/sample_http.log
You should see coloured alerts printed to the console and an audit.log written to data/.

Step 2 · Verify the HMAC chain
python -m lidas.cli verify data/audit.log
Expected output: OK: audit log chain is intact

Step 3 · Manually tamper and verify again
Open data/audit.log in a text editor. Change one character in any line. Save. Then run verify again:
python -m lidas.cli verify data/audit.log
Expected output: TAMPER DETECTED: chain broken at line N
Write what you observed in your learning journal. This is the core security property of the audit log — experience it hands-on.

Step 4 · Write docs/log-integrity.md
Document the HMAC chain in plain language that a non-developer could understand. Cover:
• What the chain is and why it matters (what it proves and what it does not prove)
• What GENESIS_HMAC is and why the chain needs a starting point
• What happens to entries after the tampered one (they all fail too — explain why)
• The step-by-step procedure to verify the chain using the CLI
• The limits of this approach: if the HMAC key leaks, an attacker can forge a consistent chain

Step 5 · Write docs/log-schema.md
Document the audit log JSON entry schema. Include an example entry with each field explained:
{
  "prev_hmac": "abc123...",   // HMAC of the previous entry
  "alert": {                  // the detection event
    "rule_id": "SSH-001",
    "severity": "HIGH",
    "timestamp": "2026-06-30T09:14:01+00:00",
    "source_ip": "10.0.0.5",
    "confidence": 0.9,
    "summary": "5 failed SSH logins...",
    "evidence": ["raw log line"]
  },
  "entry_hmac": "def456..."  // HMAC of prev_hmac + this alert
}

Week 4  ·  Audit logging & documentation  ⚑
Engineering
Run `python -m lidas.cli scan fixtures/sample_ssh.log` — see alerts printed
⚑ Security
Run `python -m lidas.cli scan fixtures/sample_http.log` — verify canary alert fires
⚑ Security
Run `python -m lidas.cli verify data/audit.log` — confirm chain is intact
⚑ Security
Manually tamper one byte in audit.log — re-verify and confirm TAMPER DETECTED at correct line
⚑ Security
Write docs/log-integrity.md: chain explanation, verification procedure, key leak limitation
Engineering
Write docs/log-schema.md: annotated example of each field in the audit log JSON format
Engineering
Open a PR for all Month 1 work into your fork’s main — review your own diff; merge only when fork CI is green. Then open a milestone PR into upstream intern/YOUR_USERNAME (not upstream main)
✓  Deliverable: Month 1 complete: spec, threat model, tests, audit log docs — on fork main and synced to upstream intern branch


  MONTH 2 — Architecture · Patterns · CI/CD · Docker
Goal: deepen the architecture, benchmark it, add new rules, ship a signed v1.0.0, and containerise with a hardened CI pipeline.
Week 5 — Efficient data structures & benchmarking
Duration: ~8–10 hours across the week

This week is about understanding why the existing data structure choices were made and measuring their performance.

Task 1 · Understand the sliding window (deque)
Open lidas/rules.py and find SSHBruteForceRule. The _attempts dict maps an IP address to a collections.deque. A deque is used instead of a list because:
• Appending to the right is O(1) — same as a list
• Removing from the left (popleft) is O(1) — a list would be O(n)
Trace through the sliding window eviction logic line by line in your learning journal. Draw a timeline with 7 events and show which entries are in the deque after each one.

Task 2 · Write a benchmark script
Create scripts/benchmark.py:
import time, random
from lidas.parser import parse_line
from lidas.rules import RuleEngine

def generate_ssh_line(ip, failed=True):
    result = 'Failed' if failed else 'Accepted'
    return f'Jun 30 09:14:01 host sshd[1]: {result} password for user test from {ip} port 22 ssh2'

engine = RuleEngine()
N = 10_000
lines = [generate_ssh_line(f'10.0.{random.randint(0,255)}.{random.randint(1,254)}') for _ in range(N)]

start = time.perf_counter()
for line in lines:
    event = parse_line(line)
    engine.process_event(event)
elapsed = time.perf_counter() - start
print(f'{N} events in {elapsed:.3f}s — {N/elapsed:.0f} events/sec')

Run it and note the result in docs/BENCHMARKS.md. Then add 100 rules (duplicate the brute force rule with different IPs) and re-run. What happens to throughput? Note your findings.

Task 3 · Bloom filter deduplication
PortScanHintRule currently tracks every 404 from every IP in a deque. Add a bloom filter to skip the deque lookup for IPs that have definitely not been seen before:
# In PortScanHintRule.__init__:
self._seen_ips = set()   # simple set as a bloom filter substitute
# In process(): return [] early if ip not in self._seen_ips and len(bucket) == 0
Benchmark again. Document the throughput improvement in BENCHMARKS.md.

Week 5  ·  Data structures & benchmarking
Engineering
Trace the sliding window deque eviction logic on paper with 7 timed events
Engineering
Write scripts/benchmark.py and record baseline throughput on 10k events
Engineering
Run benchmark with 100 rules — document the throughput drop in BENCHMARKS.md
Engineering
Add early-exit optimisation to PortScanHintRule — re-benchmark and document improvement
Engineering
Commit BENCHMARKS.md with a table: config, events/sec, memory estimate
✓  Deliverable: docs/BENCHMARKS.md committed with baseline + optimised results

Week 6 — Security architecture & least privilege
Duration: ~8–10 hours across the week

This week you audit the existing architecture for security boundaries, document them, and extend the system with a new rule.

Task 1 · Draw the trust boundary diagram
Using draw.io, Excalidraw, or even paper, draw the system with the following components and label the trust boundary of each:
• Log file (untrusted — written by the OS or application)
• Parser (reads untrusted input — must never crash or exec)
• Rule engine (trusted — modifies internal state only)
• Audit log file (trusted but append-only — must never be read-modified-written)
• HMAC key file (secret — 0600 permissions, never logged)
• Console output (output only — never loops back)
Save the diagram as docs/architecture.png and reference it from a new docs/ARCHITECTURE.md.

⚑
The key architectural security property is that the parser is the only component that touches untrusted data. The rule engine only ever receives already-parsed LogEvent objects. This is the separation of concerns that prevents a malformed log line from poisoning detection state.

Task 2 · Verify least-privilege file access
If you run LIDAS in production, it should not run as root. Verify this locally:
# Check what user would be used in Docker (Week 7 will enforce this)
# For now, run LIDAS and confirm it does NOT need write access to the log file it is reading
chmod 444 fixtures/sample_ssh.log
python -m lidas.cli scan fixtures/sample_ssh.log
# Should still work — LIDAS only reads the log, it does not write to it
chmod 644 fixtures/sample_ssh.log  # restore

Task 3 · Write a new detection rule
Add a new rule to lidas/rules.py. Choose one of:
• SSH-002 — Accepted login from a new/unknown IP (requires a known-good IP allowlist in config)
• HTTP-004 — Repeated 401 HTTP responses from the same IP (credential stuffing against a web login)
• HTTP-005 — Path traversal attempt (../../etc/passwd patterns in request path)
Follow the exact same class structure as the existing rules: inherit Rule, set rule_id/rule_name/severity, implement process(). Then write positive and negative tests before the implementation.

Week 6  ·  Security architecture & least privilege  ⚑
⚑ Security
Draw the trust boundary diagram and save to docs/architecture.png
⚑ Security
Write docs/ARCHITECTURE.md referencing the diagram and explaining each component's privilege level
⚑ Security
Verify LIDAS reads log files as read-only — document this in ARCHITECTURE.md
Engineering
Write tests for your new rule (positive + negative) BEFORE implementing it
Engineering
Implement the new rule and add it to DEFAULT_RULES in rules.py
Engineering
Run full test suite — confirm coverage stays at ≥80%
Engineering
Write an ADR (Architecture Decision Record) for your new rule in docs/adr/
✓  Deliverable: Architecture doc, trust boundary diagram, new rule with tests — merge to fork main via PR, then milestone PR to upstream intern/YOUR_USERNAME

Week 7 — Docker containerisation & hardening
Duration: ~10–12 hours across the week — you will hit Docker issues; that is expected

This week you containerise LIDAS with a hardened Docker image and write the GitHub Actions CI pipeline.

Step 1 · Write the Dockerfile
Create Dockerfile at the repo root:
# Stage 1: build / install dependencies (we have none, but this is the pattern)
FROM python:3.12-slim AS builder
WORKDIR /app
COPY lidas/ ./lidas/
COPY pyproject.toml* setup.cfg* ./

# Stage 2: minimal runtime image
FROM gcr.io/distroless/python3-debian12
# distroless has no shell, no package manager, no curl
# An attacker who exploits a bug gets almost nothing
WORKDIR /app
COPY --from=builder /app/lidas ./lidas

# Non-root user — distroless provides uid 65532 (nonroot)
USER nonroot

# Log file is passed in at runtime via volume mount
ENTRYPOINT ['/usr/bin/python3', '-m', 'lidas.cli']

Step 2 · Write docker-compose.yml
services:
  lidas:
    build: .
    volumes:
      # mount logs as read-only — LIDAS only reads them
      - ./fixtures:/logs:ro
      # audit log and HMAC key go in a named volume
      - lidas-data:/data
    environment:
      - LIDAS_AUDIT_LOG_PATH=/data/audit.log
      - LIDAS_KEY_PATH=/data/hmac.key
    command: ['scan', '/logs/sample_ssh.log']

volumes:
  lidas-data:

Step 3 · Build and test the image
docker build -t lidas:dev .
docker compose up
# You should see alerts printed, same as running locally

Step 4 · Extend the GitHub Actions CI pipeline
The scaffold already includes .github/workflows/ci.yml with test and SAST jobs.
The workflow triggers on push/PR to main and intern/** so the same file is the
intern gate on your fork and the mentor gate on upstream intern branches.
Do not replace the whole file from scratch — update it in place:
• Re-enable the coverage gate on the test job (--cov-fail-under=80) now that Week 3 tests exist
• Keep the container-scan job’s `if: hashFiles('Dockerfile') != ''` gate (or remove the
  `if:` only after your Dockerfile is committed — never paste a Trivy job that always runs
  before the Dockerfile exists)
• Keep the on: branches list as main + intern/** (do not broaden to every ref)

Target shape of .github/workflows/ci.yml after Week 7:
name: CI
on:
  push:
    branches: [main, "intern/**"]
  pull_request:
    branches: [main, "intern/**"]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install pytest pytest-cov
      - run: pytest tests/ --cov=lidas --cov-fail-under=80

  sast:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: returntocorp/semgrep-action@v1
        with:
          config: 'p/python'

  container-scan:
    runs-on: ubuntu-latest
    needs: test
    if: hashFiles('Dockerfile') != ''
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t lidas:ci .
      - uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'lidas:ci'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'

⚑
The CI pipeline is itself a security control. The SAST job catches code-level vulnerabilities. The Trivy job catches known CVEs in the base image and Python packages. The coverage gate ensures detection rules cannot be shipped without tests. All three must pass before a PR can be merged.

Week 7  ·  Docker containerisation & CI/CD pipeline  ⚑
⚑ Security
Write a two-stage Dockerfile using distroless as the runtime image
⚑ Security
Confirm the container runs as UID 65532 (nonroot) — verify with `docker inspect`
⚑ Security
Mount the log file read-only (:ro) in docker-compose.yml
⚑ Security
Mount the audit log and HMAC key in a named volume — never in the image
⚑ Security
Extend .github/workflows/ci.yml: coverage gate on, Trivy runs once Dockerfile exists; keep triggers on main + intern/**
Engineering
Push to your fork — verify CI jobs pass in the Actions tab (fork gate)
Engineering
Add the CI status badge to README.md
✓  Deliverable: Hardened Docker image, CI pipeline passing on GitHub, status badge in README

Week 8 — Signed v1.0.0 release & retrospective
Duration: ~6–8 hours across the week

This is the final week. You package, sign, and release LIDAS v1.0.0, write the release notes, and present your learning to your mentor.

Step 1 · Update the version
Open lidas/__init__.py and change __version__ = '0.1.0' to __version__ = '1.0.0'.
git add lidas/__init__.py
git commit -m 'chore: bump version to 1.0.0'

Step 2 · Write CHANGELOG.md
Create CHANGELOG.md at the repo root following the Keep a Changelog format:
# Changelog

## [1.0.0] - 2026-07-07

### Added
- SSH brute force detection (SSH-001): sliding window, 5 failures in 60s
- SQL injection detection (HTTP-001): 6 regex patterns
- Suspicious user agent detection (HTTP-002)
- Canary token detection (CANARY-001): paths and SSH usernames
- Directory scan detection (HTTP-003)
- [YOUR NEW RULE FROM WEEK 6]
- HMAC-SHA256 chained audit log with tamper verification
- CLI: scan, tail, verify subcommands
- Docker: distroless, non-root, read-only log mount
- CI: test (≥80% coverage), SAST (Semgrep), container scan (Trivy)

### Security
- All threat model items from docs/THREAT_MODEL.md addressed
- HMAC key file created with 0600 permissions on first run
- Audit log is append-only; no read-modify-write possible via CLI

Step 3 · Tag and release on GitHub (on your fork)
git tag -a v1.0.0 -m 'Release v1.0.0'
git push origin v1.0.0
Go to your fork on GitHub → Releases → Draft a new release → choose tag v1.0.0.
Paste your CHANGELOG entry into the release notes. Attach any relevant benchmark numbers.
Do not push release tags to upstream main. After the release is on your fork, open a
milestone handoff PR into upstream intern/YOUR_USERNAME so the org has your final tree.
If your mentor asks you to tag the upstream intern branch, follow their instructions —
still never tag or release against upstream main.

Step 4 · OWASP Dependency-Check (stretch goal)
Run OWASP Dependency-Check against the project to verify there are no known vulnerable dependencies (LIDAS has no runtime Python deps, so this should be clean):
docker run --rm -v $(pwd):/src owasp/dependency-check:latest \
  --project lidas --scan /src --format HTML --out /src/docs/dep-check.html
Link the clean report in your release notes.

Step 5 · Retrospective — present to your mentor
Prepare a 15-minute walkthrough covering:
• The threat model: what threats you identified and how LIDAS addresses each
• The HMAC chain: live demo of tamper detection using the CLI
• The rule engine: explain the sliding window algorithm in your own words
• The CI pipeline: show a passing pipeline run on your fork, and (if available) on the upstream intern branch
• What you would do differently if you started again
• What you want to build in Month 3 (integration tests, hardened chain verification, SIEM integration)

Week 8  ·  Signed v1.0.0 release & retrospective  ⚑
Engineering
Update __version__ to 1.0.0 in lidas/__init__.py
⚑ Security
Write CHANGELOG.md with all features and security items from Months 1–2
Engineering
Tag v1.0.0 and publish a GitHub Release on your fork (not upstream main); then open handoff PR to upstream intern/YOUR_USERNAME
⚑ Security
Run OWASP Dependency-Check and link the clean report in the release notes
⚑ Security
Verify the final audit log chain is intact after all test runs: `python -m lidas.cli verify data/audit.log`
Engineering
Prepare and deliver 15-minute retrospective to mentor
✓  Deliverable: v1.0.0 on your fork with CHANGELOG and benchmarks; milestone handoff on upstream intern branch

Evaluation criteria
Your mentor will assess the following at the end of Month 2:

■  Threat model quality
Does THREAT_MODEL.md identify realistic threats? Are the mitigations specific and verifiable?
■  Test coverage & quality
Are there positive AND negative cases for every rule? Do fuzz tests cover binary and malformed inputs? Is coverage ≥80%?
■  HMAC chain correctness
Does the tamper detection test pass? Can you explain why entry N+1 fails when entry N is tampered?
■  Architecture documentation
Does ARCHITECTURE.md accurately describe trust boundaries? Is the distroless/non-root Docker setup explained?
■  CI pipeline
Do all three jobs (test, SAST, Trivy) pass? Is the pipeline blocking — not just advisory?
■  New rule quality
Is the new rule from Week 6 well-tested, well-documented, and added to DEFAULT_RULES?
■  CHANGELOG & release
Is v1.0.0 tagged, released, and documented to a standard a colleague could understand?

Quick reference
Key commands
# Run all tests with coverage
pytest tests/ -v --cov=lidas --cov-report=term-missing

# Scan a log file
python -m lidas.cli scan fixtures/sample_ssh.log

# Follow a growing log file
python -m lidas.cli tail /var/log/auth.log

# Verify the audit log chain
python -m lidas.cli verify data/audit.log

# Build and run in Docker
docker build -t lidas:dev . && docker compose up

# Run SAST locally
semgrep --config=p/python lidas/

# Scan Docker image for CVEs
trivy image lidas:dev

Files you will create or complete
(Create = new file. Complete/extend = scaffold stub or template already present.)

docs/SPEC.md  (Week 1 · create)  Project specification and acceptance criteria
docs/THREAT_MODEL.md  (Week 1 · create)  STRIDE analysis across the full data flow
SECURITY.md  (Week 2 · complete template)  Vulnerability disclosure and key handling policy
tests/test_rules.py  (Week 3 · extend stub)  Positive + negative tests for all detection rules
tests/test_audit_log.py  (Week 3 · extend stub)  HMAC chain clean and tamper detection tests
tests/test_parser.py / test_fuzz.py  (Week 3 · extend)  Fuzz cases for malformed input
docs/log-integrity.md  (Week 4 · create)  Plain-language chain explanation and verify procedure
docs/log-schema.md  (Week 4 · create)  Annotated audit log JSON schema
scripts/benchmark.py  (Week 5 · create)  Throughput benchmarking script
docs/BENCHMARKS.md  (Week 5 · create)  Benchmark results table
docs/ARCHITECTURE.md  (Week 6 · create)  Trust boundary diagram and component description
lidas/rules.py  (Week 6 · extend)  New detection rule added to DEFAULT_RULES
Dockerfile  (Week 7 · create)  Two-stage distroless, non-root container
docker-compose.yml  (Week 7 · create)  Read-only log mount, named volume for data
.github/workflows/ci.yml  (Week 7 · extend)  Coverage gate + Trivy once Dockerfile exists
CHANGELOG.md  (Week 8 · create)  v1.0.0 release notes in Keep a Changelog format

LIDAS Intern Guide · Year 1 Cybersecurity Capstone · Genkey / Effesus Technologies