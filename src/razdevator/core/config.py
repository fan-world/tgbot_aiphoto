from __future__ import annotations

import os
from pathlib import Path

from razdevator.core.enums import PaymentProvider


class Settings:
    def __init__(
        self,
        *,
        admin_bot_token: str | None = None,
        owner_ids_raw: str | None = None,
        database_path: Path | str | None = None,
        default_admin_rate: int | str | None = None,
        main_bot_link: str | None = None,
        common_bot_token: str | None = None,
        common_bot_audience: str | None = None,
        common_bot_title: str | None = None,
        default_ru_payment_provider: PaymentProvider | str | None = None,
        default_en_payment_provider: PaymentProvider | str | None = None,
        platega_base_url: str | None = None,
        platega_merchant_id: str | None = None,
        platega_secret: str | None = None,
        public_base_url: str | None = None,
        webhook_host: str | None = None,
        webhook_port: int | str | None = None,
        platega_webhook_path: str | None = None,
        generation_provider: str | None = None,
        crebots_base_url: str | None = None,
        crebots_api_key: str | None = None,
        assets_dir: Path | str | None = None,
    ) -> None:
        env = load_dotenv()
        self.admin_bot_token = admin_bot_token or os.getenv("ADMIN_BOT_TOKEN") or env.get("ADMIN_BOT_TOKEN", "")
        self.owner_ids_raw = (
            owner_ids_raw
            if owner_ids_raw is not None
            else os.getenv("OWNER_IDS") or env.get("OWNER_IDS", "")
        )
        self.database_path = Path(
            database_path
            or os.getenv("DATABASE_PATH")
            or env.get("DATABASE_PATH", "data/razdevator.sqlite3")
        )
        self.default_admin_rate = int(
            default_admin_rate
            or os.getenv("DEFAULT_ADMIN_RATE")
            or env.get("DEFAULT_ADMIN_RATE", "30")
        )
        self.main_bot_link = (
            main_bot_link
            if main_bot_link is not None
            else os.getenv("MAIN_BOT_LINK") or env.get("MAIN_BOT_LINK", "")
        )
        self.common_bot_token = (
            common_bot_token
            if common_bot_token is not None
            else os.getenv("COMMON_BOT_TOKEN") or env.get("COMMON_BOT_TOKEN", "")
        )
        self.common_bot_audience = (
            common_bot_audience
            if common_bot_audience is not None
            else os.getenv("COMMON_BOT_AUDIENCE") or env.get("COMMON_BOT_AUDIENCE", "ru")
        )
        self.common_bot_title = (
            common_bot_title
            if common_bot_title is not None
            else os.getenv("COMMON_BOT_TITLE") or env.get("COMMON_BOT_TITLE", "")
        )
        self.default_ru_payment_provider = PaymentProvider(
            default_ru_payment_provider
            or os.getenv("DEFAULT_RU_PAYMENT_PROVIDER")
            or env.get("DEFAULT_RU_PAYMENT_PROVIDER", "manual")
        )
        self.default_en_payment_provider = PaymentProvider(
            default_en_payment_provider
            or os.getenv("DEFAULT_EN_PAYMENT_PROVIDER")
            or env.get("DEFAULT_EN_PAYMENT_PROVIDER", "manual")
        )
        self.platega_base_url = (
            platega_base_url
            or os.getenv("PLATEGA_BASE_URL")
            or env.get("PLATEGA_BASE_URL", "https://app.platega.io")
        ).rstrip("/")
        self.platega_merchant_id = (
            platega_merchant_id
            if platega_merchant_id is not None
            else os.getenv("PLATEGA_MERCHANT_ID") or env.get("PLATEGA_MERCHANT_ID", "")
        )
        self.platega_secret = (
            platega_secret
            if platega_secret is not None
            else os.getenv("PLATEGA_SECRET") or env.get("PLATEGA_SECRET", "")
        )
        self.public_base_url = (
            public_base_url
            if public_base_url is not None
            else os.getenv("PUBLIC_BASE_URL") or env.get("PUBLIC_BASE_URL", "")
        ).rstrip("/")
        self.webhook_host = (
            webhook_host
            if webhook_host is not None
            else os.getenv("WEBHOOK_HOST") or env.get("WEBHOOK_HOST", "0.0.0.0")
        )
        self.webhook_port = int(
            webhook_port
            or os.getenv("WEBHOOK_PORT")
            or env.get("WEBHOOK_PORT", "8081")
        )
        raw_webhook_path = (
            platega_webhook_path
            if platega_webhook_path is not None
            else os.getenv("PLATEGA_WEBHOOK_PATH")
            or env.get("PLATEGA_WEBHOOK_PATH", "/webhooks/platega/payment-status")
        )
        self.platega_webhook_path = raw_webhook_path if raw_webhook_path.startswith("/") else f"/{raw_webhook_path}"
        self.generation_provider = (
            generation_provider
            or os.getenv("GENERATION_PROVIDER")
            or env.get("GENERATION_PROVIDER", "stub")
        )
        self.crebots_base_url = (
            crebots_base_url
            or os.getenv("CREBOTS_BASE_URL")
            or env.get("CREBOTS_BASE_URL", "https://api.crebots.com/api")
        ).rstrip("/")
        self.crebots_api_key = (
            crebots_api_key
            if crebots_api_key is not None
            else os.getenv("CREBOTS_API_KEY") or env.get("CREBOTS_API_KEY", "")
        )
        self.assets_dir = Path(
            assets_dir
            or os.getenv("ASSETS_DIR")
            or env.get("ASSETS_DIR", "src/razdevator/assets/screens")
        )

    @classmethod
    def model_construct(cls, **values: object) -> "Settings":
        return cls(**values)

    @property
    def owner_ids(self) -> set[int]:
        values = {
            int(item.strip())
            for item in self.owner_ids_raw.split(",")
            if item.strip()
        }
        return values

    @property
    def platega_configured(self) -> bool:
        return bool(self.platega_merchant_id and self.platega_secret)

    @property
    def platega_webhook_url(self) -> str:
        if not self.public_base_url:
            return ""
        return f"{self.public_base_url}{self.platega_webhook_path}"

    @property
    def crebots_configured(self) -> bool:
        return bool(self.crebots_api_key)


def load_dotenv(path: str = ".env") -> dict[str, str]:
    env_path = Path(path)
    if not env_path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values
