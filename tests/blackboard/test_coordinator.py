"""Coordinator tests — Phase 0 prototypes.

These tests target the state machine and token-grant logic. Bodies are TODOs;
docstrings spell out the assertions so implementation is mechanical.
"""
from __future__ import annotations

import pytest

from src.services.blackboard import BlackboardStore, Coordinator, Proposal


@pytest.fixture
def coordinator(db_session):
    """Provide a ``Coordinator`` bound to a per-test DB session."""
    # TODO: Phase 0 — implement fixture body
    raise NotImplementedError("Phase 0 prototype — implement coordinator fixture")


def test_submit_accepts_valid_proposal(coordinator: Coordinator) -> None:
    """A proposal from an authorized agent with a fresh base_version is committed.

    Steps (implement in body):
        1. Build a ``Proposal(from_agent="user", section=SectionName.CODE_SNAPSHOT,
           base_version=0, operation=ProposalOperation.UPSERT, ...)``.
        2. decision = await coordinator.submit(proposal)
        3. assert decision.accepted is True and decision.version == 1
    """
    # TODO: Phase 0 — implement
    raise NotImplementedError("Phase 0 prototype — implement test_submit_accepts_valid_proposal")


def test_submit_rejects_unauthorized_agent(coordinator: Coordinator) -> None:
    """A proposal whose ``from_agent`` is not in ``WRITE_PERMISSIONS[section]`` is rejected.

    Steps (implement in body):
        1. Build a proposal from ``from_agent="mentor"`` writing
           ``STUCK_HYPOTHESES`` (only ``analyzer`` may write that section).
        2. decision = await coordinator.submit(proposal)
        3. assert decision.accepted is False and "permission" in decision.reason.lower()
    """
    # TODO: Phase 0 — implement
    raise NotImplementedError("Phase 0 prototype — implement test_submit_rejects_unauthorized_agent")


def test_request_speaking_token_respects_priority(coordinator: Coordinator) -> None:
    """P0 tokens are granted before P5 tokens when both are pending.

    Steps (implement in body):
        1. Enqueue a P5 request, then a P0 request.
        2. token = await coordinator.request_speaking_token("mentor", priority=0)
        3. assert token.priority == 0
    """
    # TODO: Phase 0 — implement
    raise NotImplementedError("Phase 0 prototype — implement test_request_speaking_token_respects_priority")


def test_p3_throttling_90_seconds(coordinator: Coordinator) -> None:
    """Two P3 tokens within 90s — the second is suppressed.

    Steps (implement in body):
        1. First P3 token granted.
        2. Immediately request another P3 token.
        3. assert the second request returns ``None`` (or raises ``TokenSuppressed``).
    """
    # TODO: Phase 0 — implement
    raise NotImplementedError("Phase 0 prototype — implement test_p3_throttling_90_seconds")