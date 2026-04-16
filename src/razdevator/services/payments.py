from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Any

from razdevator.core.config import Settings
from razdevator.core.enums import Audience, PaymentProvider, PaymentStatus, TransactionDirection
from razdevator.core.models import BotInstance, EndUserProfile, PaymentRecord
from razdevator.db.repositories import PaymentRepository, UserRepository


class PaymentError(Exception):
    pass


class PaymentNotConfiguredError(PaymentError):
    pass


@dataclass(slots=True)
class TopUpPackage:
    slug: str
    credits: int
    amount_cents: int

    def title(self) -> str:
        return f"{self.credits}💎"


@dataclass(slots=True)
class PaymentQuote:
    amount_cents: int
    currency: str
    provider: PaymentProvider
    text: str


@dataclass(slots=True)
class CheckoutSession:
    provider: PaymentProvider
    channel: str
    transaction_id: str
    status: str
    redirect_url: str | None
    amount_cents: int
    currency: str
    expires_in: str | None
    payment_method: str | None
    amount_usdt: float | None = None
    usdt_rate: float | None = None
    qr_bytes: bytes | None = None
    qr_url: str | None = None
    payment_details: str | None = None
    description: str | None = None


class PaymentRegistry:
    """Упрощённая регистрация платежей для открытой/free-версии.

    Вместо реальных платёжных провайдеров пополнение происходит мгновенно:
    - создаётся запись в таблице payments со статусом PAID
    - пользователю начисляются кредиты

    Это избавляет проект от внешних провайдеров и валютных конверсий,
    в то же время сохраняя внутреннюю модель платежей (записи в БД).
    """

    def __init__(
        self,
        settings: Settings,
        users: UserRepository | None,
        payments: PaymentRepository | None,
    ) -> None:
        self.settings = settings
        self.users = users
        self.payments = payments
        self._packages = [
            TopUpPackage("mini", credits=100, amount_cents=1000),
            TopUpPackage("standard", credits=300, amount_cents=2500),
            TopUpPackage("max", credits=700, amount_cents=5000),
        ]

    def provider_for_audience(self, audience: Audience) -> PaymentProvider:
        # Для бесплатной версии используем MANUAL как метку
        return PaymentProvider.MANUAL

    def packages_for(self, audience: Audience) -> list[TopUpPackage]:
        return list(self._packages)

    def get_package(self, slug: str) -> TopUpPackage | None:
        return next((item for item in self._packages if item.slug == slug), None)

    def quote(self, audience: Audience, amount_cents: int, locale: str) -> PaymentQuote:
        # Без валюты — показываем, что пакет бесплатный
        provider = self.provider_for_audience(audience)
        text = f"FREE"
        return PaymentQuote(
            amount_cents=amount_cents,
            currency="",
            provider=provider,
            text=text,
        )

    async def create_ru_checkout(
        self,
        *,
        bot_instance: BotInstance,
        profile: EndUserProfile,
        package: TopUpPackage,
        channel: str,
    ) -> CheckoutSession:
        # В бесплатной версии сразу начисляем кредиты и отмечаем платёж как PAID
        if self.payments is None or self.users is None:
            raise RuntimeError("Repositories are not attached to payment registry.")

        transaction_id = f"free-{uuid.uuid4().hex}"
        meta = json.dumps({"bot_instance_id": bot_instance.id, "end_user_id": profile.id, "credits": package.credits, "package_slug": package.slug, "channel": channel}, separators=(",", ":"))
        await self.payments.create_payment(
            bot_instance_id=bot_instance.id,
            end_user_id=profile.id,
            amount_cents=package.amount_cents,
            currency="",
            provider=PaymentProvider.MANUAL,
            direction=TransactionDirection.DEPOSIT,
            status=PaymentStatus.PAID,
            external_id=transaction_id,
            meta_json=meta,
        )
        await self.users.add_balance(profile.id, package.credits)
        return CheckoutSession(
            provider=PaymentProvider.MANUAL,
            channel=channel,
            transaction_id=transaction_id,
            status=PaymentStatus.PAID.value,
            redirect_url=None,
            amount_cents=package.amount_cents,
            currency="",
            expires_in=None,
            payment_method=None,
        )

    async def refresh_ru_checkout(self, transaction_id: str) -> tuple[CheckoutSession, PaymentRecord | None]:
        # Возвращаем запись из БД, если есть
        if self.payments is None:
            raise RuntimeError("Payment repository is not attached.")
        record = await self.payments.get_payment_by_external_id(transaction_id)
        session = CheckoutSession(
            provider=PaymentProvider.MANUAL,
            channel=("qr" if record is None else (json.loads(record.meta_json).get("channel") if record.meta_json else "qr")),
            transaction_id=transaction_id,
            status=(record.status.value if record else PaymentStatus.PENDING.value),
            redirect_url=None,
            amount_cents=(record.amount_cents if record else 0),
            currency=(record.currency if record else ""),
            expires_in=None,
            payment_method=None,
        )
        return session, record

    async def process_platega_callback(self, payload: dict[str, Any]) -> PaymentRecord | None:
        # В бесплатной версии внешние callbacks не используются
        return None

    async def _apply_status_transition(self, record: PaymentRecord | None, payload: dict[str, Any]) -> None:
        # Метод оставлен для совместимости, но в free-режиме платёж уже считается обработанным
        return

    def _channel_from_payment(self, record: PaymentRecord | None) -> str:
        if record is None or not record.meta_json:
            return "qr"
        try:
            payload = json.loads(record.meta_json)
        except json.JSONDecodeError:
            return "qr"
        return str(payload.get("channel") or "qr")


def map_external_status(status: str) -> PaymentStatus:
    if status == "CONFIRMED":
        return PaymentStatus.PAID
    if status in {"CANCELED", "CHARGEBACK", "CHARGEBACKED"}:
        return PaymentStatus.CANCELED
    return PaymentStatus.PENDING


def extract_credits(meta_json: str | None) -> int:
    if not meta_json:
        return 0
    try:
        payload = json.loads(meta_json)
    except json.JSONDecodeError:
        return 0
    try:
        return int(payload.get("credits") or 0)
    except (TypeError, ValueError):
        return 0


def try_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
