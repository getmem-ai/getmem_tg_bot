"""Mini App API routes.

All ``/me*`` routes are scoped to the authenticated Telegram user (from a
validated ``initData`` header); ``/admin/*`` additionally requires the caller to
be in ``ADMIN_IDS``. Editable config is read/written via the ConfigStore.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..core import ConfigStore
from ..core.config_store import ModelSpec
from ..db import repo
from .auth import TelegramUser
from .deps import (
    current_user,
    db_session,
    get_bot,
    get_config,
    get_settings,
    require_admin,
)
from .schemas import (
    ActivityItem,
    ActivityOut,
    AdminStatsOut,
    AdminUser,
    AdminUsersOut,
    AdminUserUpdate,
    AnalyticsOut,
    BroadcastIn,
    BroadcastOut,
    DayCount,
    HealthOut,
    ModelCount,
    InvoiceIn,
    InvoiceOut,
    MeOut,
    ModelSpecOut,
    PromptIn,
    PromptOut,
    RoleIn,
    RoleOut,
    ProviderIn,
    ProviderOut,
    ProvidersOut,
    RecentUser,
    RuntimeIn,
    RuntimeOut,
    SetModelIn,
    SetModelOut,
    TierInfo,
    TierOut,
    TiersIn,
    TiersOut,
    TotalsOut,
    UpgradeTier,
    UsageOut,
    UsagePoint,
    UsageSeriesOut,
    UserOut,
)

router = APIRouter()
log = logging.getLogger(__name__)


def _spec_out(m: ModelSpec) -> ModelSpecOut:
    return ModelSpecOut(provider=m.provider, id=m.id, label=m.label)


def _mask_key(key: str) -> str | None:
    if not key:
        return None
    if len(key) <= 9:
        return "••••"
    return f"{key[:5]}…{key[-4:]}"


@router.get("/health", response_model=HealthOut)
async def health() -> HealthOut:
    return HealthOut(status="ok")


# -- user --------------------------------------------------------------------


@router.get("/me", response_model=MeOut)
async def me(
    user: TelegramUser = Depends(current_user),
    settings: Settings = Depends(get_settings),
    config: ConfigStore = Depends(get_config),
    session: AsyncSession = Depends(db_session),
) -> MeOut:
    db_user = await repo.get_or_create_user(
        session, user.id, username=user.username, first_name=user.first_name
    )
    tier = await config.tier_for_user(db_user)
    limit = (
        db_user.limit_override
        if db_user.limit_override is not None
        else tier.daily_limit
    )
    used = await repo.used_today(session, user.id)
    messages = await repo.message_count(session, user.id)
    payments = await repo.payment_count(session, user.id)
    paid = await config.paid_tiers()
    return MeOut(
        user=UserOut(
            id=db_user.id,
            username=db_user.username,
            first_name=db_user.first_name,
            tier=db_user.tier,
            is_premium=db_user.is_premium,
            premium_until=db_user.premium_until,
            preferred_model=db_user.preferred_model,
            role=db_user.role,
            role_enabled=db_user.role_enabled,
            banned=db_user.banned,
            created_at=db_user.created_at,
        ),
        usage=UsageOut(
            used_today=used,
            limit=limit,
            remaining=max(0, limit - used),
        ),
        totals=TotalsOut(messages=messages, payments=payments),
        is_admin=settings.is_admin(user.id) or db_user.is_admin,
        tier=TierInfo(key=tier.key, name=tier.name, daily_limit=tier.daily_limit),
        available_models=[_spec_out(m) for m in tier.models],
        upgrade_tiers=[
            UpgradeTier(
                key=t.key,
                name=t.name,
                daily_limit=t.daily_limit,
                price_stars=t.price_stars,
                period_days=t.period_days,
                model_count=len(t.models),
            )
            for t in paid
            if t.key != db_user.tier  # don't offer the tier they're already on
        ],
        user_roles_enabled=await config.user_roles_enabled(),
    )


@router.put("/me/role", response_model=RoleOut)
async def set_my_role(
    body: RoleIn,
    user: TelegramUser = Depends(current_user),
    config: ConfigStore = Depends(get_config),
    session: AsyncSession = Depends(db_session),
) -> RoleOut:
    if not await config.user_roles_enabled():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Personal roles are disabled by the operator.",
        )
    fields = body.model_fields_set
    db_user = await repo.get_or_create_user(session, user.id)
    if "role" in fields:
        await repo.set_role(session, user.id, (body.role or "").strip()[:1000] or None)
    if "enabled" in fields and body.enabled is not None:
        await repo.set_role_enabled(session, user.id, body.enabled)
    await session.flush()
    refreshed = await repo.get_user(session, user.id) or db_user
    return RoleOut(role=refreshed.role, enabled=refreshed.role_enabled)


@router.post("/me/invoice", response_model=InvoiceOut)
async def create_invoice(
    body: InvoiceIn,
    user: TelegramUser = Depends(current_user),
    config: ConfigStore = Depends(get_config),
    bot=Depends(get_bot),  # type: ignore[no-untyped-def]
) -> InvoiceOut:
    """Mint a Telegram Stars invoice link for a paid tier (opened in-app)."""
    from aiogram.types import LabeledPrice

    if bot is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payments are not configured.",
        )
    tier = (await config.tiers()).get(body.tier_key)
    if tier is None or not tier.is_paid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="That plan is not purchasable.",
        )
    link = await bot.create_invoice_link(
        title=f"{tier.name} plan",
        description=(
            f"{tier.name}: up to {tier.daily_limit} messages/day for "
            f"{tier.period_days} days."
        ),
        payload=f"tier:{tier.key}",
        currency="XTR",
        prices=[LabeledPrice(label=tier.name, amount=tier.price_stars)],
    )
    return InvoiceOut(invoice_link=link)


@router.put("/me/model", response_model=SetModelOut)
async def set_my_model(
    body: SetModelIn,
    user: TelegramUser = Depends(current_user),
    config: ConfigStore = Depends(get_config),
    session: AsyncSession = Depends(db_session),
) -> SetModelOut:
    db_user = await repo.get_or_create_user(session, user.id)
    if body.model is not None:
        tier = await config.tier_for_user(db_user)
        if body.model not in {m.id for m in tier.models}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Model is not available in your plan.",
            )
    await repo.set_preferred_model(session, user.id, body.model)
    return SetModelOut(preferred_model=body.model)


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
                role=m.role, content=m.content, model=m.model, created_at=m.created_at
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


# -- admin: prompt -----------------------------------------------------------


@router.get("/admin/prompt", response_model=PromptOut)
async def get_prompt(
    _admin: TelegramUser = Depends(require_admin),
    config: ConfigStore = Depends(get_config),
) -> PromptOut:
    return PromptOut(
        system_prompt=await config.system_prompt(),
        is_default=await config.system_prompt_is_default(),
    )


@router.put("/admin/prompt", response_model=PromptOut)
async def set_prompt(
    body: PromptIn,
    _admin: TelegramUser = Depends(require_admin),
    config: ConfigStore = Depends(get_config),
) -> PromptOut:
    prompt = body.system_prompt.strip()
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="system_prompt must not be empty",
        )
    await config.set_system_prompt(prompt)
    return PromptOut(system_prompt=prompt, is_default=False)


# -- admin: runtime (voice + disabled models) --------------------------------


async def _runtime_out(config: ConfigStore) -> RuntimeOut:
    tiers = await config.tiers()
    seen: dict[str, ModelSpec] = {}
    for tier in tiers.values():
        for m in tier.models:
            seen.setdefault(m.id, m)
    return RuntimeOut(
        voice_enabled=await config.voice_enabled(),
        disabled_models=sorted(await config.disabled_models()),
        all_models=[_spec_out(m) for m in seen.values()],
        user_roles_enabled=await config.user_roles_enabled(),
        generation_paused=await config.generation_paused(),
        max_tokens=await config.max_tokens(),
    )


@router.get("/admin/runtime", response_model=RuntimeOut)
async def get_runtime(
    _admin: TelegramUser = Depends(require_admin),
    config: ConfigStore = Depends(get_config),
) -> RuntimeOut:
    return await _runtime_out(config)


@router.put("/admin/runtime", response_model=RuntimeOut)
async def set_runtime(
    body: RuntimeIn,
    _admin: TelegramUser = Depends(require_admin),
    config: ConfigStore = Depends(get_config),
) -> RuntimeOut:
    if body.voice_enabled is not None:
        await config.set_voice_enabled(body.voice_enabled)
    if body.disabled_models is not None:
        await config.set_disabled_models(body.disabled_models)
    if body.user_roles_enabled is not None:
        await config.set_user_roles_enabled(body.user_roles_enabled)
    if body.generation_paused is not None:
        await config.set_generation_paused(body.generation_paused)
    if body.max_tokens is not None:
        await config.set_max_tokens(body.max_tokens)
    return await _runtime_out(config)


# -- admin: providers --------------------------------------------------------


def _provider_out(p) -> ProviderOut:  # type: ignore[no-untyped-def]
    return ProviderOut(
        name=p.name,
        kind=p.kind,
        is_default=p.is_default,
        enabled=p.enabled,
        has_key=p.has_key,
        key_masked=_mask_key(p.api_key),
        models=p.models,
        note=p.note,
    )


@router.get("/admin/providers", response_model=ProvidersOut)
async def get_providers(
    _admin: TelegramUser = Depends(require_admin),
    config: ConfigStore = Depends(get_config),
) -> ProvidersOut:
    providers = await config.providers()
    return ProvidersOut(providers=[_provider_out(p) for p in providers.values()])


@router.put("/admin/providers", response_model=ProviderOut)
async def set_provider(
    body: ProviderIn,
    _admin: TelegramUser = Depends(require_admin),
    config: ConfigStore = Depends(get_config),
) -> ProviderOut:
    try:
        provider = await config.set_provider(
            body.name,
            enabled=body.enabled,
            api_key=body.api_key,
            models=body.models,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return _provider_out(provider)


# -- admin: tiers ------------------------------------------------------------


def _tier_out(t) -> TierOut:  # type: ignore[no-untyped-def]
    return TierOut(
        key=t.key,
        name=t.name,
        daily_limit=t.daily_limit,
        price_stars=t.price_stars,
        period_days=t.period_days,
        models=[_spec_out(m) for m in t.models],
    )


@router.get("/admin/tiers", response_model=TiersOut)
async def get_tiers(
    _admin: TelegramUser = Depends(require_admin),
    config: ConfigStore = Depends(get_config),
) -> TiersOut:
    tiers = await config.tiers()
    return TiersOut(tiers=[_tier_out(t) for t in tiers.values()])


@router.put("/admin/tiers", response_model=TiersOut)
async def set_tiers(
    body: TiersIn,
    _admin: TelegramUser = Depends(require_admin),
    config: ConfigStore = Depends(get_config),
) -> TiersOut:
    payload = [
        {
            "key": t.key,
            "name": t.name,
            "daily_limit": t.daily_limit,
            "price_stars": t.price_stars,
            "period_days": t.period_days,
            "models": [{"provider": m.provider, "id": m.id} for m in t.models],
        }
        for t in body.tiers
    ]
    tiers = await config.set_tiers(payload)
    return TiersOut(tiers=[_tier_out(t) for t in tiers.values()])


async def _admin_user(session, settings: Settings, config: ConfigStore, u) -> AdminUser:  # type: ignore[no-untyped-def]
    tier = await config.tier_for_user(u)
    limit = u.limit_override if u.limit_override is not None else tier.daily_limit
    env_admin = settings.is_admin(u.id)
    return AdminUser(
        id=u.id,
        first_name=u.first_name,
        username=u.username,
        tier=u.tier,
        is_premium=u.is_premium,
        premium_until=u.premium_until,
        banned=u.banned,
        is_admin=env_admin or u.is_admin,
        env_admin=env_admin,
        limit_override=u.limit_override,
        used_today=await repo.used_today(session, u.id),
        daily_limit=limit,
        messages=await repo.message_count(session, u.id),
        payments=await repo.payment_count(session, u.id),
        created_at=u.created_at,
    )


@router.get("/admin/users", response_model=AdminUsersOut)
async def admin_list_users(
    search: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _admin: TelegramUser = Depends(require_admin),
    settings: Settings = Depends(get_settings),
    config: ConfigStore = Depends(get_config),
    session: AsyncSession = Depends(db_session),
) -> AdminUsersOut:
    users, total = await repo.list_users(
        session, search=search, limit=limit, offset=offset
    )
    return AdminUsersOut(
        users=[await _admin_user(session, settings, config, u) for u in users],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.put("/admin/users/{user_id}", response_model=AdminUser)
async def admin_update_user(
    user_id: int,
    body: AdminUserUpdate,
    _admin: TelegramUser = Depends(require_admin),
    settings: Settings = Depends(get_settings),
    config: ConfigStore = Depends(get_config),
    session: AsyncSession = Depends(db_session),
) -> AdminUser:
    fields = body.model_fields_set
    user = await repo.get_or_create_user(session, user_id)

    if "banned" in fields and body.banned is not None:
        await repo.set_banned(session, user_id, body.banned)
    if "is_admin" in fields and body.is_admin is not None:
        await repo.set_admin(session, user_id, body.is_admin)
    if "limit_override" in fields:
        await repo.set_limit_override(session, user_id, body.limit_override)
    if "tier" in fields:
        key = body.tier or "free"
        tiers = await config.tiers()
        if key not in tiers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown tier."
            )
        if key == "free":
            await repo.set_tier(session, user_id, "free", None)
        else:
            until = dt.datetime.now(dt.timezone.utc) + dt.timedelta(
                days=tiers[key].period_days or 30
            )
            await repo.set_tier(session, user_id, key, until)
    if "reset_usage" in fields and body.reset_usage:
        await repo.reset_today_usage(session, user_id)

    await session.flush()
    user = await repo.get_user(session, user_id) or user
    return await _admin_user(session, settings, config, user)


_BROADCAST_TASKS: set[asyncio.Task[None]] = set()


async def _run_broadcast(bot, ids: list[int], text: str) -> None:  # type: ignore[no-untyped-def]
    """Throttled background send (~20 msg/s); per-user failures are ignored."""
    sent = failed = 0
    for uid in ids:
        try:
            await bot.send_message(uid, text)
            sent += 1
        except Exception:  # noqa: BLE001 - user blocked the bot, deactivated, etc.
            failed += 1
        await asyncio.sleep(0.05)
    log.info("broadcast done: sent=%d failed=%d", sent, failed)


@router.post("/admin/broadcast", response_model=BroadcastOut)
async def admin_broadcast(
    body: BroadcastIn,
    _admin: TelegramUser = Depends(require_admin),
    bot=Depends(get_bot),  # type: ignore[no-untyped-def]
    session: AsyncSession = Depends(db_session),
) -> BroadcastOut:
    text = body.text.strip()
    if not text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="text is empty"
        )
    if bot is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Bot is not configured.",
        )
    ids = await repo.all_user_ids(session, tier=body.tier)
    task = asyncio.create_task(_run_broadcast(bot, ids, text))
    _BROADCAST_TASKS.add(task)
    task.add_done_callback(_BROADCAST_TASKS.discard)
    return BroadcastOut(queued=len(ids))


@router.get("/admin/analytics", response_model=AnalyticsOut)
async def admin_analytics(
    days: int = Query(default=14, ge=1, le=90),
    _admin: TelegramUser = Depends(require_admin),
    session: AsyncSession = Depends(db_session),
) -> AnalyticsOut:
    return AnalyticsOut(
        messages=[DayCount(**d) for d in await repo.messages_per_day(session, days)],
        new_users=[DayCount(**d) for d in await repo.new_users_per_day(session, days)],
        model_mix=[ModelCount(**m) for m in await repo.model_mix(session, days)],
        revenue_stars=await repo.revenue_stars(session),
    )


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
