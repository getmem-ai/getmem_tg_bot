# Production deployment (domain + automatic HTTPS)

Most people should just use **long polling** — it needs no domain, no open
ports and no certificates:

```bash
cp .env.example .env   # then edit
docker compose up -d --build
```

Use the **webhook** setup below only if you specifically want Telegram to push
updates to a public HTTPS endpoint (e.g. lower latency, or running many bots
behind one proxy). It uses [Caddy](https://caddyserver.com/) to obtain and renew
a Let's Encrypt certificate for your domain automatically — no `certbot`, no
manual cert files.

## 1. Point a domain at the server

Create a DNS **A record** (e.g. `bot.example.com`) pointing at your server's
public IP. Make sure ports **80** and **443** are open.

## 2. Configure `.env`

In addition to the usual keys, set:

```env
WEBHOOK_URL=https://bot.example.com
WEBHOOK_SECRET=<paste: openssl rand -hex 32>
DOMAIN=bot.example.com
ACME_EMAIL=you@example.com
```

When `WEBHOOK_URL` is set the bot automatically switches from polling to webhook
mode and registers the webhook with Telegram on startup.

## 3. Launch

From the repository root:

```bash
docker compose -f deploy/docker-compose.prod.yml --env-file .env up -d --build
```

Caddy issues the certificate on first start (give it a few seconds), then
reverse-proxies `https://bot.example.com/webhook` to the bot.

## 4. Verify

```bash
docker compose -f deploy/docker-compose.prod.yml logs -f bot
```

You should see `Webhook set to https://bot.example.com/webhook`. Message your
bot to confirm.

### Switching back to polling

Unset `WEBHOOK_URL` (or run the default `docker compose up -d`). The bot calls
`deleteWebhook` on startup when polling, so there's nothing else to clean up.

## How TLS works here

- The bot container speaks plain HTTP on port `8080` (never exposed publicly).
- Caddy terminates TLS on `443`, manages the Let's Encrypt cert lifecycle, and
  proxies to the bot. Certificates live in the `caddy-data` volume and renew
  automatically.
