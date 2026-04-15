from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from razdevator.core.models import BotInstance


def home_keyboard(*, is_owner: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔗 Общий бот и трафик", callback_data="admin:general")
    builder.button(text="🤖 Мои боты", callback_data="admin:bots")
    builder.button(text="👤 Профиль", callback_data="admin:profile")
    if is_owner:
        builder.button(text="🛡 Панель владельца", callback_data="admin:owner")
    builder.adjust(1)
    return builder.as_markup()


def back_home_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="← Назад", callback_data="admin:home")
    return builder.as_markup()


def personal_bots_keyboard(bots: list[BotInstance]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for bot in bots:
        prefix = "🟢" if bot.is_active else "⛔"
        builder.button(
            text=f"{prefix} {bot.title}",
            callback_data=f"admin:bot:{bot.id}",
        )
    builder.button(text="＋ Создать бота", callback_data="admin:create")
    builder.button(text="← Назад", callback_data="admin:home")
    builder.adjust(1)
    return builder.as_markup()


def create_bot_locale_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🇷🇺 Русский", callback_data="admin:create:ru")
    builder.button(text="🌍 International", callback_data="admin:create:en")
    builder.button(text="← Назад", callback_data="admin:bots")
    builder.adjust(1)
    return builder.as_markup()


def bot_detail_keyboard(bot: BotInstance) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="⏻ Выключить бота" if bot.is_active else "⏻ Включить бота",
        callback_data=f"admin:bot_toggle:{bot.id}",
    )
    builder.button(text="🔗 Ссылка", callback_data=f"admin:bot_links:{bot.id}")
    builder.button(text="👋 Welcome-текст", callback_data=f"admin:bot_welcome:{bot.id}")
    builder.button(text="🖤 Farewell-текст", callback_data=f"admin:bot_farewell:{bot.id}")
    builder.button(text="📣 Рассылка", callback_data=f"admin:bot_broadcast:{bot.id}")
    builder.button(text="🗑 Архивировать", callback_data=f"admin:bot_delete:{bot.id}")
    builder.button(text="✖ Закрыть", callback_data="admin:bots")
    builder.adjust(1, 1, 2, 1, 1, 1)
    return builder.as_markup()


def owner_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💸 Изменить ставку", callback_data="admin:owner:rate")
    builder.button(text="📈 Статистика реферала", callback_data="admin:owner:referral_stats")
    builder.button(text="📣 Глобальная рассылка", callback_data="admin:owner:broadcast")
    builder.button(text="🔗 Главный бот", callback_data="admin:owner:main_link")
    builder.button(text="← Назад", callback_data="admin:home")
    builder.adjust(1)
    return builder.as_markup()
