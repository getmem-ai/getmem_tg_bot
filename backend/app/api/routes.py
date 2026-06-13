"""Mini App API routes.

All ``/me*`` routes are scoped to the authenticated Telegram user (from a
validated ``initData`` header); ``/admin/*`` additionally requires the caller to
be in ``ADMIN_IDS``.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..db import repo
from .auth import TelegramUser
from .deps import current_user, db_session, get_settings, require_admin
from .schemas import (
    ActivityItem,
    ActivityOut,
    AdminStatsOut,
    HealthOut,
    MeOut,
    PromptIn,
    PromptOut,
    RecentUser,
    TotalsOut,
    UsageOut,
    UsagePoint,
    UsageSeriesOut,
    UserOut,
)

router = APIRouter()


@router.get("/health", response_model=HealthOut)
async def health() -> HealthOut:
    return HealthOut(status="ok")


@router.get("/me", response_model=MeOut)
async def me(
    user: TelegramUser = Depends(current_user),
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(db_session),
) -> MeOut:
    db_user = await repo.get_or_create_user(
        session, user.id, username=user.username, first_name=user.first_name
    )
    limit = settings.daily_limit_for(db_user.is_premium)
    used = await repo.used_today(session, user.id)
    messages = await repo.message_count(session, user.id)
    payments = await repo.payment_count(session, user.id)
    return MeOut(
        user=UserOut(
            id=db_user.id,
            username=db_user.username,
            first_name=db_user.first_name,
            tier=db_user.tier,
            is_premium=db_user.is_premium,
            premium_until=db_user.premium_until,
            preferred_model=db_user.preferred_model,
            created_at=db_user.created_at,
        ),
        usage=UsageOut(
            used_today=used, limit=limit, remaining=max(0, limit - used)
        ),
        totals=TotalsOut(messages=messages, payments=payments),
        is_admin=settings.is_admin(user.id),
    )


@router.get("/me/activity", response_model=ActivityOut)
async def my_activity(
    limit: int = Query(default=20, ge=1, le=100),
    user: TelegramUser = Depends(current_user),
    session: AsyncSession = Depends(db_session),
) -> ActivityOut:
    rows = await repo.activity(session, user.id, limit)
    return ActivityOut(
        items=[
            ActivityItem(
                role=m.role,
                content=m.content,
                model=m.model,
                created_at=m.created_at,
            )
            for m in rows
        ]
    )


@router.get("/me/usage", response_model=UsageSeriesOut)
async def my_usage(
    days: int = Query(default=14, ge=1, le=90),
    user: TelegramUser = Depends(current_user),
    session: AsyncSession = Depends(db_session),
) -> UsageSeriesOut:
    series = await repo.usage_series(session, user.id, days)
    return UsageSeriesOut(
        series=[UsagePoint(day=str(p["day"]), count=int(p["count"])) for p in series]
    )


@router.get("/admin/prompt", response_model=PromptOut)
async def get_prompt(
    _admin: TelegramUser = Depends(require_admin),
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(db_session),
) -> PromptOut:
    stored = await repo.get_setting(session, repo.SYSTEM_PROMPT_KEY)
    return PromptOut(
        system_prompt=stored or settings.system_prompt,
        is_default=stored is None,
    )


@router.put("/admin/prompt", response_model=PromptOut)
async def set_prompt(
    body: PromptIn,
    _admin: TelegramUser = Depends(require_admin),
    session: AsyncSession = Depends(db_session),
) -> PromptOut:
    prompt = body.system_prompt.strip()
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="system_prompt must not be empty",
        )
    await repo.set_system_prompt(session, prompt)
    return PromptOut(system_prompt=prompt, is_default=False)


@router.get("/admin/stats", response_model=AdminStatsOut)
async def admin_stats(
    _admin: TelegramUser = Depends(require_admin),
    session: AsyncSession = Depends(db_session),
) -> AdminStatsOut:
    stats = await repo.global_stats(session)
    users = await repo.recent_users(session, limit=10)
    return AdminStatsOut(
        users=stats["users"],
        premium=stats["premium"],
        messages_today=stats["messages_today"],
        payments=stats["payments"],
        recent_users=[
            RecentUser(
                id=u.id,
                first_name=u.first_name,
                username=u.username,
                tier=u.tier,
                created_at=u.created_at,
            )
            for u in users
        ],
    )
