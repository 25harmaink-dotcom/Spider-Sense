from datetime import datetime, timezone

from sqlalchemy import String, Text, Float, ForeignKey, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# ---------------- USER MODEL ----------------

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )


# ---------------- INCIDENT MODEL ----------------

class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True)

    citizen_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    hero_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    severity: Mapped[int] = mapped_column(
          Integer,
          nullable=False
    )

    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="reported",
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )


# ---------------- STATUS HISTORY MODEL ----------------

class StatusHistory(Base):
    __tablename__ = "status_history"

    id: Mapped[int] = mapped_column(primary_key=True)

    incident_id: Mapped[int] = mapped_column(
        ForeignKey("incidents.id"),
        nullable=False
    )

    actor_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    previous_status: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    next_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Cryptographic audit fields

    previous_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True
    )

    event_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True
    )

    event_hmac: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True
    )