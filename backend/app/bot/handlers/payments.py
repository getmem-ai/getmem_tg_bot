"""Premium upgrade flow via Telegram Stars (no external payment provider).

Flow: /upgrade → "Pay N Stars" button → :func:`answer_invoice` (currency
``XTR``) → ``pre_checkout_query`` (approve) → ``successful_payment`` (grant
premium + record the charge idempotently).
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

from ...config import Settings
from ...db import Database, repo
from .. import keyboards, texts

router = Router(name="payments")
log = logging.getLogger(__name__)

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
    if not isinstance(callback.message, Message):
        await callback.answer()
        return
    await callback.message.answer_invoice(
        title=texts.PAYMENT_TITLE,
        description=texts.payment_description(settings.premium_period_days),
        payload=_PAYLOAD,
        currency="XTR",  # Telegram Stars
        prices=[
            LabeledPrice(
                label=texts.PAYMENT_TITLE, amount=settings.premium_price_stars
            )
        ],
        # provider_token is intentionally omitted/empty for Stars payments.
    )
    await callback.answer()


@router.pre_checkout_query()
async def on_pre_checkout(query: PreCheckoutQuery) -> None:
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def on_paid(message: Message, settings: Settings, db: Database) -> None:
    if message.from_user is None or message.successful_payment is None:
        return
    sp = message.successful_payment
    until = dt.datetime.now(dt.timezone.utc) + dt.timedelta(
        days=settings.premium_period_days
    )
    async with db.session() as session:
        await repo.get_or_create_user(
            session,
            message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )
        await repo.grant_premium(session, message.from_user.id, until)
        await repo.record_payment(
            session,
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
