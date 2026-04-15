from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from razdevator.core.enums import (
    Audience,
    BotKind,
    BroadcastScope,
    GenerationFeature,
    GenerationStatus,
    PaymentStatus,
    PaymentProvider,
    StaffRole,
    TransactionDirection,
)


@dataclass(slots=True)
class StaffUser:
    id: int
    telegram_id: int
    username: str | None
    full_name: str
    role: StaffRole
    referral_tag: str
    commission_rate: int
    created_at: datetime

    @property
    def is_owner(self) -> bool:
        return self.role is StaffRole.OWNER


@dataclass(slots=True)
class BotInstance:
    id: int
    bot_id: int | None
    token: str
    username: str | None
    title: str
    kind: BotKind
    audience: Audience
    owner_staff_id: int | None
    is_active: bool
    is_archived: bool
    welcome_text: str | None
    farewell_text: str | None
    hero_media: str | None
    payment_provider: PaymentProvider
    created_at: datetime

    @property
    def start_link(self) -> str:
        if not self.username:
            return ""
        return f"https://t.me/{self.username}"


@dataclass(slots=True)
class EndUserProfile:
    id: int
    bot_instance_id: int
    telegram_id: int
    username: str | None
    full_name: str
    language_code: str
    balance: int
    successful_generations: int
    failed_generations: int
    referred_by_staff_id: int | None
    created_at: datetime


@dataclass(slots=True)
class BotStats:
    total_users: int
    month_users: int
    week_users: int
    today_users: int
    paid_payments: int
    total_payments: int
    month_paid_payments: int
    month_total_payments: int
    week_paid_payments: int
    week_total_payments: int
    today_paid_payments: int
    today_total_payments: int
    earned_cents: int
    total_generations: int


@dataclass(slots=True)
class OwnerStats:
    admins: int
    client_bots: int
    users: int
    generations: int
    revenue_cents: int
    payouts_cents: int


@dataclass(slots=True)
class TemplateItem:
    slug: str
    title_ru: str
    title_en: str
    credits: int
    preview_path: Path | None = None

    def title(self, locale: str) -> str:
        return self.title_ru if locale == "ru" else self.title_en


@dataclass(slots=True)
class GenerationJob:
    id: int
    bot_instance_id: int
    end_user_id: int
    feature: GenerationFeature
    template_slug: str
    status: GenerationStatus
    cost_credits: int
    source_file_id: str | None
    result_file_id: str | None
    error_text: str | None
    created_at: datetime


@dataclass(slots=True)
class BroadcastJob:
    id: int
    scope: BroadcastScope
    bot_instance_id: int | None
    created_by_staff_id: int
    text: str
    media_path: str | None
    created_at: datetime


@dataclass(slots=True)
class PaymentRecord:
    id: int
    bot_instance_id: int
    end_user_id: int
    amount_cents: int
    currency: str
    provider: PaymentProvider
    direction: TransactionDirection
    status: PaymentStatus
    external_id: str | None
    meta_json: str | None
    created_at: datetime
