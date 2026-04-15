from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any

from aiohttp import ClientSession

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


class PlategaClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def base_url(self) -> str:
        return self.settings.platega_base_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        if not self.settings.platega_configured:
            raise PaymentNotConfiguredError("Platega merchant credentials are missing.")
        return {
            "accept": "application/json",
            "Content-Type": "application/json",
            "X-MerchantId": self.settings.platega_merchant_id,
            "X-Secret": self.settings.platega_secret,
        }

    async def create_transaction(
        self,
        *,
        amount_rub: int,
        description: str,
        return_url: str,
        failed_url: str,
        payload: str,
    ) -> dict[str, Any]:
        body = {
            "paymentMethod": 2,
            "paymentDetails": {
                "amount": amount_rub,
                "currency": "RUB",
            },
            "description": description,
            "return": return_url,
            "failedUrl": failed_url,
            "payload": payload,
        }
        async with ClientSession(headers=self._headers()) as session:
            async with session.post(f"{self.base_url}/transaction/process", json=body) as response:
                if response.status >= 400:
                    raise PaymentError(await response.text())
                return await response.json()

    async def fetch_transaction(self, transaction_id: str) -> dict[str, Any]:
        async with ClientSession(headers=self._headers()) as session:
            async with session.get(f"{self.base_url}/transaction/{transaction_id}") as response:
                if response.status >= 400:
                    raise PaymentError(await response.text())
                return await response.json()


class PaymentRegistry:
    def __init__(
        self,
        settings: Settings,
        users: UserRepository | None,
        payments: PaymentRepository | None,
    ) -> None:
        self.settings = settings
        self.users = users
        self.payments = payments
        self.platega = PlategaClient(settings)
        self._packages = [
            TopUpPackage("mini", credits=100, amount_cents=1000),
            TopUpPackage("standard", credits=300, amount_cents=2500),
            TopUpPackage("max", credits=700, amount_cents=5000),
        ]

    def provider_for_audience(self, audience: Audience) -> PaymentProvider:
        if audience is Audience.RU:
            return self.settings.default_ru_payment_provider
        return self.settings.default_en_payment_provider

    def packages_for(self, audience: Audience) -> list[TopUpPackage]:
        return list(self._packages)

    def get_package(self, slug: str) -> TopUpPackage | None:
        return next((item for item in self._packages if item.slug == slug), None)

    def quote(self, audience: Audience, amount_cents: int, locale: str) -> PaymentQuote:
        provider = self.provider_for_audience(audience)
        currency = "RUB" if audience is Audience.RU else "USD"
        amount = amount_cents / 100
        if locale == "ru":
            text = f"{amount:.2f} {currency} через {provider.value}"
        else:
            text = f"{amount:.2f} {currency} via {provider.value}"
        return PaymentQuote(
            amount_cents=amount_cents,
            currency=currency,
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
        if bot_instance.payment_provider is not PaymentProvider.PLATEGA:
            raise PaymentError("This RU bot is not configured to use Platega.")

        amount_rub = max(1, round(package.amount_cents / 100))
        payload = json.dumps(
            {
                "bot_instance_id": bot_instance.id,
                "end_user_id": profile.id,
                "credits": package.credits,
                "package_slug": package.slug,
                "channel": channel,
            },
            separators=(",", ":"),
        )
        description = f"Пополнение баланса {package.credits} монет для {profile.telegram_id}"
        return_url = bot_instance.start_link or self.settings.main_bot_link or "https://t.me"
        failed_url = return_url

        created = await self.platega.create_transaction(
            amount_rub=amount_rub,
            description=description,
            return_url=return_url,
            failed_url=failed_url,
            payload=payload,
        )
        transaction_id = str(created["transactionId"])
        details = await self.platega.fetch_transaction(transaction_id)

        if self.payments is None:
            raise RuntimeError("Payment repository is not attached.")
        await self.payments.create_payment(
            bot_instance_id=bot_instance.id,
            end_user_id=profile.id,
            amount_cents=package.amount_cents,
            currency="RUB",
            provider=PaymentProvider.PLATEGA,
            direction=TransactionDirection.DEPOSIT,
            status=PaymentStatus.PENDING,
            external_id=transaction_id,
            meta_json=payload,
        )
        return self._build_checkout_session(
            created=created,
            details=details,
            amount_cents=package.amount_cents,
            channel=channel,
        )

    async def refresh_ru_checkout(self, transaction_id: str) -> tuple[CheckoutSession, PaymentRecord | None]:
        details = await self.platega.fetch_transaction(transaction_id)
        if self.payments is None:
            raise RuntimeError("Payment repository is not attached.")
        record = await self.payments.get_payment_by_external_id(transaction_id)
        session = self._build_checkout_session(
            created=details,
            details=details,
            amount_cents=record.amount_cents if record else 0,
            channel=self._channel_from_payment(record),
        )
        await self._apply_status_transition(record, details)
        refreshed = await self.payments.get_payment_by_external_id(transaction_id)
        return session, refreshed

    async def process_platega_callback(self, payload: dict[str, Any]) -> PaymentRecord | None:
        transaction_id = str(payload.get("id") or "")
        if not transaction_id or self.payments is None:
            return None
        record = await self.payments.get_payment_by_external_id(transaction_id)
        await self._apply_status_transition(record, payload)
        return await self.payments.get_payment_by_external_id(transaction_id)

    def _build_checkout_session(
        self,
        *,
        created: dict[str, Any],
        details: dict[str, Any],
        amount_cents: int,
        channel: str,
    ) -> CheckoutSession:
        qr_value = details.get("qr")
        qr_bytes, qr_url = decode_qr_payload(qr_value)
        amount_usdt = try_float(details.get("amountUsdt"))
        usdt_rate = try_float(details.get("usdtRate") or created.get("usdtRate"))
        return CheckoutSession(
            provider=PaymentProvider.PLATEGA,
            channel=channel,
            transaction_id=str(created.get("transactionId") or details.get("id") or ""),
            status=str(details.get("status") or created.get("status") or "PENDING"),
            redirect_url=created.get("redirect") or details.get("payformSuccessUrl"),
            amount_cents=amount_cents,
            currency="RUB",
            expires_in=details.get("expiresIn") or created.get("expiresIn"),
            payment_method=details.get("paymentMethod") or created.get("paymentMethod"),
            amount_usdt=amount_usdt,
            usdt_rate=usdt_rate,
            qr_bytes=qr_bytes if channel == "qr" else None,
            qr_url=qr_url if channel == "qr" else None,
            payment_details=created.get("paymentDetails"),
            description=details.get("description"),
        )

    async def _apply_status_transition(
        self,
        record: PaymentRecord | None,
        payload: dict[str, Any],
    ) -> None:
        if record is None or self.payments is None:
            return

        raw_status = str(payload.get("status") or "").upper()
        target_status = map_external_status(raw_status)
        await self.payments.update_status_by_external_id(record.external_id or "", target_status)

        if (
            target_status is PaymentStatus.PAID
            and record.status is not PaymentStatus.PAID
            and self.users is not None
        ):
            credits = extract_credits(record.meta_json)
            if credits > 0:
                await self.users.add_balance(record.end_user_id, credits)

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


def decode_qr_payload(value: Any) -> tuple[bytes | None, str | None]:
    if not value:
        return None, None
    if not isinstance(value, str):
        return None, None
    stripped = value.strip()
    if stripped.startswith("http://") or stripped.startswith("https://"):
        return None, stripped
    if stripped.startswith("data:image"):
        _, _, stripped = stripped.partition(",")
    try:
        return base64.b64decode(stripped), None
    except Exception:
        return None, None


def try_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
