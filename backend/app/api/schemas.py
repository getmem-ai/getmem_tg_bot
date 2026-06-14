"""Pydantic response models for the Mini App API.

These define the exact JSON contract the Next.js Mini App consumes.
"""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel


class UserOut(BaseModel):
    id: int
    username: str | None
    first_name: str | None
    tier: str
    is_premium: bool
    premium_until: dt.datetime | None
    preferred_model: str | None
    role: str | None
    role_enabled: bool = False
    banned: bool = False
    avatar: str | None = None
    reply_language: str | None = None
    reply_style: str | None = None
    reply_length: str | None = None
    timezone: str = "UTC"
    created_at: dt.datetime


class ProfileIn(BaseModel):
    """User-editable profile. Only the fields present are updated; an explicit
    ``null`` clears a value (e.g. removing the avatar)."""

    avatar: str | None = None
    reply_language: str | None = None
    reply_style: str | None = None
    reply_length: str | None = None
    timezone: str | None = None


class ProfileOut(BaseModel):
    avatar: str | None = None
    reply_language: str | None = None
    reply_style: str | None = None
    reply_length: str | None = None
    timezone: str = "UTC"


class UsageOut(BaseModel):
    used_today: int
    limit: int
    remaining: int


class TotalsOut(BaseModel):
    messages: int
    payments: int


class ModelSpecOut(BaseModel):
    provider: str
    id: str
    label: str


class TierInfo(BaseModel):
    key: str
    name: str
    daily_limit: int


class UpgradeTier(BaseModel):
    key: str
    name: str
    daily_limit: int
    price_stars: int
    period_days: int
    model_count: int
    models: list[ModelSpecOut]


class BrandOut(BaseModel):
    name: str
    tagline: str


class MeOut(BaseModel):
    user: UserOut
    usage: UsageOut
    totals: TotalsOut
    is_admin: bool
    tier: TierInfo
    available_models: list[ModelSpecOut]
    upgrade_tiers: list[UpgradeTier]
    user_roles_enabled: bool
    brand: BrandOut


class RoleIn(BaseModel):
    # Partial: only fields explicitly present are applied.
    role: str | None = None
    enabled: bool | None = None


class RoleOut(BaseModel):
    role: str | None
    enabled: bool


class InvoiceIn(BaseModel):
    tier_key: str


class InvoiceOut(BaseModel):
    invoice_link: str


class SetModelIn(BaseModel):
    model: str | None = None


class SetModelOut(BaseModel):
    preferred_model: str | None


class RuntimeOut(BaseModel):
    voice_enabled: bool
    disabled_models: list[str]
    all_models: list[ModelSpecOut]
    user_roles_enabled: bool
    generation_paused: bool
    max_tokens: int
    vision_enabled: bool
    vision_model: str
    vision_provider: str
    vision_premium_only: bool
    welcome_message: str  # "" when using the built-in default
    brand_name: str
    brand_tagline: str
    streaming_enabled: bool
    scheduling_enabled: bool


class RuntimeIn(BaseModel):
    voice_enabled: bool | None = None
    disabled_models: list[str] | None = None
    user_roles_enabled: bool | None = None
    generation_paused: bool | None = None
    max_tokens: int | None = None
    vision_enabled: bool | None = None
    vision_model: str | None = None
    vision_provider: str | None = None
    vision_premium_only: bool | None = None
    welcome_message: str | None = None
    brand_name: str | None = None
    brand_tagline: str | None = None
    streaming_enabled: bool | None = None
    scheduling_enabled: bool | None = None


class ProviderTestIn(BaseModel):
    name: str
    api_key: str | None = None  # optional override; falls back to the stored key
    model: str | None = None


class ProviderTestOut(BaseModel):
    ok: bool
    detail: str


class ProviderOut(BaseModel):
    name: str
    kind: str
    is_default: bool
    enabled: bool
    has_key: bool
    key_masked: str | None
    models: list[str]
    note: str | None = None


class ProvidersOut(BaseModel):
    providers: list[ProviderOut]


class ProviderIn(BaseModel):
    name: str
    enabled: bool | None = None
    api_key: str | None = None
    models: list[str] | None = None


class TierModelIn(BaseModel):
    provider: str
    id: str


class TierOut(BaseModel):
    key: str
    name: str
    daily_limit: int
    price_stars: int
    period_days: int
    models: list[ModelSpecOut]


class TiersOut(BaseModel):
    tiers: list[TierOut]


class TierIn(BaseModel):
    key: str
    name: str
    daily_limit: int
    price_stars: int = 0
    period_days: int = 30
    models: list[TierModelIn]


class TiersIn(BaseModel):
    tiers: list[TierIn]


class ActivityItem(BaseModel):
    role: str
    content: str
    model: str | None
    created_at: dt.datetime


class ActivityOut(BaseModel):
    items: list[ActivityItem]


class UsagePoint(BaseModel):
    day: str
    count: int


class UsageSeriesOut(BaseModel):
    series: list[UsagePoint]


class RecentUser(BaseModel):
    id: int
    first_name: str | None
    username: str | None
    tier: str
    created_at: dt.datetime


class AdminStatsOut(BaseModel):
    users: int
    premium: int
    messages_today: int
    payments: int
    recent_users: list[RecentUser]


class PromptOut(BaseModel):
    system_prompt: str
    is_default: bool


class PromptIn(BaseModel):
    system_prompt: str


class AdminUser(BaseModel):
    id: int
    first_name: str | None
    username: str | None
    tier: str
    is_premium: bool
    premium_until: dt.datetime | None
    banned: bool
    is_admin: bool
    env_admin: bool  # admin via ADMIN_IDS — can't be revoked from the UI
    limit_override: int | None
    used_today: int
    daily_limit: int
    messages: int
    payments: int
    created_at: dt.datetime


class AdminUsersOut(BaseModel):
    users: list[AdminUser]
    total: int
    limit: int
    offset: int


class AdminUserUpdate(BaseModel):
    # Only fields explicitly present are applied (null is a meaningful value).
    banned: bool | None = None
    is_admin: bool | None = None
    limit_override: int | None = None
    tier: str | None = None
    reset_usage: bool | None = None


class BroadcastIn(BaseModel):
    text: str
    tier: str | None = None  # None = all users


class BroadcastOut(BaseModel):
    queued: int


class DayCount(BaseModel):
    day: str
    count: int


class ModelCount(BaseModel):
    model: str
    count: int


class AnalyticsOut(BaseModel):
    messages: list[DayCount]
    new_users: list[DayCount]
    model_mix: list[ModelCount]
    revenue_stars: int


class HealthOut(BaseModel):
    status: str


# -- templates, config backup, onboarding ------------------------------------


class TemplateOut(BaseModel):
    key: str
    name: str
    emoji: str = ""
    description: str = ""


class TemplatesOut(BaseModel):
    templates: list[TemplateOut]


class ConfigApplyResult(BaseModel):
    applied: list[str]
    todo: list[str]


class ConfigImportIn(BaseModel):
    config: dict


class OnboardingOut(BaseModel):
    onboarded: bool
    has_openrouter_key: bool
    system_prompt_is_default: bool
    tiers_count: int
    providers_configured: int  # providers that are enabled AND have a usable key


# -- scheduling --------------------------------------------------------------


class ScheduleIn(BaseModel):
    title: str
    prompt: str
    frequency: str = "daily"  # daily | weekly | interval | as_needed
    times: list[str] = []  # ["08:00", "20:00"] in the user's timezone
    weekdays: list[int] = []  # 0=Mon … 6=Sun (used when frequency == weekly)
    interval_days: int | None = None  # used when frequency == interval
    enabled: bool = True


class ScheduleOut(BaseModel):
    id: int
    title: str
    prompt: str
    frequency: str
    times: list[str]
    weekdays: list[int]
    interval_days: int | None
    enabled: bool
    next_run_at: dt.datetime | None
    last_run_at: dt.datetime | None
    created_at: dt.datetime


class SchedulesOut(BaseModel):
    tasks: list[ScheduleOut]
    timezone: str
    enabled: bool  # whether the operator allows scheduling at all


class ScheduleRunOut(BaseModel):
    id: int
    task_id: int
    fired_at: dt.datetime
    status: str
    preview: str


class ScheduleRunsOut(BaseModel):
    runs: list[ScheduleRunOut]
