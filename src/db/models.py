"""SQLAlchemy ORM models for the Joyful Coding Platform.

Defines the persistent state for users, coding sessions, the blackboard
section payloads, and the append-only timeline event log.

Style notes:
    Inherits from the legacy ``declarative_base()`` in ``db.database`` to stay
    consistent with the existing skeleton. New tables use SQLAlchemy 2.0-style
    ``Mapped[...]`` annotations where the migration to ``DeclarativeBase`` is
    straightforward, but we keep the shared ``Base`` import point so existing
    code (e.g. ``models.Base.metadata.create_all``) keeps working.
"""
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    """Application user account."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    is_active = Column(Boolean, default=True)
    problems_solved = Column(Integer, default=0)


class CodingSession(Base):
    """A single coding-attempt session for a user against a problem.

    Named ``CodingSession`` (not ``Session``) to avoid shadowing the
    SQLAlchemy ``Session`` type imported throughout the codebase.
    """

    __tablename__ = "coding_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    problem_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        Enum("active", "closed", name="coding_session_status"),
        default="active",
        nullable=False,
        index=True,
    )

    sections: Mapped[list["BlackboardSection"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )
    events: Mapped[list["TimelineEvent"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="TimelineEvent.ts",
    )


class BlackboardSection(Base):
    """One blackboard region for a coding session.

    Stores a JSONB ``payload`` (or ``JSON`` on SQLite for local dev) plus a
    monotonic ``version`` for optimistic concurrency control in
    ``BlackboardStore.commit``.
    """

    __tablename__ = "blackboard_sections"
    __table_args__ = (
        # One row per (session, section) — the store relies on this.
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("coding_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    section_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload: Mapped[Any] = mapped_column(JSON, nullable=False, default=dict)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    session: Mapped[CodingSession] = relationship(back_populates="sections")


class TimelineEvent(Base):
    """Append-only event log row.

    Every state-changing event in the system must land here per
    ``project-structure.mdc`` §8. Never update or delete a row.
    """

    __tablename__ = "timeline_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("coding_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload: Mapped[Any] = mapped_column(JSON, nullable=False, default=dict)
    agent: Mapped[str | None] = mapped_column(String(64), nullable=True)
    proposal_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    session: Mapped[CodingSession] = relationship(back_populates="events")
