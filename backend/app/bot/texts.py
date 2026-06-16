"""User-facing message strings, kept in one place for easy editing / i18n.

Telegram messages use HTML parse mode. The bot ships in English by default; a
single file makes it trivial to translate or reword the whole UX.
"""

from __future__ import annotations

import html


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
        f"👋 <b>Hi {html.escape(name)}!</b>\n\n"
        "<blockquote>I'm your AI chat assistant — powered by free models via "
        "OpenRouter, with automatic fallback so you're never stuck.</blockquote>\n"
        f"{memory_line}\n"
        f"{extra_block}\n"
        "Just send me a message and let's talk. 💬\n\n"
        "<b>Quick commands</b>\n"
        "• /help — everything I can do\n"
        "• /me — your usage &amp; plan\n"
        "• /model — pick the AI model\n"
        "• /app — open your dashboard\n"
        "• /reset — clear our recent chat\n"
        "• /forget — wipe what I remember about you"
    )


HELP = (
    "🤖 <b>What I can do</b>\n\n"
    "<blockquote>Chat naturally — I keep context and <b>remember you over time</b> "
    "(memory by <a href=\"https://getmem.ai\">GetMem</a>). I run on rotating models "
    "with automatic fallback, understand <b>voice</b>, and on Premium I can read "
    "<b>photos</b> too.</blockquote>\n"
    "<b>Commands</b>\n"
    "/start — intro\n"
    "/me — your plan, usage and remaining messages today\n"
    "/model — choose which AI model answers you\n"
    "/app — open your dashboard (Mini App)\n"
    "/upgrade — unlock premium models &amp; higher limits ⭐\n"
    "/tune — teach me how to behave for you (tunes my style to your goals)\n"
    "/reset — forget the recent chat window (short-term)\n"
    "/forget — erase everything I remember about you (long-term)\n"
    "/help — this message\n\n"
    "🎤 Send a <b>voice message</b> and I'll transcribe and answer it."
)


TUNE_DISABLED = (
    "✋ Personalised behaviour is turned off by the operator, so I can't tune "
    "myself for you right now."
)

TUNE_USAGE = (
    "✍️ Tell me how you'd like me to behave, for example:\n"
    "<code>/tune be my concise running coach — remember my goals and push me</code>\n\n"
    "I'll rewrite my personal style for you using our recent chat and what I "
    "remember about you."
)

TUNE_THINKING = "✍️ Tuning how I respond to you…"

TUNE_FAILED = "😕 Couldn't update that just now. Please try again in a moment."


def tune_done(role: str) -> str:
    # Expandable blockquote (Bot API 10.1 / aiogram 3.29) — long roles collapse.
    return (
        "✅ Done — from now on I'll follow this for you:\n\n"
        f"<blockquote expandable>{html.escape(role)}</blockquote>\n\n"
        "Run /tune again to adjust, or manage it in your dashboard settings."
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
    rows = [
        f"Plan: <b>{plan}</b>",
        f"Today: <b>{used}/{limit}</b>  {bar}",
        f"Model: <code>{html.escape(model)}</code>",
    ]
    if premium_until:
        rows.append(f"Premium until: <b>{premium_until}</b>")
    body = "\n".join(rows)
    return f"👤 <b>Your account</b>\n<blockquote>{body}</blockquote>"


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
    lines = ["⭐ <b>Upgrade your plan</b>\n"]
    for t in tiers:
        name = html.escape(t.name)
        lines.append(
            "<blockquote>"
            f"<b>{name}</b> — <b>{t.price_stars}</b> ⭐ / {t.period_days} days\n"
            f"• Up to <b>{t.daily_limit}</b> messages per day\n"
            f"• <b>{len(t.models)}</b> models incl. premium"
            "</blockquote>"
        )
    lines.append("Pick a plan below to pay with Telegram Stars.")
    return "\n".join(lines)


def payment_title(name: str) -> str:
    return f"{name} plan"


def payment_description(name: str, days: int) -> str:
    return f"{name} plan for {days} days: higher daily limits and more models."


def payment_success(name: str, days: int) -> str:
    safe = html.escape(name)
    return (
        f"🎉 <b>Payment received — welcome to {safe}!</b>\n\n"
        f"<blockquote>You're upgraded for <b>{days}</b> days. Higher limits and "
        "premium models are live.</blockquote>\n"
        "Set your model with /model. Enjoy! ⭐"
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
        "<blockquote>⭐ <b>Premium</b> models (Claude, GPT-4o, Gemini Pro) are far "
        "more reliable and rarely busy — tap /upgrade to skip the queue.</blockquote>\n"
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
        "🛠 <b>Admin panel</b>\n"
        "<blockquote>"
        f"🎤 Voice: <b>{'ON' if voice_on else 'OFF'}</b>\n"
        f"🚫 Disabled models: <b>{disabled_models}</b>\n\n"
        f"👥 Users: <b>{stats['users']}</b> (⭐ {stats['premium']})\n"
        f"💬 Messages today: <b>{stats['messages_today']}</b>\n"
        f"💳 Payments: <b>{stats['payments']}</b>"
        "</blockquote>\n"
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
    body = html.escape(_truncate(prompt, 3500))
    return (
        f"<b>Current system prompt</b> — {src}:\n"
        f"<blockquote expandable>{body}</blockquote>\n"
        "Change it with /setprompt or from the Mini App dashboard."
    )


def admin_prompt_saved(prompt: str) -> str:
    body = html.escape(_truncate(prompt, 3500))
    return (
        "✅ System prompt updated and saved. It applies to all users now.\n"
        f"<blockquote expandable>{body}</blockquote>"
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
VISION_PREMIUM = (
    "🖼 Free models can't read images.\n\n"
    "⭐ <b>Premium</b> unlocks image understanding (e.g. estimating calories from "
    "a photo) — tap /upgrade.\n"
    "<i>No request was used.</i>"
)
VOICE_EMPTY = "🤔 I couldn't make out any speech in that. Mind trying again?"


def voice_heard(text: str) -> str:
    # Escape + quote what we heard (transcripts can contain < & and be long).
    return f"🎤 <blockquote expandable>{html.escape(text)}</blockquote>"


def voice_too_long(max_seconds: int) -> str:
    return (
        f"⚠️ That voice message is too long. Please keep it under "
        f"{max_seconds} seconds."
    )
