from __future__ import annotations

from dataclasses import dataclass, field

from razdevator.core.config import Settings
from razdevator.db.database import Database
from razdevator.db.repositories import (
    BotRepository,
    GenerationRepository,
    PaymentRepository,
    SettingsRepository,
    StaffRepository,
    StatsRepository,
    UserRepository,
)
from razdevator.services.generation import GenerationService
from razdevator.services.i18n import I18n
from razdevator.services.media import MediaCatalog
from razdevator.services.payments import PaymentRegistry
from razdevator.services.provisioning import ensure_bootstrap_bots
from razdevator.services.templates import TemplateCatalog


@dataclass(slots=True)
class AppContext:
    settings: Settings
    db: Database
    i18n: I18n
    media: MediaCatalog
    templates: TemplateCatalog
    staff: StaffRepository
    bots: BotRepository
    users: UserRepository
    payments: PaymentRepository
    generations: GenerationRepository
    stats: StatsRepository
    app_settings: SettingsRepository
    payment_registry: PaymentRegistry
    generation_service: GenerationService
    runner: object | None = field(default=None)

    async def bootstrap(self) -> None:
        await self.app_settings.ensure_defaults()
        await ensure_bootstrap_bots(self)

    async def close(self) -> None:
        await self.db.close()


async def build_context(settings: Settings) -> AppContext:
    db = Database(settings.database_path)
    i18n = I18n()
    media = MediaCatalog(settings.assets_dir)
    templates = TemplateCatalog()

    app = AppContext(
        settings=settings,
        db=db,
        i18n=i18n,
        media=media,
        templates=templates,
        staff=StaffRepository(db, settings),
        bots=BotRepository(db, settings),
        users=UserRepository(db),
        payments=PaymentRepository(db),
        generations=GenerationRepository(db),
        stats=StatsRepository(db),
        app_settings=SettingsRepository(db, settings),
        payment_registry=PaymentRegistry(
            settings=settings,
            users=None,
            payments=None,
        ),
        generation_service=GenerationService(
            settings=settings,
            i18n=i18n,
            users=None,
            generations=None,
        ),
    )
    app.payment_registry.users = app.users
    app.payment_registry.payments = app.payments
    app.generation_service.users = app.users
    app.generation_service.generations = app.generations
    return app
