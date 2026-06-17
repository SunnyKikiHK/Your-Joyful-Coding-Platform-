"""Blackboard store tests — Phase 0 prototypes.

Each test is wired up with fixtures and assertions spelled out in the
docstring, but the body just tags ``# TODO: Phase 0 — implement`` so it's
obvious where the assertion goes. Replace the body when implementing.
"""
from __future__ import annotations

import pytest

from src.services.blackboard import BlackboardStore, SectionName, VersionConflict


@pytest.fixture
def store(db_session):
    """Provide a ``BlackboardStore`` bound to a per-test DB session."""
    # TODO: Phase 0 — implement fixture body
    raise NotImplementedError("Phase 0 prototype — implement store fixture")


def test_round_trip(store: BlackboardStore) -> None:
    """``commit`` then ``read`` returns the same payload and version=1.

    Steps (implement in body):
        1. await store.commit(session_id=..., section=SectionName.CODE_SNAPSHOT,
                              expected_version=0, payload={"code": "x"},
                              agent="user")
        2. payload, version = await store.read(session_id, SectionName.CODE_SNAPSHOT)
        3. assert payload == {"code": "x"} and version == 1
    """
    # TODO: Phase 0 — implement
    raise NotImplementedError("Phase 0 prototype — implement test_round_trip")


def test_version_conflict(store: BlackboardStore) -> None:
    """Two concurrent ``commit``s with the same ``expected_version`` — exactly one wins.

    Steps (implement in body):
        1. First commit succeeds (expected_version=0 → returns 1).
        2. Second commit with expected_version=0 raises ``VersionConflict``.
    """
    # TODO: Phase 0 — implement
    raise NotImplementedError("Phase 0 prototype — implement test_version_conflict")


def test_event_log_appended(store: BlackboardStore) -> None:
    """Every commit produces a ``TimelineEvent`` row.

    Steps (implement in body):
        1. Commit once.
        2. Query the timeline table for that session.
        3. Assert at least one row exists with ``kind == "commit"``.
    """
    # TODO: Phase 0 — implement
    raise NotImplementedError("Phase 0 prototype — implement test_event_log_appended")