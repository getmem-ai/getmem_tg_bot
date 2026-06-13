"""Premium upgrade flow via Telegram Stars (no external payment provider).

Telegram Stars (currency ``XTR``) lets a bot sell digital goods directly, with
an empty ``provider_token``. Flow:

1. /upgrade → offer message with a "Pay N Stars" button.
2. button → :func:`send_invoice` with an ``XTR`` price.
3. Telegram asks our bot to confirm via ``pre_checkout_query`` → we approve.
4. On success Telegram sends a ``successful_payment`` message → we grant premium.
"""

from __future__ import annotations

import logging
import time

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)

from .. import keyboards, texts
from ..config import Settings
from ..storage import Storage

router = Router(name="payments")
log = logging.getLogger(__name__)

# Payload that ties a successful payment back to this product.
_PAYLOAD = "premium_subscription"


@router.message(Command("upgrade"))
async def cmd_upgrade(message: Message, settings: Settings) -> None:
    await message.answer(
        texts.upgrade_offer(
            settings.premium_price_stars,
            settings.premium_period_days,
            settings.premium_daily_limit,
        ),
        reply_markup=keyboards.upgrade_keyboard(settings.premium_price_stars),
    )


@router.callback_query(F.data == f"{keyboards.CB_UPGRADE}:buy")
async def on_buy(callback: CallbackQuery, settings: Settings) -> None:
    if callback.message is None:
        return
    await callback.message.answer_invoice(
        title=texts.PAYMENT_TITLE,
        description=texts.payment_description(settings.premium_period_days),
        payload=_PAYLOAD,
        currency="XTR",  # Telegram Stars
        prices=[
            LabeledPrice(
                label=texts.PAYMENT_TITLE,
                amount=settings.premium_price_stars,
            )
        ],
        # provider_token is intentionally omitted/empty for Stars payments.
    )
    await callback.answer()


@router.pre_checkout_query()
async def on_pre_checkout(query: PreCheckoutQuery) -> None:
    # Nothing to validate server-side for a flat digital product — approve.
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def on_paid(message: Message, settings: Settings, storage: Storage) -> None:
    if message.from_user is None or message.successful_payment is None:
        return
    sp = message.successful_payment
    until = int(time.time()) + settings.premium_period_days * 86_400
    await storage.grant_premium(message.from_user.id, until)
    await storage.record_payment(
        sp.telegram_payment_charge_id,
        message.from_user.id,
        sp.total_amount,
    )
    log.info(
        "premium granted tg=%s charge=%s stars=%s",
        message.from_user.id,
        sp.telegram_payment_charge_id,
        sp.total_amount,
    )
    await message.answer(texts.payment_success(settings.premium_period_days))
