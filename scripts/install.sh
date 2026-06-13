#!/usr/bin/env bash
#
# GetMem Telegram Bot — one-command installer.
#
#   curl -fsSL https://raw.githubusercontent.com/getmem-ai/getmem_tg_bot/main/scripts/install.sh | bash
#
# Interactively collects your Telegram token, admin id and API keys, writes a
# .env, and brings the stack up with Docker Compose. Re-runnable and idempotent.
#
# Flags:
#   --non-interactive   Don't prompt; read everything from the environment.
#   --prod              Use the production compose (Caddy auto-HTTPS); needs DOMAIN.
#   --voice             Also start the optional voice (faster-whisper) service.
#   --dir <path>        Install into <path> (default: ./getmem_tg_bot).
#   --no-start          Set up .env but don't build/run (useful for testing).
#   -h, --help          Show help.
#
set -euo pipefail

REPO_URL="https://github.com/getmem-ai/getmem_tg_bot"
RAW_BRANCH="main"

# ---- pretty output ---------------------------------------------------------
if [ -t 1 ]; then
  BOLD=$'\033[1m'; DIM=$'\033[2m'; RED=$'\033[31m'; GRN=$'\033[32m'
  YLW=$'\033[33m'; BLU=$'\033[34m'; RST=$'\033[0m'
else
  BOLD=""; DIM=""; RED=""; GRN=""; YLW=""; BLU=""; RST=""
fi
info()  { printf "%s\n" "${BLU}▸${RST} $*"; }
ok()    { printf "%s\n" "${GRN}✓${RST} $*"; }
warn()  { printf "%s\n" "${YLW}!${RST} $*"; }
err()   { printf "%s\n" "${RED}✗${RST} $*" >&2; }
die()   { err "$*"; exit 1; }

# ---- args ------------------------------------------------------------------
INTERACTIVE=1; MODE="local"; VOICE=0; START=1; TARGET_DIR="getmem_tg_bot"
while [ $# -gt 0 ]; do
  case "$1" in
    --non-interactive) INTERACTIVE=0 ;;
    --prod) MODE="prod" ;;
    --voice) VOICE=1 ;;
    --no-start) START=0 ;;
    --dir) TARGET_DIR="${2:?--dir needs a path}"; shift ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//' | head -n 22; exit 0 ;;
    *) die "Unknown option: $1" ;;
  esac
  shift
done

banner() {
  printf "\n%s\n" "${BOLD}🧠 GetMem Telegram Bot — installer${RST}"
  printf "%s\n\n" "${DIM}memory-first AI bot + Mini App · OpenRouter · Telegram Stars${RST}"
}

# ---- prerequisites ---------------------------------------------------------
need_docker() {
  command -v docker >/dev/null 2>&1 || die \
    "Docker is required. Install it: https://docs.docker.com/get-docker/"
  if docker compose version >/dev/null 2>&1; then
    COMPOSE="docker compose"
  elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE="docker-compose"
  else
    die "Docker Compose is required (Docker Desktop ships it, or install the plugin)."
  fi
  docker info >/dev/null 2>&1 || die "Docker daemon isn't running. Start Docker and retry."
  ok "Docker and Compose detected."
}

gen_secret() {
  if command -v openssl >/dev/null 2>&1; then openssl rand -hex 16
  else head -c 16 /dev/urandom | od -An -tx1 | tr -d ' \n'; fi
}

# ---- fetch the project -----------------------------------------------------
fetch_repo() {
  # Already inside the repo? Use it.
  if [ -f "docker-compose.yml" ] && [ -d "backend" ] && [ -f ".env.example" ]; then
    ok "Using the current directory ($(pwd))."
    return
  fi
  if [ -d "$TARGET_DIR/.git" ] || [ -f "$TARGET_DIR/docker-compose.yml" ]; then
    info "Reusing existing $TARGET_DIR"
  elif command -v git >/dev/null 2>&1; then
    info "Cloning $REPO_URL …"
    git clone --depth 1 "$REPO_URL" "$TARGET_DIR"
  else
    info "Downloading tarball (git not found) …"
    mkdir -p "$TARGET_DIR"
    curl -fsSL "$REPO_URL/archive/refs/heads/$RAW_BRANCH.tar.gz" \
      | tar xz --strip-components=1 -C "$TARGET_DIR"
  fi
  cd "$TARGET_DIR"
  ok "Project ready in $(pwd)"
}

# ---- prompts ---------------------------------------------------------------
# ask <var> <prompt> <default> <secret?>
ask() {
  local var="$1" prompt="$2" def="${3:-}" secret="${4:-0}" cur input
  cur="${!var:-$def}"
  if [ "$INTERACTIVE" = "0" ]; then printf -v "$var" '%s' "$cur"; return; fi
  if [ "$secret" = "1" ]; then
    printf "%s" "  ${prompt}: "; read -rs input; echo
  else
    if [ -n "$cur" ]; then printf "%s" "  ${prompt} ${DIM}[${cur}]${RST}: "
    else printf "%s" "  ${prompt}: "; fi
    read -r input
  fi
  printf -v "$var" '%s' "${input:-$cur}"
}

collect() {
  printf "\n%s\n" "${BOLD}Configuration${RST} ${DIM}(Enter accepts the default)${RST}"
  ask BOT_TOKEN          "Telegram bot token (@BotFather)" "${BOT_TOKEN:-}" 1
  [ -n "${BOT_TOKEN:-}" ] || die "BOT_TOKEN is required."
  ask ADMIN_IDS          "Your Telegram user id (admin)" "${ADMIN_IDS:-}"
  ask OPENROUTER_API_KEY "OpenRouter API key (openrouter.ai/keys)" "${OPENROUTER_API_KEY:-}" 1
  [ -n "${OPENROUTER_API_KEY:-}" ] || die "OPENROUTER_API_KEY is required."
  ask GETMEM_API_KEY     "GetMem memory key gm_live_… (optional, blank = no memory)" "${GETMEM_API_KEY:-}" 1
  if [ "$MODE" = "prod" ]; then
    ask DOMAIN     "Domain for the bot (e.g. bot.example.com)" "${DOMAIN:-}"
    [ -n "${DOMAIN:-}" ] || die "--prod needs a DOMAIN."
    ask ACME_EMAIL "Email for Let's Encrypt" "${ACME_EMAIL:-}"
  fi
  POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-$(gen_secret)}"
  WEBHOOK_SECRET="${WEBHOOK_SECRET:-$(gen_secret)}"
}

write_env() {
  if [ -f .env ]; then
    if [ "$INTERACTIVE" = "1" ]; then
      printf "%s" "  ${YLW}.env exists — overwrite? [y/N]${RST}: "; read -r yn
      case "$yn" in [yY]*) ;; *) warn "Keeping existing .env"; return ;; esac
    else
      warn "Keeping existing .env (non-interactive)"; return
    fi
  fi
  local napi miniapp_url enable_voice="false"
  [ "$VOICE" = "1" ] && enable_voice="true"
  if [ "$MODE" = "prod" ]; then napi="/api"; miniapp_url="https://${DOMAIN}"; else
    napi="http://localhost:8000/api"; miniapp_url=""; fi

  {
    echo "# Generated by install.sh on $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "BOT_TOKEN=${BOT_TOKEN}"
    echo "OPENROUTER_API_KEY=${OPENROUTER_API_KEY}"
    echo "GETMEM_API_KEY=${GETMEM_API_KEY:-}"
    echo "ADMIN_IDS=${ADMIN_IDS:-}"
    echo "APP_NAME=GetMem Telegram Bot"
    echo "MEMORY_TOKEN_BUDGET=1500"
    echo "FREE_DAILY_LIMIT=30"
    echo "PREMIUM_DAILY_LIMIT=500"
    echo "PREMIUM_PRICE_STARS=250"
    echo "PREMIUM_PERIOD_DAYS=30"
    echo "MAX_HISTORY_TURNS=10"
    echo "POSTGRES_USER=getmem"
    echo "POSTGRES_PASSWORD=${POSTGRES_PASSWORD}"
    echo "POSTGRES_DB=getmem_bot"
    echo "POSTGRES_HOST=db"
    echo "POSTGRES_PORT=5432"
    echo "API_PORT=8000"
    echo "MINIAPP_PORT=3000"
    echo "CORS_ORIGINS=*"
    echo "NEXT_PUBLIC_API_BASE=${napi}"
    echo "MINIAPP_URL=${miniapp_url}"
    echo "ENABLE_VOICE=${enable_voice}"
    echo "TRANSCRIBER_URL=http://transcriber:8001"
    if [ "$MODE" = "prod" ]; then
      echo "DOMAIN=${DOMAIN}"
      echo "ACME_EMAIL=${ACME_EMAIL:-}"
      echo "WEBHOOK_URL=https://${DOMAIN}"
      echo "WEBHOOK_SECRET=${WEBHOOK_SECRET}"
    fi
  } > .env
  ok "Wrote .env"
}

launch() {
  local files=(-f docker-compose.yml) profiles=()
  [ "$MODE" = "prod" ] && files=(-f deploy/docker-compose.prod.yml)
  [ "$VOICE" = "1" ] && profiles=(--profile voice)
  if [ "$START" = "0" ]; then
    warn "--no-start: skipping build/up. Run: ${BOLD}${COMPOSE} ${files[*]} ${profiles[*]} up -d --build${RST}"
    return
  fi
  info "Building and starting (this can take a few minutes the first time)…"
  # shellcheck disable=SC2068
  $COMPOSE ${files[@]} --env-file .env ${profiles[@]} up -d --build
  ok "Stack is up."
}

done_msg() {
  printf "\n%s\n" "${GRN}${BOLD}Done!${RST}"
  echo "  • Open Telegram and message your bot."
  if [ "$MODE" = "prod" ]; then
    echo "  • Mini App / dashboard: ${BOLD}https://${DOMAIN}${RST}"
  else
    echo "  • Mini App (local browser): ${BOLD}http://localhost:${MINIAPP_PORT:-3000}${RST}"
    echo "  • Note: Telegram Mini Apps need HTTPS — use a domain (--prod) or a tunnel to open it inside Telegram."
  fi
  echo "  • Logs:  ${DIM}${COMPOSE} logs -f bot${RST}"
  echo "  • Stop:  ${DIM}${COMPOSE} down${RST}"
}

main() {
  banner
  need_docker
  fetch_repo
  collect
  write_env
  launch
  done_msg
}
main
