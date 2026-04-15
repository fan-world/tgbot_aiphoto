from __future__ import annotations

from enum import Enum


class StrEnum(str, Enum):
    pass


class StaffRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"


class BotKind(StrEnum):
    COMMON = "common"
    PERSONAL = "personal"


class Audience(StrEnum):
    RU = "ru"
    EN = "en"


class PaymentProvider(StrEnum):
    MANUAL = "manual"
    PLATEGA = "platega"
    CRYPTOBOT = "cryptobot"
    TELEGRAM_STARS = "telegram_stars"
    STRIPE = "stripe"
    YOOKASSA = "yookassa"


class TransactionDirection(StrEnum):
    DEPOSIT = "deposit"
    EXPENSE = "expense"
    REVENUE = "revenue"
    PAYOUT = "payout"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    PAID = "paid"
    CANCELED = "canceled"
    FAILED = "failed"


class BroadcastScope(StrEnum):
    GLOBAL = "global"
    BOT = "bot"


class GenerationFeature(StrEnum):
    IMAGE_TO_VIDEO = "image_to_video"
    AUDIO_IMAGE_TO_VIDEO = "audio_image_to_video"


class GenerationStatus(StrEnum):
    WAITING_PHOTO = "waiting_photo"
    QUEUED = "queued"
    DONE = "done"
    FAILED = "failed"
