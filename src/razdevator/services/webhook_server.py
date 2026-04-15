from __future__ import annotations

import logging

from aiohttp import web

from razdevator.core.context import AppContext


logger = logging.getLogger(__name__)


class WebhookServer:
    def __init__(self, app: AppContext) -> None:
        self.app = app
        self._runner: web.AppRunner | None = None
        self._site: web.TCPSite | None = None

    async def start(self) -> None:
        web_app = web.Application()
        web_app.router.add_post(
            self.app.settings.platega_webhook_path,
            self.handle_platega_callback,
        )
        self._runner = web.AppRunner(web_app)
        await self._runner.setup()
        self._site = web.TCPSite(
            self._runner,
            host=self.app.settings.webhook_host,
            port=self.app.settings.webhook_port,
        )
        await self._site.start()
        logger.info(
            "Webhook server listening on http://%s:%s%s",
            self.app.settings.webhook_host,
            self.app.settings.webhook_port,
            self.app.settings.platega_webhook_path,
        )

    async def stop(self) -> None:
        if self._runner is not None:
            await self._runner.cleanup()
            self._runner = None
            self._site = None

    async def handle_platega_callback(self, request: web.Request) -> web.Response:
        expected_merchant = self.app.settings.platega_merchant_id
        expected_secret = self.app.settings.platega_secret
        if expected_merchant and request.headers.get("X-MerchantId") != expected_merchant:
            return web.Response(status=403)
        if expected_secret and request.headers.get("X-Secret") != expected_secret:
            return web.Response(status=403)

        try:
            payload = await request.json()
        except Exception:
            return web.Response(status=400)

        record = await self.app.payment_registry.process_platega_callback(payload)
        logger.info("Processed Platega callback for transaction %s", payload.get("id"))
        return web.Response(status=200 if record or payload.get("id") else 202)
