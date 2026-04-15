from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from razdevator.core.enums import Audience
from razdevator.core.models import TemplateItem
from razdevator.services.client_locales import button_label, language_options
from razdevator.services.payments import TopUpPackage


def home_keyboard(locale: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=button_label(locale, "profile"), callback_data="client:profile")
    builder.button(text=button_label(locale, "animate_photo"), callback_data="client:animate:0")
    builder.button(text=button_label(locale, "animate_photo_sound"), callback_data="client:animate_sound")
    builder.button(text=button_label(locale, "shop"), callback_data="client:shop")
    builder.adjust(1)
    return builder.as_markup()


def profile_keyboard(locale: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=button_label(locale, "topup"), callback_data="client:shop")
    builder.button(text=button_label(locale, "language"), callback_data="client:language")
    builder.button(text=button_label(locale, "back"), callback_data="client:home")
    builder.adjust(1)
    return builder.as_markup()


def templates_keyboard(
    items: list[TemplateItem],
    *,
    locale: str,
    page: int,
    pages: int,
    mode: str = "silent",
    video_length: str | None = None,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if mode == "sound" and video_length:
        template_prefix = f"client:template_sound:{video_length}"
        nav_prefix = f"client:animate_sound_page:{video_length}"
        back_callback = "client:animate_sound"
    else:
        template_prefix = "client:template"
        nav_prefix = "client:animate"
        back_callback = "client:home"

    for item in items:
        builder.button(
            text=f"{item.title(locale)} • {item.credits}💎",
            callback_data=f"{template_prefix}:{item.slug}:{page}",
        )

    if pages > 1:
        builder.button(text="‹", callback_data=f"{nav_prefix}:{max(page - 1, 0)}")
        builder.button(text=f"{page + 1}/{pages}", callback_data="client:no_op")
        builder.button(text="›", callback_data=f"{nav_prefix}:{min(page + 1, pages - 1)}")
        builder.button(text=button_label(locale, "back"), callback_data=back_callback)
        builder.adjust(2, 2, 2, 2, 3, 1)
    else:
        builder.button(text=button_label(locale, "back"), callback_data=back_callback)
        builder.adjust(2, 2, 2, 1)

    return builder.as_markup()


def sound_duration_keyboard(locale: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=button_label(locale, "sound_short"), callback_data="client:animate_sound_select:5s")
    builder.button(text=button_label(locale, "sound_long"), callback_data="client:animate_sound_select:10s")
    builder.button(text=button_label(locale, "back"), callback_data="client:home")
    builder.adjust(1)
    return builder.as_markup()


def upload_keyboard(locale: str, back_callback: str = "client:animate:0") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text=button_label(locale, "back"), callback_data=back_callback)
    return builder.as_markup()


def shop_keyboard(locale: str, packages: list[TopUpPackage]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for package in packages:
        builder.button(text=package.title(), callback_data=f"client:topup:{package.slug}")
    builder.button(text=button_label(locale, "back"), callback_data="client:home")
    builder.adjust(3, 1)
    return builder.as_markup()


def payment_methods_keyboard(locale: str, package_slug: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🇷🇺 QR / СБП", callback_data=f"client:paymethod:{package_slug}:qr")
    builder.button(text="₿ Crypto", callback_data=f"client:paymethod:{package_slug}:crypto")
    builder.button(text=button_label(locale, "back"), callback_data="client:shop")
    builder.adjust(1)
    return builder.as_markup()


def payment_checkout_keyboard(
    locale: str,
    transaction_id: str,
    pay_url: str | None,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if pay_url:
        builder.button(text=button_label(locale, "pay"), url=pay_url)
    builder.button(text=button_label(locale, "check_payment"), callback_data=f"client:paycheck:{transaction_id}")
    builder.button(text=button_label(locale, "close"), callback_data="client:shop")
    builder.adjust(1)
    return builder.as_markup()


def language_keyboard(locale: str, audience: Audience) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    options = language_options(audience)
    for code, title in options:
        builder.button(text=title, callback_data=f"client:lang:{code}")
    builder.button(text=button_label(locale, "back"), callback_data="client:profile")
    rows = [2] * ((len(options) + 1) // 2)
    rows.append(1)
    builder.adjust(*rows)
    return builder.as_markup()
