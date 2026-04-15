from __future__ import annotations

import asyncio
import logging

from razdevator.core.config import Settings
from razdevator.core.context import AppContext, build_context
from razdevator.db.schema import init_schema
from razdevator.services.runtime import MultiBotRunner


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


async def _main() -> None:
    configure_logging()

    settings = Settings()
    app = await build_context(settings)
    await app.db.connect()
    await init_schema(app.db)
    await app.bootstrap()

    runner = MultiBotRunner(app)
    app.runner = runner

    try:
        await runner.serve_forever()
    finally:
        await app.close()


def run() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    run()
