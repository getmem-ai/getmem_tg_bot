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


class MeOut(BaseModel):
    user: UserOut
    usage: UsageOut
    totals: TotalsOut
    is_admin: bool
    tier: TierInfo
    available_models: list[ModelSpecOut]


class SetModelIn(BaseModel):
    model: str | None = None


class SetModelOut(BaseModel):
    preferred_model: str | None


class RuntimeOut(BaseModel):
    voice_enabled: bool
    disabled_models: list[str]
    all_models: list[ModelSpecOut]


class RuntimeIn(BaseModel):
    voice_enabled: bool | None = None
    disabled_models: list[str] | None = None


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
    models: list[ModelSpecOut]


class TiersOut(BaseModel):
    tiers: list[TierOut]


class TierIn(BaseModel):
    key: str
    daily_limit: int
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


class HealthOut(BaseModel):
    status: str
