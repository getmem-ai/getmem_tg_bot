"""ORM models.

Only operational state lives here — long-term *memory* is owned by the GetMem
service, not this database. Tables:

* ``users``        — tier, preferred model, premium expiry.
* ``messages``     — rolling chat log (short-term window + Mini App activity feed).
* ``daily_usage``  — per-user per-day message counters (limits + usage charts).
* ``payments``     — Telegram Stars purchases (idempotent by charge id).
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    false as sa_false,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class User(Base):
    __tablename__ = "users"

    # Telegram user id is the natural primary key.
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tier: Mapped[str] = mapped_column(String(16), default="free", server_default="free")
    preferred_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # Optional user-defined role appended to the system instructions for this
    # user's chats (e.g. "You are my English teacher"). Admin-gateable.
    role: Mapped[str | None] = mapped_column(Text, nullable=True)
    premium_until: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Admin moderation: blocked users get no replies; limit_override replaces the
    # tier's daily limit for this user when set.
    banned: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=sa_false()
    )
    limit_override: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now()
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        server_default=func.now(),
        onupdate=_utcnow,
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def is_premium(self) -> bool:
        """True when the user is on an active *paid* tier (anything but free)."""
        if not self.tier or self.tier == "free":
            return False
        if self.premium_until is None:
            return True
        until = self.premium_until
        if until.tzinfo is None:
            until = until.replace(tzinfo=dt.timezone.utc)
        return until > _utcnow()


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(16))  # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now(), index=True
    )

    user: Mapped[User] = relationship(back_populates="messages")


class DailyUsage(Base):
    __tablename__ = "daily_usage"

    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    day: Mapped[dt.date] = mapped_column(Date, primary_key=True)
    count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class AppSetting(Base):
    """Key-value store for operator-editable settings (e.g. the system prompt).

    Kept out of ``.env`` so long, frequently-tuned values can be changed live
    from the bot or the Mini App without a redeploy.
    """

    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        server_default=func.now(),
        onupdate=_utcnow,
    )


class Payment(Base):
    __tablename__ = "payments"

    charge_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    amount_stars: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, server_default=func.now()
    )
