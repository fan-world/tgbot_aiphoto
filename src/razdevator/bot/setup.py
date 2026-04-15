from __future__ import annotations

import importlib

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from razdevator.bot.handlers.admin.router import router as admin_router
from razdevator.bot.handlers.client import router as client_router_module
from razdevator.bot.middlewares.context import (
    AdminContextMiddleware,
    AppContextMiddleware,
    ClientContextMiddleware,
)
from razdevator.core.context import AppContext


def create_admin_dispatcher(app: AppContext) -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    app_middleware = AppContextMiddleware(app)
    admin_middleware = AdminContextMiddleware(app)
    dp.message.middleware(app_middleware)
    dp.callback_query.middleware(app_middleware)
    dp.message.middleware(admin_middleware)
    dp.callback_query.middleware(admin_middleware)
    dp.include_router(admin_router)
    return dp


def create_client_dispatcher(app: AppContext) -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    app_middleware = AppContextMiddleware(app)
    client_middleware = ClientContextMiddleware(app)
    dp.message.middleware(app_middleware)
    dp.callback_query.middleware(app_middleware)
    dp.message.middleware(client_middleware)
    dp.callback_query.middleware(client_middleware)
    fresh_client_router = importlib.reload(client_router_module).router
    dp.include_router(fresh_client_router)
    return dp
