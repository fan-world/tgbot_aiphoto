from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from razdevator.core.enums import Audience, BotKind

if TYPE_CHECKING:
    from razdevator.core.context import AppContext


async def ensure_bootstrap_bots(app: AppContext) -> None:
    token = app.settings.common_bot_token.strip()
    if not token:
        return

    existing = await app.bots.get_by_token(token)
    if existing is not None:
        if not app.settings.main_bot_link and existing.start_link:
            await app.app_settings.set("main_bot_link", existing.start_link)
        return

    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    try:
        me = await bot.get_me()
    finally:
        await bot.session.close()

    audience = Audience(app.settings.common_bot_audience.lower())
    title = app.settings.common_bot_title.strip() or me.first_name
    created = await app.bots.create_bot_instance(
        token=token,
        bot_id=me.id,
        username=me.username,
        title=title,
        kind=BotKind.COMMON,
        audience=audience,
        owner_staff_id=None,
        hero_media=str(app.media.assets_dir / "client_home.png"),
    )
    if created.start_link:
        await app.app_settings.set("main_bot_link", created.start_link)
