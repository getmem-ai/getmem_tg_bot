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
    created_at: dt.datetime


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


class MeOut(BaseModel):
    user: UserOut
    usage: UsageOut
    totals: TotalsOut
    is_admin: bool
    tier: TierInfo
    available_models: list[ModelSpecOut]
    upgrade_tiers: list[UpgradeTier]
    user_roles_enabled: bool


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


class RuntimeIn(BaseModel):
    voice_enabled: bool | None = None
    disabled_models: list[str] | None = None
    user_roles_enabled: bool | None = None


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
    limit_override: int | None = None
    tier: str | None = None
    reset_usage: bool | None = None


class HealthOut(BaseModel):
    status: str
