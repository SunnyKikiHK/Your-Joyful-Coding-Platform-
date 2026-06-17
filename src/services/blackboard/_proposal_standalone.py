"""Proposal envelope and validation.

Phase 0 — Foundation.

A ``Proposal`` is the only way an agent may write to the blackboard. The
coordinator validates write permission, then forwards the proposal to
``BlackboardStore.commit`` for optimistic-concurrency check + write.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from blackboard_pkg.sections import WRITE_PERMISSIONS, SectionName


class ProposalOperation(str, Enum):
    """How a proposal mutates its target section.

    - ``upsert``: replace the section payload with ``payload``.
    - ``append``: append ``payload`` to a list-shaped payload (or merge into a
      dict-shaped payload, depending on the section).
    - ``delete``: remove an entry identified by ``payload['key']``.
    """

    UPSERT = "upsert"
    APPEND = "append"
    DELETE = "delete"


class Proposal(BaseModel):
    """A write request from one agent to one blackboard section.

    Fields match the BUILD_PLAN.md Phase 0 description for ``Proposal``:
    proposal_id, session_id, from_agent, section, base_version, operation,
    payload, rationale, requires_speaking.
    """

    proposal_id: str
    session_id: int
    from_agent: str
    section: SectionName
    base_version: int = Field(..., ge=0)
    operation: ProposalOperation
    payload: dict[str, Any]
    rationale: str
    requires_speaking: bool = False


def validate(
    proposal: Proposal, write_perms: dict[SectionName, set[str]] | None = None
) -> None:
    """Raise ``PermissionError`` if ``proposal.from_agent`` cannot write to ``section``.

    Phase 0: no implementation yet — the body just tags where the check goes.
    """
    if write_perms is None:
        write_perms = WRITE_PERMISSIONS
    if proposal.from_agent not in write_perms[proposal.section]:
        raise PermissionError(
            f"{proposal.from_agent} does not have permission to write to {proposal.section}"
        )


def to_envelope(proposal: Proposal) -> dict:
    """Serialize ``proposal`` for the timeline event log.

    Returns a JSON-safe dict using the field names declared on ``Proposal``.
    Enum-typed fields (``section``, ``operation``) are emitted as their string
    values so the row can be stored directly in a ``JSON`` column and replayed
    later by ``ReplaySimulator``.
    """
    return proposal.model_dump(mode="json")
