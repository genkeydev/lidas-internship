"""FastAPI application — workflow rules loaded from client-spec.json."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from . import db
from .observability import RequestLoggingMiddleware, configure_logging
from .auth import require
from .spec import can_transition

configure_logging()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    conn = db.connect()
    db.init_schema(conn)
    conn.close()
    yield


app = FastAPI(
    title="AlertDesk",
    description="Security alert and ticket intake. Statuses and roles come from client-spec.json.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)


class TicketCreate(BaseModel):
    title: str = Field(min_length=1)
    description: str = ""
    severity: str


class AssignBody(BaseModel):
    assignee: str = Field(min_length=1)


class TransitionBody(BaseModel):
    status: str


def _ticket_row(row: Any) -> dict[str, Any]:
    return dict(row)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/tickets")
def create_ticket(
    body: TicketCreate,
    actor: dict[str, Any] = Depends(require("create")),
) -> dict[str, Any]:
    spec = actor["spec"]
    if body.severity not in spec.get("severities", []):
        raise HTTPException(status_code=400, detail="severity not in client spec")
    status = spec.get("initialStatus", "new")
    conn = db.connect()
    cur = conn.execute(
        """
        INSERT INTO tickets (title, description, severity, status, created_by)
        VALUES (?, ?, ?, ?, ?)
        """,
        (body.title, body.description, body.severity, status, actor["role"]),
    )
    ticket_id = cur.lastrowid
    conn.execute(
        "INSERT INTO audit_events (ticket_id, actor, action, detail) VALUES (?, ?, ?, ?)",
        (ticket_id, actor["role"], "create", body.title),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    conn.close()
    return _ticket_row(row)


@app.get("/tickets")
def list_tickets(actor: dict[str, Any] = Depends(require("list"))) -> list[dict[str, Any]]:
    conn = db.connect()
    rows = conn.execute("SELECT * FROM tickets ORDER BY id").fetchall()
    conn.close()
    return [_ticket_row(r) for r in rows]


@app.get("/tickets/{ticket_id}")
def get_ticket(
    ticket_id: int,
    actor: dict[str, Any] = Depends(require("get")),
) -> dict[str, Any]:
    conn = db.connect()
    row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="not found")
    return _ticket_row(row)


@app.post("/tickets/{ticket_id}/assign")
def assign_ticket(
    ticket_id: int,
    body: AssignBody,
    actor: dict[str, Any] = Depends(require("assign")),
) -> dict[str, Any]:
    conn = db.connect()
    row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="not found")
    conn.execute("UPDATE tickets SET assignee = ? WHERE id = ?", (body.assignee, ticket_id))
    conn.execute(
        "INSERT INTO audit_events (ticket_id, actor, action, detail) VALUES (?, ?, ?, ?)",
        (ticket_id, actor["role"], "assign", body.assignee),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    conn.close()
    return _ticket_row(row)


@app.post("/tickets/{ticket_id}/transition")
def transition_ticket(
    ticket_id: int,
    body: TransitionBody,
    actor: dict[str, Any] = Depends(require("transition")),
) -> dict[str, Any]:
    spec = actor["spec"]
    conn = db.connect()
    row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="not found")
    current = row["status"]
    if not can_transition(spec, current, body.status):
        conn.close()
        raise HTTPException(
            status_code=409,
            detail=f"illegal transition {current} -> {body.status}",
        )
    conn.execute("UPDATE tickets SET status = ? WHERE id = ?", (body.status, ticket_id))
    conn.execute(
        "INSERT INTO audit_events (ticket_id, actor, action, detail) VALUES (?, ?, ?, ?)",
        (ticket_id, actor["role"], "transition", f"{current}->{body.status}"),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    conn.close()
    return _ticket_row(row)
