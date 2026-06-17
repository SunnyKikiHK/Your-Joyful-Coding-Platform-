"""Blackboard package — Phase 0 exports.

Anything imported from ``src.services.blackboard`` should come through here so
callers don't need to know the internal module layout.
"""
from .coordinator import Coordinator, Decision, Token
from .proposal import Proposal, ProposalOperation, validate, to_envelope
from .sections import (
    READ_PERMISSIONS,
    WRITE_PERMISSIONS,
    SectionName,
    get_writer,
)
from .store import BlackboardStore, VersionConflict

__all__ = [
    "READ_PERMISSIONS",
    "WRITE_PERMISSIONS",
    "BlackboardStore",
    "Coordinator",
    "Decision",
    "Proposal",
    "ProposalOperation",
    "SectionName",
    "Token",
    "VersionConflict",
    "get_writer",
    "to_envelope",
    "validate",
]