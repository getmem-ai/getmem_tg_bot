"""HTTP adapter for the optional voice-transcription service.

The bot stays lightweight: instead of loading Whisper in-process, it POSTs the
downloaded voice file to the separate ``transcriber`` service and gets text
back. If the service is unreachable, callers get an empty string and the bot
degrades gracefully.

Implements :class:`app.core.ports.Transcriber`.
"""

from __future__ import annotations

import logging

import httpx

log = logging.getLogger(__name__)


class HttpTranscriber:
    def __init__(self, base_url: str, *, timeout: float = 120.0) -> None:
        self._http = httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=timeout)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def transcribe(
        self,
        audio: bytes,
        *,
        filename: str = "voice.oga",
        language: str | None = None,
    ) -> str:
        try:
            params = {"language": language} if language else None
            resp = await self._http.post(
                "/transcribe",
                files={"file": (filename, audio, "application/octet-stream")},
                params=params,
            )
            resp.raise_for_status()
            return str(resp.json().get("text", "")).strip()
        except (httpx.HTTPError, ValueError) as exc:
            log.warning("transcriber request failed: %s", exc)
            return ""

    async def healthy(self) -> bool:
        try:
            resp = await self._http.get("/health")
            return resp.status_code == 200
        except httpx.HTTPError:
            return False
