"""Mentor agent — Phase 0 trivial echo.

Phase 0 — Foundation.

The Phase 0 mentor is intentionally dumb: when it gets a speaking token, it
just echoes the user's text wrapped in ``"Echo: "``. Phase 1 replaces this
with a real drafting pipeline that reads ``stuck_hypotheses`` and produces
Socratic questions.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..blackboard.coordinator import Coordinator, Token


@dataclass
class MentorMessage:
    """One outbound message from the mentor to the user."""

    text: str
    session_id: int
    proposal_id: str | None = None  # set when the message has been committed


class Mentor:
    """Trivial Phase 0 mentor.

    Holds a handle to the ``Coordinator``. The Phase 1 version will additionally
    own an ``LLMClient`` (see ``services.llm.client``).
    """

    def __init__(self, coordinator: Coordinator) -> None:
        self._coordinator = coordinator

    async def on_token_granted(self, token: Token) -> None:
        """Called by the coordinator when the mentor gets the floor.

        Phase 0: read the user's latest message from the timeline and submit
        an echo proposal to ``OPEN_QUESTIONS_FOR_USER``.
        """
        # TODO: Phase 0 — implement
        raise NotImplementedError("Phase 0 prototype — implement on_token_granted")

    async def draft(self, proposal) -> MentorMessage:
        """Build a ``MentorMessage`` proposal for the coordinator to commit.

        Phase 0: ``proposal`` will be the raw user message; the returned
        ``MentorMessage`` should wrap it in ``"Echo: ..."``.
        """
        # TODO: Phase 0 — implement
        raise NotImplementedError("Phase 0 prototype — implement draft")

    async def _echo(self, user_message: str) -> str:
        """Phase 0 placeholder.

        Returns the user text wrapped in ``"Echo: "``. Replaced in Phase 1.
        """
        # TODO: Phase 0 — implement
        raise NotImplementedError("Phase 0 prototype — implement _echo")