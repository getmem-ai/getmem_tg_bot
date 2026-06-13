"""Mini App API routes.

All ``/me*`` routes are scoped to the authenticated Telegram user (from a
validated ``initData`` header); ``/admin/*`` additionally requires the caller to
be in ``ADMIN_IDS``. Editable config is read/written via the ConfigStore.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..core import ConfigStore
from ..core.config_store import ModelSpec
from ..db import repo
from .auth import TelegramUser
from .deps import current_user, db_session, get_config, get_settings, require_admin
from .schemas import (
    ActivityItem,
    ActivityOut,
    AdminStatsOut,
    HealthOut,
    MeOut,
    ModelSpecOut,
    PromptIn,
    PromptOut,
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
    UsageOut,
    UsagePoint,
    UsageSeriesOut,
    UserOut,
)

router = APIRouter()


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
            used_today=used,
            limit=tier.daily_limit,
            remaining=max(0, tier.daily_limit - used),
        ),
        totals=TotalsOut(messages=messages, payments=payments),
        is_admin=settings.is_admin(user.id),
        tier=TierInfo(key=tier.key, name=tier.name, daily_limit=tier.daily_limit),
        available_models=[_spec_out(m) for m in tier.models],
    )


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
