# Telegram Mini App — Bot Dashboard

A mobile-first [Telegram Mini App](https://core.telegram.org/bots/webapps) that
lets a Telegram user open the bot's web app and see their own usage and
activity. Admins additionally see global stats.

Built with **Next.js 14 (App Router)**, **TypeScript**, **Tailwind CSS**, and
**Recharts**. It talks to the bot's backend over a small typed fetch client and
uses the raw `window.Telegram.WebApp` bridge — no extra Telegram SDK packages,
so the Docker build stays small and reliable.

## How it works

### Authentication

The Mini App runs inside Telegram's in-app browser. Telegram injects
`window.Telegram.WebApp.initData` — an **opaque, signed** string describing the
current user. The frontend never parses or validates the signature. It simply
forwards the raw string to the backend on every request:

```
Authorization: tma <initDataRaw>
```

The backend validates the signature (using the bot token) and resolves the
user. See `lib/api.ts` and `lib/telegram.ts`.

If `initData` is empty (for example, when the page is opened in a normal browser
during development), the app shows a friendly **"Open inside Telegram"** screen.
For local development you can set `NEXT_PUBLIC_DEV_INIT_DATA` to a captured raw
`initData` string and the app will use that instead.

### Theming

On load the app calls `window.Telegram.WebApp.ready()` and `.expand()`, then
reads `themeParams` and maps them to CSS variables (`--tg-bg`, `--tg-text`,
`--tg-hint`, `--tg-button`, `--tg-button-text`, `--tg-secondary-bg`, ...). This
makes the UI match the user's Telegram theme in both light and dark mode, and it
re-applies automatically on `themeChanged`. See `lib/telegram.ts`.

### Data flow

A single dashboard page (`app/page.tsx`) fetches:

| Endpoint                       | Used for                          |
| ------------------------------ | --------------------------------- |
| `GET {API_BASE}/me`            | Profile, today's usage, totals    |
| `GET {API_BASE}/me/usage?days=14` | 14-day usage chart             |
| `GET {API_BASE}/me/activity?limit=20` | Recent activity list       |
| `GET {API_BASE}/admin/stats`   | Admin panel (only if `is_admin`)  |
| `GET {API_BASE}/health`        | Health check (available in client) |

Each section has its own loading skeleton and graceful error state, so a partial
failure (e.g. the chart) doesn't take down the whole page.

## Environment variables

Only `NEXT_PUBLIC_*` variables are used — there are **no server-side secrets** in
this frontend. Copy `.env.example` to `.env.local` for development.

| Variable                   | Default | Description                                            |
| -------------------------- | ------- | ------------------------------------------------------ |
| `NEXT_PUBLIC_API_BASE`     | `/api`  | Base URL for the backend API.                          |
| `NEXT_PUBLIC_DEV_INIT_DATA`| _(unset)_ | Dev-only fallback initData. **Never set in production.** |

## Development

```bash
npm install
npm run dev      # http://localhost:3000
npm run build    # production build (standalone output)
npm run start    # run the production build
npm run lint
```

Opened in a plain browser you'll see the "Open inside Telegram" screen unless
`NEXT_PUBLIC_DEV_INIT_DATA` is set.

## Docker

The image uses a multi-stage build on `node:20-alpine` with Next.js
`output: "standalone"`, runs as a non-root user, and listens on port 3000.

```bash
docker build -t bot-miniapp .
docker run -p 3000:3000 -e NEXT_PUBLIC_API_BASE=https://your-bot.example.com/api bot-miniapp
```

> Note: `NEXT_PUBLIC_*` values are inlined at **build time**. To change the API
> base for a different deployment, rebuild with the desired build arg/env, or
> serve the Mini App behind the same host/proxy as the backend and keep the
> default `/api`.

## Registering with @BotFather

Telegram Mini Apps **must be served over HTTPS**. Once deployed behind TLS:

1. Open [@BotFather](https://t.me/BotFather).
2. `/setmenubutton` (or `/newapp` for a named Mini App) and choose your bot.
3. Provide the public **HTTPS** URL of this app as the Web App URL.
4. Users can now launch it from the bot's menu button or from inline/keyboard
   Web App buttons.

When launched this way, Telegram provides a valid signed `initData` that the
backend verifies.

---

Powered by GetMem.
