# Deployment

Three ready-made setups. Pick the one that matches where you're running.

| File | For | Config source | HTTPS / domain |
|---|---|---|---|
| `../docker-compose.yml` | **Local / dev** | `.env` file | none (bot uses long polling) |
| `docker-compose.prod.yml` | **Self-managed VPS** | `.env` file | **Caddy** auto Let's Encrypt |
| `docker-compose.dokploy.yml` | **Dokploy** | env injected by Dokploy | Dokploy's Traefik |

All of them run the same services: `db` (Postgres) → `migrate` (one-shot
`alembic upgrade head`) → `bot`, `api`, `miniapp`, and an optional `transcriber`
(voice) behind the `voice` profile.

---

## 1. Local / dev

No domain, no TLS — the bot uses long polling.

```bash
cp .env.example .env          # fill BOT_TOKEN, OPENROUTER_API_KEY, GETMEM_API_KEY
docker compose up -d --build
# with voice:
docker compose --profile voice up -d --build
```

The API is published on `localhost:${API_PORT}` and the Mini App on
`localhost:${MINIAPP_PORT}`. The Mini App needs HTTPS to run *inside* Telegram —
for local UI work, open it in a browser with `NEXT_PUBLIC_DEV_INIT_DATA` set.

---

## 2. Production VPS (single domain + automatic HTTPS)

Uses [Caddy](https://caddyserver.com/) to obtain/renew a Let's Encrypt cert and
route one domain to all services:

```
https://DOMAIN/         → Mini App (Next.js)
https://DOMAIN/api/*    → API (FastAPI)
https://DOMAIN/webhook* → bot (Telegram webhook)
```

1. Point a DNS **A record** for `DOMAIN` at the server; open ports **80** & **443**.
2. In `.env` set (besides the usual keys):
   ```env
   DOMAIN=bot.example.com
   ACME_EMAIL=you@example.com
   WEBHOOK_URL=https://bot.example.com
   WEBHOOK_SECRET=<openssl rand -hex 32>
   MINIAPP_URL=https://bot.example.com
   NEXT_PUBLIC_API_BASE=/api
   ```
   Setting `WEBHOOK_URL` switches the bot from polling to webhook automatically.
3. Launch from the repo root:
   ```bash
   docker compose -f deploy/docker-compose.prod.yml --env-file .env up -d --build
   # with voice:  ... --profile voice up -d --build
   ```

Certificates live in the `caddy-data` volume and renew automatically.

---

## 3. Dokploy

[Dokploy](https://dokploy.com/) injects configuration as environment variables
(not a `.env` file) and provides its own Traefik reverse proxy with domains +
HTTPS, so this variant ships **no Caddy** and the bot uses **long polling**.

1. In Dokploy, create a **Compose** application pointing at
   `deploy/docker-compose.dokploy.yml`.
2. Paste your configuration into the app's **Environment** tab (these populate
   the `${VAR}` references in the compose file): `BOT_TOKEN`,
   `OPENROUTER_API_KEY`, `GETMEM_API_KEY`, `POSTGRES_USER/PASSWORD/DB`,
   `ADMIN_IDS`, and the Mini App URLs (below).
3. Deploy, then in Dokploy map domains:
   - `miniapp` → `https://app.example.com` (container port **3000**)
   - `api` → `https://api.example.com` (container port **8000**)
4. Set `NEXT_PUBLIC_API_BASE=https://api.example.com/api` and
   `MINIAPP_URL=https://app.example.com`, then redeploy so the Mini App bundle
   picks up the API URL (it's inlined at build time).

To enable voice, add `voice` to the compose profiles in the Dokploy UI and set
`ENABLE_VOICE=true`.

---

## Notes

- **Migrations** run in a one-shot `migrate` service that the `bot`/`api` wait
  on (`service_completed_successfully`), so schema changes apply exactly once,
  before the apps start — no migration races.
- **`NEXT_PUBLIC_API_BASE` is build-time.** If you change it, rebuild the
  `miniapp` image.
- **Switching polling ⇄ webhook:** the bot calls `deleteWebhook` on startup when
  polling and `setWebhook` when `WEBHOOK_URL` is set, so flipping the env var is
  all it takes.
