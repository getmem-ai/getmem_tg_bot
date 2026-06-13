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


class MeOut(BaseModel):
    user: UserOut
    usage: UsageOut
    totals: TotalsOut
    is_admin: bool


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
