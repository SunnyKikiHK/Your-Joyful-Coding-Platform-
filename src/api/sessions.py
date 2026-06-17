"""Session REST endpoints — Phase 0.

These endpoints open / fetch / close a coding session. They are the HTTP
boundary of the blackboard; everything past ``POST /sessions`` is async, but
the endpoints themselves are sync FastAPI handlers that take a ``Session``
dependency, matching the style of ``api/auth.py``.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.database import get_db

router = APIRouter(prefix="/sessions", tags=["Sessions"])


# Phase 0 leaves the Pydantic models as plain TODOs. The concrete fields are
# spelled out in the docstring of each endpoint so it's obvious what to add
# when the body is implemented.


@router.post("", status_code=status.HTTP_201_CREATED)
def create_session(
    # user_id: int, problem_id: str
    db: Session = Depends(get_db),
):
    """Open a new coding session.

    Request body (Phase 0): ``{"user_id": int, "problem_id": str}``.
    Response body (Phase 0): ``{"session_id": int, "status": "active"}``.
    """
    # TODO: Phase 0 — implement
    raise NotImplementedError("Phase 0 prototype — implement create_session")


@router.get("/{session_id}")
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
):
    """Return the session row plus the full blackboard snapshot.

    Response body (Phase 0): ``{"session": {...}, "blackboard": {section: payload}}``.
    """
    # TODO: Phase 0 — implement
    raise NotImplementedError("Phase 0 prototype — implement get_session")


@router.post("/{session_id}/close")
def close_session(
    session_id: int,
    db: Session = Depends(get_db),
):
    """Mark the session ended. Triggers ``Planner`` in Phase 3.

    Phase 0: just sets ``ended_at`` and ``status = "closed"``. No payload
    beyond the updated session row.
    """
    # TODO: Phase 0 — implement
    raise NotImplementedError("Phase 0 prototype — implement close_session")