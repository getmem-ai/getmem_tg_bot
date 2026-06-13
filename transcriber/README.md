# Voice transcription service

A tiny, optional FastAPI microservice that turns Telegram voice notes into text
using [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (a fast,
CPU-friendly Whisper implementation). It's kept separate from the bot so the
heavy model dependency and weights never bloat the main image — start it only if
you want voice support.

## Enable it

It runs under the `voice` Docker Compose profile:

```bash
# main stack only (no voice)
docker compose up -d --build

# include the transcriber
docker compose --profile voice up -d --build
```

When the profile is active, set `ENABLE_VOICE=true` and the bot will route voice
messages here automatically (`TRANSCRIBER_URL=http://transcriber:8001`).

## API

| Method | Path | Body | Returns |
|---|---|---|---|
| `POST` | `/transcribe` | multipart `file=<audio>` (`language` optional) | `{"text": "..."}` |
| `GET` | `/health` | — | `{"status","model","loaded"}` |

## Configuration (env)

| Variable | Default | Notes |
|---|---|---|
| `WHISPER_MODEL` | `base` | `tiny`/`base`/`small`/`medium`/`large-v3`. Bigger = better & slower. |
| `WHISPER_DEVICE` | `cpu` | `cuda` if you have a GPU. |
| `WHISPER_COMPUTE_TYPE` | `int8` | `int8` is fastest on CPU; `float16` for GPU. |
| `WHISPER_CPU_THREADS` | `0` (auto) | Limit CPU threads on small servers. |
| `WHISPER_WARMUP` | `false` | Pre-load the model at startup instead of on first request. |
| `WHISPER_DOWNLOAD_ROOT` | `/models` | Where weights are cached (mount a volume). |

## Resource notes

- `tiny`/`base` int8 use a few hundred MB of RAM and transcribe a short note in
  ~1–3s on a modest CPU — fine for a small VPS.
- `small`+ are noticeably more accurate but need more RAM/CPU.
- The model downloads on first use; the `whisper-models` volume caches it.
