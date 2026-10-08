# AlertDesk

Intern capstone scaffold for the **AlertDesk Intern Guide** (Year 2 cybersecurity,
8 weeks), version **1.0.0**. Documentation deliverables are intern-written;
the API core runs today.

![CI](https://github.com/YOUR_USERNAME/capstone/actions/workflows/alertdesk.yml/badge.svg)

## What it does

AlertDesk is a FastAPI + SQLite service for security ticket intake. **Severities,
statuses, legal transitions, and roles** are loaded from `config/client-spec.json`
so a new client brief does not require hardcoded Python enums. Auth is a **Bearer
token stub** mapped in that spec — replace it in Month 4.

## Quick start

```bash
git clone https://github.com/YOUR_USERNAME/capstone.git
cd capstone/alertdesk
pip install -e ".[dev]"
pytest tests/ -v
python -m alertdesk.cli
```

Open http://127.0.0.1:8000/docs for OpenAPI.

```bash
curl -s -H "Authorization: Bearer analyst-token" \
  -H "Content-Type: application/json" \
  -d '{"title":"Phish","severity":"high"}' \
  http://127.0.0.1:8000/tickets
```

Lead token `lead-token` may transition; `analyst-token` may not.

## Git / PR workflow

| Work | PR target |
|------|-----------|
| Weekly | Fork **`main`** |
| Milestones (Month 4/5/6) | Upstream **`intern/YOUR_USERNAME`** |
| Never | Upstream **`main`** |

## Client flexibility

| File | Role |
|------|------|
| [docs/client/BRIEF.md](docs/client/BRIEF.md) | Sample Sentinel SOC letter |
| [docs/client/spec.example.json](docs/client/spec.example.json) | Example workflow spec |
| [config/client-spec.json](config/client-spec.json) | Runtime spec |
| `docs/SPEC.md` | You write this in Week 1 |

## Internship path

| Week | You create / complete |
|------|------------------------|
| 1 | `docs/SPEC.md` + threat/abuse notes from the brief |
| 2 | Fork, `SECURITY.md`, secret scanning |
| 3 | Auth tests; ≥80% coverage |
| 4 | Commit OpenAPI; security assessment (Month 4) |
| 5 | `scripts/benchmark.py` + observability notes |
| 6 | Architecture; flags or a new status from an updated client spec |
| 7 | Dockerfile, migrations story, Trivy |
| 8 | CHANGELOG, v1.0.0, incident playbook, handoff |

See **AlertDesk_Intern_Guide.md**.

## Release and operations

- [CHANGELOG](CHANGELOG.md) records the 1.0.0 release scope.
- [Incident playbook](docs/INCIDENT_PLAYBOOK.md) covers response for this lab
  service.
