"""Week 3 deliverable: auth, assign, list, audit, fuzz.

TODO (Week 3):
- analyst cannot transition (403)
- unknown token (401)
- assign then legal triaged transition
- severity not in spec (400)
- malformed JSON / extra fields
"""


import os

import pytest
from fastapi.testclient import TestClient

from alertdesk import db
from alertdesk.app import app
@pytest.fixture()
def client(tmp_path, monkeypatch):
    dbfile = tmp_path / "test.sqlite"
    monkeypatch.setenv("ALERTDESK_DB", str(dbfile))
    monkeypatch.setenv(
        "ALERTDESK_SPEC",
        str(os.path.abspath("config/client-spec.json"))
    )

    conn = db.connect(dbfile)
    db.init_schema(conn)
    conn.close()

    with TestClient(app) as c:
        yield c
def test_analyst_cannot_transition(client: TestClient):
    created = client.post(
        "/tickets",
        json={"title": "Test ticket", "severity": "high"},
        headers={"Authorization": "Bearer analyst-token"},
    )
    assert created.status_code == 200

    ticket_id = created.json()["id"]

    res = client.post(
        f"/tickets/{ticket_id}/transition",
        json={"status": "triaged"},
        headers={"Authorization": "Bearer analyst-token"},
    )

    assert res.status_code == 403


def test_unknown_token_is_401(client: TestClient):
    res = client.get(
        "/tickets",
        headers={"Authorization": "Bearer fake-token"},
    )

    assert res.status_code == 401


def test_assign_then_triaged_transition(client: TestClient):
    created = client.post(
        "/tickets",
        json={"title": "Assigned ticket", "severity": "high"},
        headers={"Authorization": "Bearer admin-token"},
    )

    assert created.status_code == 200

    ticket_id = created.json()["id"]

    assigned = client.post(
        f"/tickets/{ticket_id}/assign",
        json={"assignee": "analyst"},
        headers={"Authorization": "Bearer admin-token"},
    )

    assert assigned.status_code == 200

    transitioned = client.post(
        f"/tickets/{ticket_id}/transition",
        json={"status": "triaged"},
        headers={"Authorization": "Bearer admin-token"},
    )

    assert transitioned.status_code == 200
    assert assigned.json()["assignee"] == "analyst"
    assert transitioned.json()["assignee"] == "analyst"
    assert transitioned.json()["status"] == "triaged"


def test_extra_ticket_fields_are_ignored(client: TestClient):
    res = client.post(
        "/tickets",
        json={
            "title": "Ticket with extra field",
            "severity": "high",
            "unexpected": "ignored",
        },
        headers={"Authorization": "Bearer admin-token"},
    )

    assert res.status_code == 200
    assert res.json()["title"] == "Ticket with extra field"
    assert "unexpected" not in res.json()


def test_invalid_severity_is_400(client: TestClient):
    res = client.post(
        "/tickets",
        json={"title": "Invalid severity", "severity": "urgent"},
        headers={"Authorization": "Bearer admin-token"},
    )

    assert res.status_code == 400


def test_malformed_json_is_rejected(client: TestClient):
    res = client.post(
        "/tickets",
        content='{"title": "Broken JSON", "severity": "high"',
        headers={
            "Authorization": "Bearer admin-token",
            "Content-Type": "application/json",
        },
    )

    assert res.status_code == 422
