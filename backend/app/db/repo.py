"""Repository functions: the only place that talks to the ORM.

Each function takes an :class:`AsyncSession` so callers control the transaction
boundary (the bot uses :meth:`Database.session`; the API uses a request-scoped
session). Keeping queries here makes them reusable across the bot and the API
and easy to unit-test.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from .models import AppSetting, DailyUsage, Message, Payment, User

# Keys for the app_settings key-value table.
SYSTEM_PROMPT_KEY = "system_prompt"
VOICE_ENABLED_KEY = "voice_enabled"
DISABLED_MODELS_KEY = "disabled_models"
PROVIDERS_KEY = "providers"
TIERS_KEY = "tiers"
USER_ROLES_KEY = "user_roles_enabled"


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _today() -> dt.date:
    return _utcnow().date()


# -- users -------------------------------------------------------------------


async def get_or_create_user(
    session: AsyncSession,
    user_id: int,
    *,
    username: str | None = None,
    first_name: str | None = None,
) -> User:
    user = await session.get(User, user_id)
    if user is None:
        user = User(id=user_id, username=username, first_name=first_name)
        session.add(user)
        await session.flush()
        return user
    # Keep profile fields fresh on each interaction.
    if username is not None and username != user.username:
        user.username = username
    if first_name is not None and first_name != user.first_name:
        user.first_name = first_name
    return user


async def get_user(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


async def set_preferred_model(
    session: AsyncSession, user_id: int, model: str | None
) -> None:
    user = await get_or_create_user(session, user_id)
    user.preferred_model = model


async def set_role(session: AsyncSession, user_id: int, role: str | None) -> None:
    user = await get_or_create_user(session, user_id)
    user.role = role


async def set_tier(
    session: AsyncSession, user_id: int, tier_key: str, until: dt.datetime | None
) -> None:
    """Put a user on a tier (any key) until ``until`` (None = no expiry)."""
    user = await get_or_create_user(session, user_id)
    user.tier = tier_key
    user.premium_until = until


# -- usage / limits ----------------------------------------------------------


async def used_today(session: AsyncSession, user_id: int) -> int:
    row = await session.get(DailyUsage, (user_id, _today()))
    return row.count if row else 0


async def consume_quota(session: AsyncSession, user_id: int) -> int:
    """Atomically increment today's counter; returns the new count.

    Uses a Postgres UPSERT so concurrent messages can't lose an increment.
    """
    today = _today()
    stmt = (
        pg_insert(DailyUsage)
        .values(user_id=user_id, day=today, count=1)
        .on_conflict_do_update(
            index_elements=[DailyUsage.user_id, DailyUsage.day],
            set_={"count": DailyUsage.count + 1},
        )
        .returning(DailyUsage.count)
    )
    result = await session.execute(stmt)
    return int(result.scalar_one())


async def usage_series(
    session: AsyncSession, user_id: int, days: int
) -> list[dict[str, object]]:
    """Daily message counts for the last ``days`` days (zero-filled, oldest→newest)."""
    days = max(1, min(days, 90))
    start = _today() - dt.timedelta(days=days - 1)
    rows = await session.execute(
        select(DailyUsage.day, DailyUsage.count)
        .where(DailyUsage.user_id == user_id, DailyUsage.day >= start)
    )
    counts = {day: count for day, count in rows.all()}
    series: list[dict[str, object]] = []
    for i in range(days):
        day = start + dt.timedelta(days=i)
        series.append({"day": day.isoformat(), "count": int(counts.get(day, 0))})
    return series


# -- history (short-term window) + activity feed -----------------------------


async def add_message(
    session: AsyncSession,
    user_id: int,
    role: str,
    content: str,
    *,
    model: str | None = None,
) -> None:
    session.add(
        Message(user_id=user_id, role=role, content=content, model=model)
    )


async def recent_history(
    session: AsyncSession, user_id: int, turns: int
) -> list[dict[str, str]]:
    """Most-recent messages as a prompt window (oldest→newest)."""
    rows = await session.execute(
        select(Message.role, Message.content)
        .where(Message.user_id == user_id)
        .order_by(Message.id.desc())
        .limit(turns * 2)
    )
    items = rows.all()
    return [{"role": r, "content": c} for r, c in reversed(items)]


async def activity(
    session: AsyncSession, user_id: int, limit: int
) -> list[Message]:
    limit = max(1, min(limit, 100))
    rows = await session.execute(
        select(Message)
        .where(Message.user_id == user_id)
        .order_by(Message.id.desc())
        .limit(limit)
    )
    return list(rows.scalars().all())


async def clear_history(session: AsyncSession, user_id: int) -> None:
    await session.execute(delete(Message).where(Message.user_id == user_id))


async def message_count(session: AsyncSession, user_id: int) -> int:
    return int(
        await session.scalar(
            select(func.count()).select_from(Message).where(Message.user_id == user_id)
        )
        or 0
    )


# -- payments ----------------------------------------------------------------


async def record_payment(
    session: AsyncSession, charge_id: str, user_id: int, amount_stars: int
) -> None:
    stmt = (
        pg_insert(Payment)
        .values(charge_id=charge_id, user_id=user_id, amount_stars=amount_stars)
        .on_conflict_do_nothing(index_elements=[Payment.charge_id])
    )
    await session.execute(stmt)


async def payment_count(session: AsyncSession, user_id: int) -> int:
    return int(
        await session.scalar(
            select(func.count()).select_from(Payment).where(Payment.user_id == user_id)
        )
        or 0
    )


# -- admin / global stats ----------------------------------------------------


async def global_stats(session: AsyncSession) -> dict[str, int]:
    total_users = await session.scalar(select(func.count()).select_from(User)) or 0
    premium = (
        await session.scalar(
            select(func.count()).select_from(User).where(User.tier == "premium")
        )
        or 0
    )
    msgs_today = (
        await session.scalar(
            select(func.coalesce(func.sum(DailyUsage.count), 0)).where(
                DailyUsage.day == _today()
            )
        )
        or 0
    )
    payments = await session.scalar(select(func.count()).select_from(Payment)) or 0
    return {
        "users": int(total_users),
        "premium": int(premium),
        "messages_today": int(msgs_today),
        "payments": int(payments),
    }


async def recent_users(session: AsyncSession, limit: int = 10) -> list[User]:
    rows = await session.execute(
        select(User).order_by(User.created_at.desc()).limit(limit)
    )
    return list(rows.scalars().all())


# -- admin user management ---------------------------------------------------


async def list_users(
    session: AsyncSession,
    *,
    search: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[User], int]:
    limit = max(1, min(limit, 100))
    base = select(User)
    count_q = select(func.count()).select_from(User)
    if search and search.strip():
        s = search.strip()
        cond = User.username.ilike(f"%{s}%") | User.first_name.ilike(f"%{s}%")
        if s.lstrip("-").isdigit():
            cond = cond | (User.id == int(s))
        base = base.where(cond)
        count_q = count_q.where(cond)
    total = int(await session.scalar(count_q) or 0)
    rows = await session.execute(
        base.order_by(User.created_at.desc()).limit(limit).offset(max(0, offset))
    )
    return list(rows.scalars().all()), total


async def set_banned(session: AsyncSession, user_id: int, banned: bool) -> None:
    user = await get_or_create_user(session, user_id)
    user.banned = banned


async def set_limit_override(
    session: AsyncSession, user_id: int, value: int | None
) -> None:
    user = await get_or_create_user(session, user_id)
    user.limit_override = value if (value is None or value >= 0) else None


async def reset_today_usage(session: AsyncSession, user_id: int) -> None:
    await session.execute(
        delete(DailyUsage).where(
            DailyUsage.user_id == user_id, DailyUsage.day == _today()
        )
    )


# -- app settings (key-value) ------------------------------------------------


async def get_setting(session: AsyncSession, key: str) -> str | None:
    row = await session.get(AppSetting, key)
    return row.value if row else None


async def set_setting(session: AsyncSession, key: str, value: str) -> None:
    stmt = (
        pg_insert(AppSetting)
        .values(key=key, value=value)
        .on_conflict_do_update(
            index_elements=[AppSetting.key], set_={"value": value}
        )
    )
    await session.execute(stmt)


async def get_system_prompt(session: AsyncSession, default: str) -> str:
    """The operator-set system prompt, or ``default`` when none is stored."""
    stored = await get_setting(session, SYSTEM_PROMPT_KEY)
    return stored if stored and stored.strip() else default


async def set_system_prompt(session: AsyncSession, prompt: str) -> None:
    await set_setting(session, SYSTEM_PROMPT_KEY, prompt)
