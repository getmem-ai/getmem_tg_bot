"""Lazy faster-whisper model wrapper.

`faster-whisper <https://github.com/SYSTRAN/faster-whisper>`_ is a CTranslate2
reimplementation of Whisper that runs several times faster than the reference
model on CPU — especially with ``int8`` quantization. That makes it practical to
transcribe short Telegram voice notes on a modest, GPU-less server.

The model is loaded once on first use (so the service starts instantly) and runs
in a worker thread (it's sync and CPU-bound), keeping the event loop responsive.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from faster_whisper import WhisperModel

log = logging.getLogger(__name__)


class Transcriber:
    def __init__(
        self,
        *,
        model_size: str | None = None,
        device: str | None = None,
        compute_type: str | None = None,
        download_root: str | None = None,
        cpu_threads: int | None = None,
    ) -> None:
        self.model_size = model_size or os.getenv("WHISPER_MODEL", "base")
        self.device = device or os.getenv("WHISPER_DEVICE", "cpu")
        self.compute_type = compute_type or os.getenv("WHISPER_COMPUTE_TYPE", "int8")
        self.download_root = download_root or os.getenv(
            "WHISPER_DOWNLOAD_ROOT", "/models"
        )
        self.cpu_threads = cpu_threads or int(os.getenv("WHISPER_CPU_THREADS", "0"))
        self._model: "WhisperModel | None" = None
        self._lock = asyncio.Lock()

    @property
    def loaded(self) -> bool:
        return self._model is not None

    async def _ensure_model(self) -> "WhisperModel":
        if self._model is not None:
            return self._model
        async with self._lock:
            if self._model is None:
                from faster_whisper import WhisperModel

                log.info(
                    "Loading faster-whisper model=%s device=%s compute=%s "
                    "(first run downloads weights)…",
                    self.model_size,
                    self.device,
                    self.compute_type,
                )
                self._model = await asyncio.to_thread(
                    WhisperModel,
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                    download_root=self.download_root,
                    cpu_threads=self.cpu_threads,
                )
                log.info("faster-whisper model ready.")
        return self._model

    async def transcribe(
        self, audio_path: str, *, language: str | None = None
    ) -> str:
        model = await self._ensure_model()

        def _run() -> str:
            segments, _info = model.transcribe(
                audio_path,
                language=language,
                vad_filter=True,  # skip silence → faster + cleaner
                beam_size=1,      # greedy: fastest on CPU
            )
            return " ".join(seg.text.strip() for seg in segments).strip()

        return await asyncio.to_thread(_run)

    async def warmup(self) -> None:
        try:
            await self._ensure_model()
        except Exception as exc:  # noqa: BLE001
            log.warning("warmup failed: %s", exc)
