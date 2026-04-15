from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from razdevator.bot.setup import create_admin_dispatcher, create_client_dispatcher
from razdevator.core.context import AppContext
from razdevator.core.models import BotInstance
from razdevator.services.webhook_server import WebhookServer


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ClientRuntime:
    instance: BotInstance
    bot: Bot
    dispatcher_task: asyncio.Task[None]


class MultiBotRunner:
    def __init__(self, app: AppContext) -> None:
        self.app = app
        self.admin_bot: Bot | None = None
        self.admin_task: asyncio.Task[None] | None = None
        self.client_runtimes: dict[int, ClientRuntime] = {}
        self.webhook_server = WebhookServer(app)

    async def serve_forever(self) -> None:
        await self.webhook_server.start()
        if self.app.settings.admin_bot_token.strip():
            self.admin_bot = self._make_bot(self.app.settings.admin_bot_token)
            admin_dp = create_admin_dispatcher(self.app)
            self.admin_task = asyncio.create_task(
                admin_dp.start_polling(
                    self.admin_bot,
                    allowed_updates=admin_dp.resolve_used_update_types(),
                )
            )
            logger.info("Admin bot launched.")
        else:
            logger.info("Admin bot token is empty, admin polling is skipped.")

        for instance in await self.app.bots.list_active_client_bots():
            await self.launch_client_bot(instance)

        tasks = [
            runtime.dispatcher_task
            for runtime in self.client_runtimes.values()
        ]
        if self.admin_task is not None:
            tasks.append(self.admin_task)
        if not tasks:
            tasks.append(asyncio.create_task(asyncio.Event().wait()))
        try:
            await asyncio.gather(*tasks)
        finally:
            await self.shutdown()

    async def launch_client_bot(self, instance: BotInstance) -> None:
        if instance.id in self.client_runtimes or not instance.is_active or instance.is_archived:
            return

        bot = self._make_bot(instance.token)
        dispatcher = create_client_dispatcher(self.app)
        task = asyncio.create_task(
            dispatcher.start_polling(
                bot,
                allowed_updates=dispatcher.resolve_used_update_types(),
            )
        )
        runtime = ClientRuntime(instance=instance, bot=bot, dispatcher_task=task)
        self.client_runtimes[instance.id] = runtime
        task.add_done_callback(lambda _: self.client_runtimes.pop(instance.id, None))
        logger.info("Client bot launched: %s", instance.title)

    async def stop_client_bot(self, bot_instance_id: int) -> None:
        runtime = self.client_runtimes.pop(bot_instance_id, None)
        if runtime is None:
            return
        runtime.dispatcher_task.cancel()
        try:
            await runtime.dispatcher_task
        except asyncio.CancelledError:
            pass
        await runtime.bot.session.close()
        logger.info("Client bot stopped: %s", runtime.instance.title)

    def get_client_bot(self, bot_instance_id: int) -> Bot | None:
        runtime = self.client_runtimes.get(bot_instance_id)
        return runtime.bot if runtime else None

    async def shutdown(self) -> None:
        for bot_instance_id in list(self.client_runtimes):
            await self.stop_client_bot(bot_instance_id)
        if self.admin_bot is not None:
            await self.admin_bot.session.close()
        await self.webhook_server.stop()

    def _make_bot(self, token: str) -> Bot:
        return Bot(
            token=token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
