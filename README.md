# LIDAS — Lightweight Intrusion Detection System

Intern capstone scaffold for the **LIDAS Intern Guide** (8-week programme).
Follow the guide week by week; files marked as deliverables in the guide are
intentionally missing or stubbed here.

![CI](https://github.com/YOUR_USERNAME/lidas/actions/workflows/ci.yml/badge.svg)

## What it does

LIDAS is a lightweight intrusion detection system that parses SSH and HTTP
access logs, runs five detection rules (SSH brute force, SQL injection,
suspicious user agents, canary tokens, and directory/path scanning), and
records every alert in an HMAC-chained append-only audit log. Operators can
`scan` a file once, `tail` a growing log, or `verify` audit-log integrity
from the CLI.

## Quick start

1. Fork `https://github.com/YOUR_ORG/lidas` on GitHub (mentor provides the real org).
2. Clone **your fork**, then run:

```bash
git clone https://github.com/YOUR_USERNAME/lidas.git
cd lidas
pip install pytest pytest-cov
pytest tests/ -v
python -m lidas.cli scan fixtures/sample_ssh.log
python -m lidas.cli verify data/audit.log
```

The CI badge above points at your fork’s Actions once you replace `YOUR_USERNAME`.

## Git / PR workflow

| Work | PR target |
|------|-----------|
| Weekly / day-to-day | Your **fork’s `main`** (intern gate — fork CI must pass) |
| Milestones (Month 1, Week 6, Week 8 handoff) | Upstream **`YOUR_ORG/lidas`** branch **`intern/YOUR_USERNAME`** |
| Never | Upstream **`main`** (mentors only) |

CI: the same `.github/workflows/ci.yml` runs on `main` and `intern/**`. Fork Actions are your day-to-day gate; upstream Actions on `intern/*` validate milestone PRs.

## Detection rules

| Rule ID    | Name                        | Severity | Trigger                                      |
|------------|-----------------------------|----------|----------------------------------------------|
| SSH-001    | SSH brute force             | HIGH     | ≥5 failed SSH logins from one IP in 60s      |
| HTTP-001   | Possible SQL injection      | CRITICAL | SQLi signatures in the HTTP request path     |
| HTTP-002   | Suspicious user agent       | MEDIUM   | Known scanner tools in the User-Agent string |
| CANARY-001 | Canary token accessed       | CRITICAL | Access to decoy paths or canary SSH users    |
| HTTP-003   | Possible directory/path scan| MEDIUM   | ≥10 HTTP 404s from one IP in 30s             |

## CLI commands

- **scan** — process a log file once and exit
- **tail** — follow a growing log file continuously (like `tail -f`)
- **verify** — verify the HMAC chain integrity of an audit log

## Configuration (environment variables)

| Variable              | Default            | Description                                      |
|-----------------------|--------------------|--------------------------------------------------|
| `LIDAS_AUDIT_LOG_PATH`| `./data/audit.log` | Path to the append-only HMAC audit log           |
| `LIDAS_KEY_PATH`      | `./data/hmac.key`  | Path to the 32-byte HMAC key file                |
| `LIDAS_MIN_CONFIDENCE`| `0.5`              | Global confidence threshold; lower alerts drop   |

## Security notes

- The HMAC key file is created at `LIDAS_KEY_PATH` on first run with `0600`
  permissions. Never commit it — `data/*` is in `.gitignore`.
- The audit log is append-only. To verify integrity: `lidas verify <path>`
- Run LIDAS as a non-root user in production (enforced in the Week 7 Docker image).

## Provided scaffold layout

```
lidas/
├── lidas/
│   ├── __init__.py
│   ├── models.py
│   ├── parser.py
│   ├── rules.py
│   ├── audit_log.py
│   ├── emitter.py
│   └── cli.py
├── tests/
│   ├── test_parser.py      # starter parser tests (extend in Week 3)
│   ├── test_rules.py       # stub — Week 3 deliverable
│   └── test_audit_log.py   # stub — Week 3 deliverable
├── fixtures/
│   ├── sample_ssh.log
│   └── sample_http.log
├── docs/                   # Week 1+ documentation deliverables
├── scripts/                # Week 5 benchmark script
├── data/
│   └── .gitkeep            # runtime key + audit log created here
├── .github/workflows/ci.yml  # test + SAST now; Trivy after Week 7 Dockerfile
├── .gitignore
├── pyproject.toml
├── README.md
└── SECURITY.md             # Week 2 template — replace placeholders
```

## Internship path

| Week | You create / complete |
|------|------------------------|
| 1 | `docs/SPEC.md`, `docs/THREAT_MODEL.md` (create) |
| 2 | Fork upstream → harden fork; learn hybrid PRs (fork `main` weekly; upstream `intern/YOU` for milestones) |
| 3 | Extend test stubs; fuzz cases; ≥80% coverage (`fail_under` in pyproject.toml) |
| 4 | `docs/log-integrity.md`, `docs/log-schema.md`; Month 1 PR → fork `main`, then upstream `intern/YOU` |
| 5 | `scripts/benchmark.py`, `docs/BENCHMARKS.md` (create) |
| 6 | `docs/ARCHITECTURE.md`, new rule; PR → fork `main`, then upstream `intern/YOU` |
| 7 | `Dockerfile`, `docker-compose.yml`; extend CI (coverage + Trivy; triggers on `main` + `intern/**`) |
| 8 | `CHANGELOG.md`, v1.0.0 release on fork; handoff PR to upstream `intern/YOU` |

See **LIDAS_Intern_Guide** (in this repo or provided by your mentor) for the full checklist.
