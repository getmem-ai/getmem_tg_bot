"""Premium upgrade flow via Telegram Stars (no external payment provider).

Tiers are admin-defined; any tier with ``price_stars > 0`` is purchasable. Flow:
/upgrade → one button per paid tier → :func:`answer_invoice` (currency ``XTR``)
→ ``pre_checkout_query`` (approve) → ``successful_payment`` → put the user on
that tier for its billing period and record the charge idempotently.
"""

from __future__ import annotations

import datetime as dt
import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)

from ...core import ConfigStore
from ...db import Database, repo
from .. import keyboards, texts

router = Router(name="payments")
log = logging.getLogger(__name__)

_PAYLOAD_PREFIX = "tier:"


@router.message(Command("upgrade"))
async def cmd_upgrade(message: Message, config: ConfigStore) -> None:
    paid = await config.paid_tiers()
    if not paid:
        await message.answer(texts.UPGRADE_NONE)
        return
    await message.answer(
        texts.upgrade_offer(paid),
        reply_markup=keyboards.upgrade_keyboard(paid),
    )


@router.callback_query(F.data.startswith(f"{keyboards.CB_UPGRADE}:"))
async def on_buy(callback: CallbackQuery, config: ConfigStore) -> None:
    if not isinstance(callback.message, Message) or callback.data is None:
        await callback.answer()
        return
    tier_key = callback.data.split(":", 1)[1]
    tiers = await config.tiers()
    tier = tiers.get(tier_key)
    if tier is None or not tier.is_paid:
        await callback.answer("That plan is no longer available.", show_alert=True)
        return
    await callback.message.answer_invoice(
        title=texts.payment_title(tier.name),
        description=texts.payment_description(tier.name, tier.period_days),
        payload=f"{_PAYLOAD_PREFIX}{tier.key}",
        currency="XTR",  # Telegram Stars
        prices=[LabeledPrice(label=tier.name, amount=tier.price_stars)],
        # provider_token is intentionally omitted/empty for Stars payments.
    )
    await callback.answer()


@router.pre_checkout_query()
async def on_pre_checkout(query: PreCheckoutQuery) -> None:
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def on_paid(
    message: Message, config: ConfigStore, db: Database
) -> None:
    if message.from_user is None or message.successful_payment is None:
        return
    sp = message.successful_payment
    tier_key = (
        sp.invoice_payload[len(_PAYLOAD_PREFIX):]
        if sp.invoice_payload.startswith(_PAYLOAD_PREFIX)
        else "premium"
    )
    tiers = await config.tiers()
    tier = tiers.get(tier_key)
    period = tier.period_days if tier else 30
    until = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=period)

    async with db.session() as session:
        await repo.get_or_create_user(
            session,
            message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )
        await repo.set_tier(session, message.from_user.id, tier_key, until)
        # Smart switch: put the new premium user straight on the flagship model
        # so they don't have to hunt for it in /model.
        if tier is not None:
            top = await config.top_model_for_tier(tier)
            if top:
                await repo.set_preferred_model(session, message.from_user.id, top)
        await repo.record_payment(
            session,
            sp.telegram_payment_charge_id,
            message.from_user.id,
            sp.total_amount,
        )
    log.info(
        "tier granted tg=%s tier=%s charge=%s stars=%s",
        message.from_user.id,
        tier_key,
        sp.telegram_payment_charge_id,
        sp.total_amount,
    )
    await message.answer(
        texts.payment_success(tier.name if tier else tier_key, period)
    )
