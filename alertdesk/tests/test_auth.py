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

@pytest.mark.skip(reason="Week 3 — implement unknown bearer token")
def test_unknown_token_is_401():
    pass
 