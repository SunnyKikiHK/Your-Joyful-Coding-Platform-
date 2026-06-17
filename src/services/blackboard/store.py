"""Postgres JSONB-backed blackboard store with optimistic concurrency.

Phase 0 — Foundation.

The store is the only writer to the ``blackboard_sections`` and
``timeline_events`` tables. Agents never touch the DB directly; they submit
``Proposal`` objects to ``Coordinator.submit`` which calls ``BlackboardStore``.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from .sections import SectionName


class VersionConflict(Exception):
    """Raised by ``BlackboardStore.commit`` when ``expected_version`` is stale."""


class BlackboardStore:
    """Owns reads and writes to ``blackboard_sections`` + ``timeline_events``.

    Phase 0: only ``CODE_SNAPSHOT`` and ``TIMELINE`` are exercised; the others
    are still wired through this class so Phase 1+ don't need a refactor.
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    async def read(self, session_id: int, section: SectionName) -> tuple[Any, int]:
        """Return ``(payload, version)`` for ``(session_id, section)``.

        Phase 0: must hit Postgres JSONB row; on SQLite for local dev the same
        JSON column is used. Returns ``(default_payload, 0)`` if the row does
        not exist yet.
        """
        # TODO: Phase 0 — implement
        sql = text(
            """
            SELECT payload, version 
            FROM blackboard_sections 
            WHERE session_id = :session_id AND section_name = :section
            """
        )
        result = self._db.execute(
            sql, session_id=session_id, section=section
        ).fetchone()
        if result is None:
            return {}, 0
        return result[0], result[1]

    async def get_section_versions(self, session_id: int) -> dict[SectionName, int]:
        """Return a `{section: version}`` map for the whole session.

        Used by observability (Phase 4) and tests in Phase 0.
        """
        # TODO: Phase 0 — implement
        sql = text(
            """
            SELECT section_name, version 
            FROM blackboard_sections 
            WHERE session_id = :session_id
        """
        )
        result = self._db.execute(sql, session_id=session_id).fetchall()
        return {section_name: version for section_name, version in result}

    async def commit(
        self,
        session_id: int,
        section: SectionName,
        expected_version: int,
        payload: Any,
        agent: str,
    ) -> int:
        """Optimistic CAS write; bumps ``version``; returns the new version.

        Raises ``VersionConflict`` if the on-disk version does not match
        ``expected_version``. Every successful commit must also append a
        ``TimelineEvent`` row.
        """
        # TODO: Phase 0 — implement
        sql = text(
            """
            UPDATE blackboard_sections 
            SET payload = :payload, version = version + 1 
            WHERE session_id = :session_id AND section_name = :section AND version = :expected_version
        """
        )
        result = self._db.execute(
            sql,
            session_id=session_id,
            section=section,
            expected_version=expected_version,
            payload=payload,
        )
        if result.rowcount == 0:
            raise VersionConflict
        return result.rowcount

    async def append_event(self, event: dict) -> None:
        """Append-only insert into ``timeline_events``.

        Called by ``commit`` and by the coordinator when a non-write event
        (e.g. ``speaking_token_granted``) happens.
        """
        # TODO: Phase 0 — implement
        return
