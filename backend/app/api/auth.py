"""Telegram Mini App ``initData`` validation.

A Mini App receives a signed ``initData`` string from Telegram. The backend
verifies the HMAC signature with the bot token (per Telegram's spec) to
authenticate the user — we never trust a user id sent in the clear.

Spec: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl


class InitDataError(Exception):
    """Raised when initData is missing, malformed, expired or has a bad signature."""


@dataclass(frozen=True)
class TelegramUser:
    id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None


def validate_init_data(
    init_data: str, bot_token: str, *, max_age: int = 86_400
) -> TelegramUser:
    """Validate a raw ``initData`` string and return the authenticated user."""
    if not init_data:
        raise InitDataError("Empty initData")
    if not bot_token:
        raise InitDataError("Server is missing BOT_TOKEN; cannot validate initData")

    try:
        pairs = dict(parse_qsl(init_data, strict_parsing=True, keep_blank_values=True))
    except ValueError as exc:
        raise InitDataError("Malformed initData") from exc

    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise InitDataError("initData missing hash")

    data_check_string = "\n".join(
        f"{key}={pairs[key]}" for key in sorted(pairs)
    )
    secret_key = hmac.new(
        b"WebAppData", bot_token.encode(), hashlib.sha256
    ).digest()
    calculated = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated, received_hash):
        raise InitDataError("Bad initData signature")

    # Freshness: reject stale initData to limit replay.
    if max_age > 0:
        try:
            auth_date = int(pairs.get("auth_date", "0"))
        except ValueError:
            auth_date = 0
        if auth_date <= 0 or time.time() - auth_date > max_age:
            raise InitDataError("initData expired")

    user_raw = pairs.get("user")
    if not user_raw:
        raise InitDataError("initData has no user")
    try:
        user = json.loads(user_raw)
        return TelegramUser(
            id=int(user["id"]),
            first_name=user.get("first_name"),
            last_name=user.get("last_name"),
            username=user.get("username"),
        )
    except (ValueError, KeyError, TypeError) as exc:
        raise InitDataError("initData user is malformed") from exc


def parse_auth_header(header: str | None) -> str:
    """Extract the raw initData from an ``Authorization: tma <initData>`` header."""
    if not header:
        raise InitDataError("Missing Authorization header")
    parts = header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "tma":
        raise InitDataError("Authorization must be: tma <initData>")
    return parts[1]
