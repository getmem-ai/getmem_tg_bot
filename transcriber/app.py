"""Tiny FastAPI transcription service.

One internal endpoint, ``POST /transcribe``, accepts an uploaded audio file
(Telegram voice notes are OGG/Opus) and returns the recognised text. It runs in
its own container so the heavy faster-whisper dependency and model weights stay
out of the bot/API image; the bot calls it over the internal Docker network and
degrades gracefully when it's not running.
"""

from __future__ import annotations

import logging
import os
import tempfile
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel

from whisper_model import Transcriber

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
log = logging.getLogger("transcriber")

transcriber = Transcriber()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if os.getenv("WHISPER_WARMUP", "false").lower() in {"1", "true", "yes", "on"}:
        log.info("Warming up model on startup…")
        await transcriber.warmup()
    yield


app = FastAPI(title="GetMem Voice Transcriber", version="0.2.0", lifespan=lifespan)


class TranscriptionOut(BaseModel):
    text: str


class HealthOut(BaseModel):
    status: str
    model: str
    loaded: bool


@app.get("/health", response_model=HealthOut)
async def health() -> HealthOut:
    return HealthOut(
        status="ok", model=transcriber.model_size, loaded=transcriber.loaded
    )


@app.post("/transcribe", response_model=TranscriptionOut)
async def transcribe(
    file: UploadFile = File(...),
    language: str | None = None,
) -> TranscriptionOut:
    suffix = os.path.splitext(file.filename or "audio.oga")[1] or ".oga"
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    try:
        tmp.write(await file.read())
        tmp.close()
        text = await transcriber.transcribe(tmp.name, language=language)
        return TranscriptionOut(text=text)
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
