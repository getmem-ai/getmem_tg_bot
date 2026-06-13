"""Exception types raised by the getmem SDK.

Mirrors the standard error envelope from `plans/shared/error-format.md`:

    {"error": "...", "message": "...", "details": {}, "request_id": "..."}
"""

from __future__ import annotations

from typing import Any


class GetmemError(Exception):
    """Base class for every error raised by this SDK."""


class GetmemApiError(GetmemError):
    """A non-2xx response from the memory service.

    Attributes
    ----------
    status:
        HTTP status code (e.g. 401, 402, 429, 500).
    code:
        Machine-readable error code from the response ``error`` field
        (e.g. ``"unauthorized"``, ``"quota_exceeded"``), or a synthetic
        ``http_<status>`` when the body is not the standard envelope.
    request_id:
        Server request id, for cross-service debugging, when present.
    details:
        Optional structured details from the response body.
    retry_after:
        Seconds to wait before retrying, parsed from ``Retry-After`` on 429s.
    """

    def __init__(
        self,
        status: int,
        code: str,
        message: str,
        *,
        request_id: str | None = None,
        details: dict[str, Any] | None = None,
        retry_after: float | None = None,
    ) -> None:
        suffix = f" (request_id={request_id})" if request_id else ""
        super().__init__(f"[{code}/HTTP {status}] {message}{suffix}")
        self.status = status
        self.code = code
        self.message = message
        self.request_id = request_id
        self.details = details or {}
        self.retry_after = retry_after

    @property
    def is_quota_exceeded(self) -> bool:
        return self.status == 402 or self.code == "quota_exceeded"

    @property
    def is_rate_limited(self) -> bool:
        return self.status == 429 or self.code == "rate_limited"

    @property
    def is_unauthorized(self) -> bool:
        return self.status == 401 or self.code == "unauthorized"

    @property
    def is_not_found(self) -> bool:
        return self.status == 404 or self.code == "not_found"


class GetmemTimeoutError(GetmemError):
    """The request exceeded the configured timeout."""


class GetmemConnectionError(GetmemError):
    """A transport-level failure (DNS, TCP, TLS) before a response arrived."""
