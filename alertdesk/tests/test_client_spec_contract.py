"""API contract tests for client-controlled workflow configuration."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from alertdesk import db
from alertdesk.app import app


def test_api_obeys_updated_client_workflow_spec(tmp_path, monkeypatch):
    """A client can add a workflow status without changing application code."""
    spec = {
        "schemaVersion": "1.0.0",
        "client": "Contract test client",
        "severities": ["low", "urgent"],
        "initialStatus": "new",
        "statuses": ["new", "waiting-vendor", "closed"],
        "transitions": {
            "new": ["waiting-vendor"],
            "waiting-vendor": ["closed"],
            "closed": [],
        },
        "roles": {
            "analyst": ["create", "list", "get"],
            "lead": ["create", "list", "get", "transition"],
        },
        "tokens": {"analyst-contract-token": "analyst", "lead-contract-token": "lead"},
    }
    spec_path = tmp_path / "client-spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    db_path = tmp_path / "contract.sqlite"
    monkeypatch.setenv("ALERTDESK_SPEC", str(spec_path))
    monkeypatch.setenv("ALERTDESK_DB", str(db_path))

    conn = db.connect(db_path)
    db.init_schema(conn)
    conn.close()

    with TestClient(app) as client:
        created = client.post(
            "/tickets",
            json={"title": "Vendor review", "severity": "urgent"},
            headers={"Authorization": "Bearer analyst-contract-token"},
        )
        assert created.status_code == 200
        ticket_id = created.json()["id"]
        assert created.json()["status"] == "new"

        waiting = client.post(
            f"/tickets/{ticket_id}/transition",
            json={"status": "waiting-vendor"},
            headers={"Authorization": "Bearer lead-contract-token"},
        )
        assert waiting.status_code == 200
        assert waiting.json()["status"] == "waiting-vendor"

        illegal = client.post(
            f"/tickets/{ticket_id}/transition",
            json={"status": "new"},
            headers={"Authorization": "Bearer lead-contract-token"},
        )
        assert illegal.status_code == 409
