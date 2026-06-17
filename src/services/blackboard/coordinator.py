"""Coordinator — the heart of the system.

Phase 0 — Foundation.

The coordinator owns the speaking-token state machine and is the only path
agents use to write to the blackboard. See ``WORKFLOW_ARCHITECTURE_C.md`` §3.5
for the priority levels and throttling rules.
"""
from __future__ import annotations

from typing import Any

from .proposal import Proposal
from .store import BlackboardStore


class Decision:
    """Result of ``Coordinator.submit``.

    Attributes:
        accepted: ``True`` if the proposal was committed.
        version: New version number if accepted, else ``None``.
        reason: Human-readable rejection reason if not accepted.
    """

    accepted: bool
    version: int | None
    reason: str | None


class Token:
    """A speaking token handed to one agent.

    Attributes:
        agent: The agent that received the token.
        priority: P0–P5 priority (see ``WORKFLOW_ARCHITECTURE_C.md`` §3.5).
        granted_at: Unix timestamp the token was issued.
        expires_at: Unix timestamp after which the token is stale.
    """

    agent: str
    priority: int
    granted_at: float
    expires_at: float


class Coordinator:
    """State machine + speaking-token dispatcher.

    Holds a single ``BlackboardStore`` instance plus in-memory token state.
    There is one ``Coordinator`` per process (FastAPI app).
    """

    def __init__(self, store: BlackboardStore) -> None:
        self._store = store

    async def submit(self, proposal: Proposal) -> Decision:
        """Validate permission → check version → commit (or reject).

        This is the single entry point for any agent that wants to write the
        blackboard.
        """
        # TODO: Phase 0 — implement
        raise NotImplementedError("Phase 0 prototype — implement submit")

    async def request_speaking_token(self, agent: str, priority: int) -> Token:
        """Hand out a speaking token honoring P0–P5 ordering and 90s throttling.

        Returns ``None`` (or raises) if the token is currently suppressed (see
        ``_should_suppress_p3``).
        """
        # TODO: Phase 0 — implement
        raise NotImplementedError("Phase 0 prototype — implement request_speaking_token")

    async def on_event(self, event: dict) -> None:
        """Central event hook called by the WS endpoint.

        Phase 0: only updates the idle tracker. Phase 1 wires this to the
        analyzer's idle-tick path.
        """
        # TODO: Phase 0 — implement
        raise NotImplementedError("Phase 0 prototype — implement on_event")

    def _decide_priority(self, proposal: Proposal) -> int:
        """Map a ``Proposal`` to a P0–P5 priority.

        Phase 0: trivial mapping — only ``OPEN_QUESTIONS_FOR_USER`` becomes a
        proactive P3; everything else is P5 (logging only).
        """
        # TODO: Phase 0 — implement
        raise NotImplementedError("Phase 0 prototype — implement _decide_priority")

    def _should_suppress_p3(self) -> bool:
        """Implement the P3 suppression rules from §3.5.

        Returns ``True`` if a proactive mentor message should be dropped right
        now (e.g. the user just passed a test, or another mentor message went
        out less than 90 seconds ago).
        """
        # TODO: Phase 0 — implement
        raise NotImplementedError("Phase 0 prototype — implement _should_suppress_p3")