"""User-facing message strings, kept in one place for easy editing / i18n.

Telegram messages use HTML parse mode. The bot ships in English by default; a
single file makes it trivial to translate or reword the whole UX.
"""

from __future__ import annotations


def start(
    name: str, memory_on: bool, voice_on: bool = False, vision_on: bool = False
) -> str:
    memory_line = (
        "🧠 I have <b>long-term memory</b> — I'll remember what matters about "
        "you across conversations."
        if memory_on
        else "ℹ️ Long-term memory is currently disabled by the operator."
    )
    extras = []
    if voice_on:
        extras.append("🎤 You can send me <b>voice messages</b>.")
    if vision_on:
        extras.append("🖼 You can send me <b>photos</b> and I'll read them.")
    extra_block = ("\n".join(extras) + "\n") if extras else ""
    return (
        f"👋 Hi {name}!\n\n"
        f"I'm a chat assistant powered by free AI models via OpenRouter.\n"
        f"{memory_line}\n"
        f"{extra_block}\n"
        "Just send me a message and let's talk.\n\n"
        "Useful commands:\n"
        "• /help — what I can do\n"
        "• /me — your usage & plan\n"
        "• /model — pick the AI model\n"
        "• /app — open your dashboard\n"
        "• /reset — clear our recent chat history\n"
        "• /forget — wipe everything I remember about you"
    )


HELP = (
    "<b>What I can do</b>\n\n"
    "💬 Chat naturally — I keep context and remember you over time.\n"
    "🧠 Memory is powered by <a href=\"https://getmem.ai\">GetMem</a>.\n"
    "🤖 I run on rotating free models and fall back automatically.\n\n"
    "<b>Commands</b>\n"
    "/start — intro\n"
    "/me — your plan, usage and remaining messages today\n"
    "/model — choose which AI model answers you\n"
    "/app — open your dashboard (Mini App)\n"
    "/upgrade — unlock premium models &amp; higher limits\n"
    "/reset — forget the recent chat window (short-term)\n"
    "/forget — erase everything I remember about you (long-term)\n"
    "/help — this message\n\n"
    "🎤 Send a <b>voice message</b> and I'll transcribe and answer it."
)


def me(
    *,
    tier: str,
    used: int,
    limit: int,
    model: str,
    premium_until: str | None,
) -> str:
    bar_total = 10
    filled = 0 if limit <= 0 else min(bar_total, round(used / limit * bar_total))
    bar = "▰" * filled + "▱" * (bar_total - filled)
    plan = "⭐ Premium" if tier == "premium" else "🆓 Free"
    lines = [
        "<b>Your account</b>",
        f"Plan: {plan}",
        f"Today: {used}/{limit}  {bar}",
        f"Model: <code>{model}</code>",
    ]
    if premium_until:
        lines.append(f"Premium until: {premium_until}")
    return "\n".join(lines)


def limit_reached(tier: str, limit: int) -> str:
    if tier == "premium":
        return (
            f"⚠️ You've reached your daily limit of {limit} messages. "
            "It resets in under 24h. Thanks for being a premium user!"
        )
    return (
        f"⚠️ You've hit the free daily limit of {limit} messages.\n\n"
        "It resets every day. Want more — plus access to premium models like "
        "Claude and GPT-4o? Tap /upgrade. ⭐"
    )


UPGRADE_NONE = (
    "There are no paid plans configured yet. You're on the free plan — enjoy!"
)


def upgrade_offer(tiers: list) -> str:  # list[TierConfig]
    lines = ["<b>⭐ Upgrade your plan</b>\n"]
    for t in tiers:
        lines.append(
            f"<b>{t.name}</b> — {t.price_stars} Stars / {t.period_days} days\n"
            f"• Up to <b>{t.daily_limit}</b> messages per day\n"
            f"• {len(t.models)} models incl. premium\n"
        )
    lines.append("Pick a plan below to pay with Telegram Stars.")
    return "\n".join(lines)


def payment_title(name: str) -> str:
    return f"{name} plan"


def payment_description(name: str, days: int) -> str:
    return f"{name} plan for {days} days: higher daily limits and more models."


def payment_success(name: str, days: int) -> str:
    return (
        f"🎉 Payment received — welcome to <b>{name}</b>!\n\n"
        f"You're upgraded for {days} days. Set a model with /model. Enjoy!"
    )


MODEL_PICK = "Choose a model, or keep Auto so I always pick a working one:"
MODEL_AUTO = "🔄 Auto (recommended)"
MODEL_SET_AUTO = "✅ Model set to automatic rotation — I'll always pick a working one."


def model_set(model: str) -> str:
    return f"✅ Model set to <code>{model}</code>."


def model_locked_alert() -> str:
    return "🔒 That's a premium model. Unlock it with /upgrade."


RESET_DONE = "🧹 Cleared our recent chat window. Long-term memory is untouched."
FORGET_PROMPT = (
    "⚠️ This will permanently erase <b>everything</b> I remember about you "
    "(long-term memory). This cannot be undone. Are you sure?"
)


def forget_done(count: int) -> str:
    return f"🗑️ Done. Erased {count} memories. We're starting fresh."


FORGET_CANCEL = "Cancelled — your memory is safe."
THINKING = "💭 Thinking…"
# Shown if generation is slow — a gentle italic nudge for free users.
THINKING_UPSELL = (
    "💭 Thinking…\n\n"
    "<i>Tip: Premium plans use faster, more reliable models — /upgrade ⭐</i>"
)
ERROR_GENERIC = (
    "😕 Something went wrong on my side. Please try again in a moment."
)
BANNED = "🚫 Your access to this bot has been suspended."
PAUSED = "⏸️ The bot is temporarily paused for maintenance. Please try again soon."


def all_busy(is_premium: bool) -> str:
    """Shown when every model in the user's pool is unavailable."""
    if is_premium:
        return (
            "😕 The models are momentarily busy. Please try again in a few "
            "seconds — your premium models usually free up quickly."
        )
    return (
        "😕 All the free models are busy right now.\n\n"
        "⭐ <b>Premium</b> models (Claude, GPT-4o, Gemini Pro) are far more "
        "reliable and rarely busy — tap /upgrade to skip the queue.\n"
        "Otherwise, please try again in a minute."
    )

# -- Mini App -----------------------------------------------------------------
OPEN_APP_BUTTON = "📊 Open dashboard"
APP_OPEN = "Tap below to open your dashboard — usage, history and your plan."
APP_DISABLED = (
    "The dashboard isn't configured on this deployment yet. "
    "Set MINIAPP_URL to enable it."
)

# -- Admin --------------------------------------------------------------------
def admin_panel(*, voice_on: bool, disabled_models: int, stats: dict[str, int]) -> str:
    return (
        "<b>🛠 Admin panel</b>\n\n"
        f"🎤 Voice: <b>{'ON' if voice_on else 'OFF'}</b>\n"
        f"🚫 Disabled models: <b>{disabled_models}</b>\n\n"
        f"👥 Users: {stats['users']} (⭐ {stats['premium']})\n"
        f"💬 Messages today: {stats['messages_today']}\n"
        f"💳 Payments: {stats['payments']}\n\n"
        "Use the buttons below to manage the bot live.\n"
        "✏️ System prompt: /getprompt · /setprompt &lt;text&gt;"
    )


ADMIN_ONLY = "🚫 Admins only."
ADMIN_MODELS_TITLE = "Tap a model to enable/disable it in the rotation:"
ADMIN_SETPROMPT_USAGE = (
    "Usage: <code>/setprompt &lt;new system prompt&gt;</code>\n\n"
    "Everything after the command becomes the bot's persona/system prompt. "
    "It's stored in the database and applies to all users immediately."
)


def admin_prompt_show(prompt: str, is_default: bool) -> str:
    src = "default (from env)" if is_default else "custom (stored in DB)"
    return (
        f"<b>Current system prompt</b> — {src}:\n\n"
        f"<code>{_truncate(prompt, 3500)}</code>\n\n"
        "Change it with /setprompt or from the Mini App dashboard."
    )


def admin_prompt_saved(prompt: str) -> str:
    return (
        "✅ System prompt updated and saved. It applies to all users now.\n\n"
        f"<code>{_truncate(prompt, 3500)}</code>"
    )


def _truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def admin_voice_toggled(on: bool) -> str:
    return f"🎤 Voice is now {'ON' if on else 'OFF'}."


def admin_model_toggled(model: str, enabled: bool) -> str:
    state = "enabled" if enabled else "disabled"
    return f"{'✅' if enabled else '🚫'} {model} {state}."


# -- Voice --------------------------------------------------------------------
VOICE_DISABLED = "🎤 Voice messages aren't enabled on this bot."
VISION_DISABLED = "🖼 Image understanding isn't enabled on this bot."
VOICE_EMPTY = "🤔 I couldn't make out any speech in that. Mind trying again?"


def voice_heard(text: str) -> str:
    return f"🎤 <i>{text}</i>"


def voice_too_long(max_seconds: int) -> str:
    return (
        f"⚠️ That voice message is too long. Please keep it under "
        f"{max_seconds} seconds."
    )
