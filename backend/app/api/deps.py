"""FastAPI dependencies: settings, DB session and the authenticated user."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..core import ConfigStore
from ..db import Database
from .auth import InitDataError, TelegramUser, parse_auth_header, validate_init_data


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_db(request: Request) -> Database:
    return request.app.state.db


def get_config(request: Request) -> ConfigStore:
    return request.app.state.config


def get_bot(request: Request):  # type: ignore[no-untyped-def]
    return request.app.state.bot


async def db_session(
    db: Database = Depends(get_db),
) -> AsyncIterator[AsyncSession]:
    async with db.session() as session:
        yield session


def current_user(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> TelegramUser:
    """Authenticate the caller from the ``Authorization: tma <initData>`` header."""
    try:
        raw = parse_auth_header(authorization)
        return validate_init_data(
            raw, settings.bot_token, max_age=settings.init_data_max_age
        )
    except InitDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc


def require_admin(
    user: TelegramUser = Depends(current_user),
    settings: Settings = Depends(get_settings),
) -> TelegramUser:
    if not settings.is_admin(user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admins only"
        )
    return user
