import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest

from app.api.auth import InitDataError, parse_auth_header, validate_init_data

BOT_TOKEN = "123456:test-bot-token"


def _make_init_data(
    *, token: str = BOT_TOKEN, auth_date: int | None = None, user: dict | None = None
) -> str:
    user = user or {"id": 42, "first_name": "Bob", "username": "bob"}
    fields = {
        "auth_date": str(auth_date if auth_date is not None else int(time.time())),
        "query_id": "AAH_test",
        "user": json.dumps(user, separators=(",", ":")),
    }
    data_check_string = "\n".join(f"{k}={fields[k]}" for k in sorted(fields))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(
        secret, data_check_string.encode(), hashlib.sha256
    ).hexdigest()
    return urlencode(fields)


def test_valid_init_data_returns_user() -> None:
    user = validate_init_data(_make_init_data(), BOT_TOKEN)
    assert user.id == 42
    assert user.username == "bob"
    assert user.first_name == "Bob"


def test_bad_signature_rejected() -> None:
    with pytest.raises(InitDataError):
        validate_init_data(_make_init_data(token="wrong:token"), BOT_TOKEN)


def test_expired_init_data_rejected() -> None:
    stale = _make_init_data(auth_date=int(time.time()) - 100_000)
    with pytest.raises(InitDataError):
        validate_init_data(stale, BOT_TOKEN, max_age=3600)


def test_tampered_payload_rejected() -> None:
    init_data = _make_init_data()
    tampered = init_data.replace("Bob", "Eve")
    with pytest.raises(InitDataError):
        validate_init_data(tampered, BOT_TOKEN)


def test_empty_rejected() -> None:
    with pytest.raises(InitDataError):
        validate_init_data("", BOT_TOKEN)


def test_parse_auth_header() -> None:
    assert parse_auth_header("tma abc123") == "abc123"
    assert parse_auth_header("tma a b c") == "a b c"


def test_parse_auth_header_rejects_bad_scheme() -> None:
    with pytest.raises(InitDataError):
        parse_auth_header("Bearer xyz")
    with pytest.raises(InitDataError):
        parse_auth_header(None)
