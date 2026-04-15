from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, User

from razdevator.core.context import AppContext
from razdevator.services.screens import ScreenRenderer


class AppContextMiddleware(BaseMiddleware):
    def __init__(self, app: AppContext) -> None:
        self.app = app
        self.renderer = ScreenRenderer()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["app"] = self.app
        data["screen_renderer"] = self.renderer
        return await handler(event, data)


class AdminContextMiddleware(BaseMiddleware):
    def __init__(self, app: AppContext) -> None:
        self.app = app

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = _extract_user(event)
        if user is not None:
            data["staff_user"] = await self.app.staff.ensure_staff(user)
        return await handler(event, data)


class ClientContextMiddleware(BaseMiddleware):
    def __init__(self, app: AppContext) -> None:
        self.app = app

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        bot = data.get("bot")
        user = _extract_user(event)
        if bot is not None:
            bot_instance = await self.app.bots.get_by_bot_id(bot.id)
            data["bot_instance"] = bot_instance
            if bot_instance is not None and user is not None:
                profile = await self.app.users.get_profile(bot_instance.id, user.id)
                data["profile"] = profile
        return await handler(event, data)


def _extract_user(event: TelegramObject) -> User | None:
    if isinstance(event, Message):
        return event.from_user
    if isinstance(event, CallbackQuery):
        return event.from_user
    return None

