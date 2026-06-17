"""Blackboard section catalog and write-permission matrix.

Phase 0 — Foundation.

This module is the single source of truth for the canonical section ids
referenced by ``services.blackboard.proposal``, ``store``, and
``coordinator``. Keep the lists here in sync with ``WORKFLOW_ARCHITECTURE_C.md``
§3 (blackboard contents) and §3.5 (write-permission rules).
"""

from __future__ import annotations

from enum import Enum

# Phase 0 only wires CODE_SNAPSHOT and TIMELINE, but the full table is
# declared here so proposals for other sections can be validated immediately.


class SectionName(str, Enum):
    """Canonical blackboard section ids.

    Order roughly matches the data-flow story in
    ``WORKFLOW_ARCHITECTURE_C.md``: inputs first, working memory in the
    middle, mentor-facing outputs last.
    """

    PROBLEM_CONTEXT = "problem_context"
    USER_PROFILE = "user_profile"
    CODE_SNAPSHOT = "code_snapshot"
    TIMELINE = "timeline"
    STUCK_HYPOTHESES = "stuck_hypotheses"
    OPEN_QUESTIONS_FOR_USER = "open_questions_for_user"
    LEARNING_PLAN_DRAFT = "learning_plan_draft"


WRITE_PERMISSIONS: dict[SectionName, set[str]] = {
    SectionName.PROBLEM_CONTEXT: {"system"},
    SectionName.USER_PROFILE: {"system", "user"},
    SectionName.CODE_SNAPSHOT: {"user", "system"},
    SectionName.TIMELINE: {"system", "analyzer", "mentor", "reflection", "planner"},
    SectionName.STUCK_HYPOTHESES: {"analyzer"},
    SectionName.OPEN_QUESTIONS_FOR_USER: {"mentor"},
    SectionName.LEARNING_PLAN_DRAFT: {"planner"},
}


READ_PERMISSIONS: dict[SectionName, set[str]] = {
    SectionName.PROBLEM_CONTEXT: {
        "system",
        "analyzer",
        "mentor",
        "reflection",
        "planner",
    },
    SectionName.USER_PROFILE: {
        "system",
        "analyzer",
        "mentor",
        "reflection",
        "planner",
    },
    # Default for everything not listed: all agents may read.
}


def get_writer(section: SectionName) -> str:
    """Return a representative writer name for ``section``.

    Phase 0: picks the lexicographically smallest entry from
    ``WRITE_PERMISSIONS[section]`` so the choice is deterministic across runs
    (the values are sets, so direct indexing is not possible).
    Used by the coordinator when logging which agent "owns" a section.
    """
    return sorted(WRITE_PERMISSIONS[section])[0]
