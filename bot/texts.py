"""User-facing message strings, kept in one place for easy editing / i18n.

Telegram messages use HTML parse mode. The bot ships in English by default; a
single file makes it trivial to translate or reword the whole UX.
"""

from __future__ import annotations


def start(name: str, memory_on: bool) -> str:
    memory_line = (
        "🧠 I have <b>long-term memory</b> — I'll remember what matters about "
        "you across conversations."
        if memory_on
        else "ℹ️ Long-term memory is currently disabled by the operator."
    )
    return (
        f"👋 Hi {name}!\n\n"
        f"I'm a chat assistant powered by free AI models via OpenRouter.\n"
        f"{memory_line}\n\n"
        "Just send me a message and let's talk.\n\n"
        "Useful commands:\n"
        "• /help — what I can do\n"
        "• /me — your usage & plan\n"
        "• /model — pick the AI model\n"
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
    "/upgrade — unlock premium models &amp; higher limits\n"
    "/reset — forget the recent chat window (short-term)\n"
    "/forget — erase everything I remember about you (long-term)\n"
    "/help — this message"
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


def upgrade_offer(price: int, days: int, limit: int) -> str:
    return (
        "<b>⭐ Premium</b>\n\n"
        f"For <b>{price} Telegram Stars</b> you get, for <b>{days} days</b>:\n"
        f"• Up to <b>{limit}</b> messages per day\n"
        "• Access to premium models (Claude, GPT-4o, Gemini Pro)\n"
        "• Priority model selection\n\n"
        "Tap the button below to pay with Telegram Stars."
    )


PAYMENT_TITLE = "Premium access"


def payment_description(days: int) -> str:
    return f"Premium plan for {days} days: premium models and higher daily limits."


def payment_success(days: int) -> str:
    return (
        "🎉 Payment received — welcome to <b>Premium</b>!\n\n"
        f"You're upgraded for {days} days. Premium models are now available — "
        "set one with /model. Enjoy!"
    )


MODEL_PICK_FREE = "Choose a model (🆓 free pool). Premium models need /upgrade."
MODEL_PICK_PREMIUM = "Choose a model. ⭐ = premium."
MODEL_AUTO = "🔄 Auto (recommended)"
MODEL_SET_AUTO = "✅ Model set to automatic rotation — I'll always pick a working one."


def model_set(model: str) -> str:
    return f"✅ Model set to <code>{model}</code>."


def model_locked() -> str:
    return "🔒 That's a premium model. Unlock it with /upgrade. ⭐"


RESET_DONE = "🧹 Cleared our recent chat window. Long-term memory is untouched."
FORGET_PROMPT = (
    "⚠️ This will permanently erase <b>everything</b> I remember about you "
    "(long-term memory). This cannot be undone. Are you sure?"
)


def forget_done(count: int) -> str:
    return f"🗑️ Done. Erased {count} memories. We're starting fresh."


FORGET_CANCEL = "Cancelled — your memory is safe."
ERROR_GENERIC = (
    "😕 All AI models are busy right now. Please try again in a moment."
)
THINKING = "💭 thinking…"
