from __future__ import annotations

from html import escape
import json

from aiogram import F, Router
from aiogram.enums import ContentType
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, InputMediaPhoto, Message

from razdevator.bot.keyboards.client import (
    home_keyboard,
    language_keyboard,
    payment_checkout_keyboard,
    payment_methods_keyboard,
    profile_keyboard,
    shop_keyboard,
    sound_duration_keyboard,
    templates_keyboard,
    upload_keyboard,
)
from razdevator.bot.states.client import GenerationState
from razdevator.core.context import AppContext
from razdevator.core.enums import GenerationFeature, GenerationStatus, PaymentProvider, PaymentStatus, TransactionDirection
from razdevator.core.models import BotInstance, EndUserProfile
from razdevator.services.client_locales import language_name, normalize_locale, supported_locales
from razdevator.services.generation import GenerationError, ProgressMessageRef
from razdevator.services.payments import CheckoutSession, PaymentError, PaymentNotConfiguredError, TopUpPackage
from razdevator.services.screens import ScreenPayload, ScreenRenderer


router = Router(name="client-router")


@router.message(CommandStart())
async def start_client(
    message: Message,
    command: CommandObject | None,
    state: FSMContext,
    app: AppContext,
    bot_instance: BotInstance | None,
    screen_renderer: ScreenRenderer,
) -> None:
    if bot_instance is None or message.from_user is None:
        await message.answer("Bot is not configured in the database.")
        return

    await state.clear()
    referred_by = None
    if command and command.args:
        staff = await app.staff.get_by_referral_tag(command.args.strip())
        referred_by = staff.id if staff else None

    profile = await app.users.upsert_user(
        bot_instance_id=bot_instance.id,
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        language_code=detect_locale(bot_instance, message.from_user.language_code),
        referred_by_staff_id=referred_by,
    )
    await render_client_home(message, app, bot_instance, profile, screen_renderer)


@router.callback_query(F.data == "client:home")
async def cb_client_home(
    callback: CallbackQuery,
    app: AppContext,
    bot_instance: BotInstance | None,
    profile: EndUserProfile | None,
    screen_renderer: ScreenRenderer,
) -> None:
    if bot_instance is None or profile is None:
        await callback.answer("Profile not found.", show_alert=True)
        return
    await render_client_home(callback, app, bot_instance, profile, screen_renderer)


@router.callback_query(F.data == "client:profile")
async def cb_client_profile(
    callback: CallbackQuery,
    app: AppContext,
    bot_instance: BotInstance | None,
    profile: EndUserProfile | None,
    screen_renderer: ScreenRenderer,
) -> None:
    if bot_instance is None or profile is None:
        await callback.answer("Profile not found.", show_alert=True)
        return
    await render_profile(callback, app, bot_instance, profile, screen_renderer)


@router.callback_query(F.data.startswith("client:animate:"))
async def cb_client_animate(
    callback: CallbackQuery,
    app: AppContext,
    bot_instance: BotInstance | None,
    profile: EndUserProfile | None,
    screen_renderer: ScreenRenderer,
) -> None:
    if bot_instance is None or profile is None:
        await callback.answer("Profile not found.", show_alert=True)
        return
    page = int(callback.data.split(":")[-1])
    await render_templates(callback, app, bot_instance, profile, screen_renderer, page)


@router.callback_query(F.data == "client:animate_sound")
async def cb_client_animate_sound(
    callback: CallbackQuery,
    app: AppContext,
    bot_instance: BotInstance | None,
    profile: EndUserProfile | None,
    screen_renderer: ScreenRenderer,
) -> None:
    if bot_instance is None or profile is None:
        await callback.answer("Profile not found.", show_alert=True)
        return
    await render_sound_duration(callback, app, bot_instance, profile, screen_renderer)


@router.callback_query(F.data.startswith("client:animate_sound_select:"))
async def cb_client_animate_sound_select(
    callback: CallbackQuery,
    app: AppContext,
    bot_instance: BotInstance | None,
    profile: EndUserProfile | None,
    screen_renderer: ScreenRenderer,
) -> None:
    if bot_instance is None or profile is None:
        await callback.answer("Profile not found.", show_alert=True)
        return
    video_length = callback.data.split(":")[-1]
    await render_sound_templates(callback, app, bot_instance, profile, screen_renderer, video_length, 0)


@router.callback_query(F.data.startswith("client:animate_sound_page:"))
async def cb_client_animate_sound_page(
    callback: CallbackQuery,
    app: AppContext,
    bot_instance: BotInstance | None,
    profile: EndUserProfile | None,
    screen_renderer: ScreenRenderer,
) -> None:
    if bot_instance is None or profile is None:
        await callback.answer("Profile not found.", show_alert=True)
        return
    _, _, video_length, page_text = callback.data.split(":")
    await render_sound_templates(
        callback,
        app,
        bot_instance,
        profile,
        screen_renderer,
        video_length,
        int(page_text),
    )


@router.callback_query(F.data.startswith("client:template:"))
async def cb_client_template(
    callback: CallbackQuery,
    state: FSMContext,
    app: AppContext,
    bot_instance: BotInstance | None,
    profile: EndUserProfile | None,
    screen_renderer: ScreenRenderer,
) -> None:
    if bot_instance is None or profile is None:
        await callback.answer("Profile not found.", show_alert=True)
        return
    _, _, slug, page_text = callback.data.split(":")
    template = app.templates.get(slug)
    if template is None:
        await callback.answer("Template not found.", show_alert=True)
        return
    await state.set_state(GenerationState.waiting_photo)
    await state.update_data(
        template_slug=slug,
        page=int(page_text),
        generation_feature=GenerationFeature.IMAGE_TO_VIDEO.value,
        video_length="5s",
        template_mode="silent",
    )
    locale = profile.language_code
    text = app.i18n.t(
        locale,
        "send_photo_for_template",
        template=template.title(locale),
    )
    await screen_renderer.show(
        callback,
        ScreenPayload(
            text=text,
            keyboard=upload_keyboard(locale),
            media_path=app.media.screen("client_upload"),
        ),
    )


@router.callback_query(F.data.startswith("client:template_sound:"))
async def cb_client_template_sound(
    callback: CallbackQuery,
    state: FSMContext,
    app: AppContext,
    bot_instance: BotInstance | None,
    profile: EndUserProfile | None,
    screen_renderer: ScreenRenderer,
) -> None:
    if bot_instance is None or profile is None:
        await callback.answer("Profile not found.", show_alert=True)
        return
    _, _, video_length, slug, page_text = callback.data.split(":")
    template = app.templates.get_audio(slug, video_length)
    if template is None:
        await callback.answer("Template not found.", show_alert=True)
        return
    await state.set_state(GenerationState.waiting_photo)
    await state.update_data(
        template_slug=slug,
        page=int(page_text),
        generation_feature=GenerationFeature.AUDIO_IMAGE_TO_VIDEO.value,
        video_length=video_length,
        template_mode="sound",
    )
    locale = profile.language_code
    text = app.i18n.t(
        locale,
        "send_photo_for_audio_template",
        template=template.title(locale),
        video_length=video_length,
    )
    await screen_renderer.show(
        callback,
        ScreenPayload(
            text=text,
            keyboard=upload_keyboard(locale, f"client:animate_sound_page:{video_length}:{page_text}"),
            media_path=app.media.screen("client_upload"),
        ),
    )


@router.message(GenerationState.waiting_photo, F.photo)
async def msg_client_photo(
    message: Message,
    state: FSMContext,
    app: AppContext,
    bot_instance: BotInstance | None,
    profile: EndUserProfile | None,
    screen_renderer: ScreenRenderer,
) -> None:
    if bot_instance is None or profile is None:
        await state.clear()
        return
    data = await state.get_data()
    feature = GenerationFeature(data.get("generation_feature", GenerationFeature.IMAGE_TO_VIDEO.value))
    video_length = data.get("video_length") or "5s"
    if feature is GenerationFeature.AUDIO_IMAGE_TO_VIDEO:
        template = app.templates.get_audio(data["template_slug"], video_length)
    else:
        template = app.templates.get(data["template_slug"])
    if template is None:
        await state.clear()
        return
    locale = profile.language_code
    if profile.balance < template.credits:
        await message.answer(app.i18n.t(profile.language_code, "not_enough_balance"))
        return
    photo = message.photo[-1]
    job = await app.generations.create_job(
        bot_instance_id=bot_instance.id,
        end_user_id=profile.id,
        feature=feature,
        template_slug=template.slug,
        cost_credits=template.credits,
        source_file_id=photo.file_id,
    )
    try:
        submitted = await app.generation_service.submit(
            bot_instance=bot_instance,
            profile=profile,
            template=template,
            job=job,
            video_length=video_length,
        )
    except GenerationError as exc:
        await app.generations.update_status(job.id, GenerationStatus.FAILED, error_text=str(exc))
        await state.clear()
        error_key = (
            "audio_generation_unavailable"
            if feature is GenerationFeature.AUDIO_IMAGE_TO_VIDEO and "Internal error" in str(exc)
            else "generation_submit_error"
        )
        await screen_renderer.show(
            message,
            ScreenPayload(
                text=app.i18n.t(locale, error_key),
                keyboard=home_keyboard(locale),
                media_path=app.media.screen("client_done"),
            ),
        )
        return
    await app.users.consume_balance(profile.id, template.credits)
    await state.clear()
    refreshed = await app.users.get_profile(bot_instance.id, profile.telegram_id)
    locale = refreshed.language_code if refreshed else locale
    if submitted.get("provider") != "crebots" or not submitted.get("task_id"):
        await screen_renderer.show(
            message,
            ScreenPayload(
                text=app.i18n.t(
                    locale,
                    "generation_queued",
                    template=template.title(locale),
                    credits=template.credits,
                ),
                keyboard=home_keyboard(locale),
                media_path=app.media.screen("client_done"),
            ),
        )
        return

    loader_message = await screen_renderer.show(
        message,
        ScreenPayload(
            text=app.i18n.t(
                locale,
                "generation_loader_active",
                template=template.title(locale),
                task_id=submitted["task_id"],
                progress=0,
                bar="[░░░░░░░░░░░░]",
            ),
            media_path=app.media.screen("client_done"),
        ),
    )
    app.generation_service.track(
        bot_instance=bot_instance,
        profile=profile,
        template=template,
        job=job,
        task_id=submitted["task_id"],
        initial_status=submitted.get("status", "NEW"),
        progress_message=ProgressMessageRef.from_message(loader_message),
    )


@router.message(GenerationState.waiting_photo)
async def msg_client_photo_invalid(
    message: Message,
    app: AppContext,
    profile: EndUserProfile | None,
) -> None:
    locale = profile.language_code if profile else "ru"
    await message.answer(app.i18n.t(locale, "send_photo_for_template", template="..."))


@router.callback_query(F.data == "client:shop")
async def cb_client_shop(
    callback: CallbackQuery,
    app: AppContext,
    bot_instance: BotInstance | None,
    profile: EndUserProfile | None,
    screen_renderer: ScreenRenderer,
) -> None:
    if bot_instance is None or profile is None:
        await callback.answer("Profile not found.", show_alert=True)
        return
    await render_shop(callback, app, bot_instance, profile, screen_renderer)


@router.callback_query(F.data.startswith("client:topup:"))
async def cb_client_topup(
    callback: CallbackQuery,
    app: AppContext,
    bot_instance: BotInstance | None,
    profile: EndUserProfile | None,
    screen_renderer: ScreenRenderer,
) -> None:
    if bot_instance is None or profile is None:
        await callback.answer("Profile not found.", show_alert=True)
        return
    slug = callback.data.split(":")[-1]
    package = app.payment_registry.get_package(slug)
    if package is None:
        await callback.answer("Package not found.", show_alert=True)
        return

    if bot_instance.audience.value == "ru" and bot_instance.payment_provider is PaymentProvider.PLATEGA:
        await screen_renderer.show(
            callback,
            ScreenPayload(
                text=app.i18n.t(
                    profile.language_code,
                    "client_payment_methods",
                    credits=package.credits,
                ),
                keyboard=payment_methods_keyboard(profile.language_code, package.slug),
                media_path=app.media.screen("client_shop"),
            ),
        )
        return

    quote = app.payment_registry.quote(
        bot_instance.audience,
        amount_cents=package.amount_cents,
        locale=profile.language_code,
    )
    await app.payments.create_payment(
        bot_instance_id=bot_instance.id,
        end_user_id=profile.id,
        amount_cents=package.amount_cents,
        currency=quote.currency,
        provider=quote.provider,
        direction=TransactionDirection.DEPOSIT,
        status=PaymentStatus.PENDING,
    )
    await screen_renderer.show(
        callback,
        ScreenPayload(
            text=app.i18n.t(
                profile.language_code,
                "payment_placeholder",
                provider=quote.provider.value,
                amount=quote.text,
            ),
            keyboard=shop_keyboard(
                profile.language_code,
                app.payment_registry.packages_for(bot_instance.audience),
            ),
            media_path=app.media.screen("client_shop"),
        ),
    )


@router.callback_query(F.data.startswith("client:paymethod:"))
async def cb_client_payment_method(
    callback: CallbackQuery,
    app: AppContext,
    bot_instance: BotInstance | None,
    profile: EndUserProfile | None,
    screen_renderer: ScreenRenderer,
) -> None:
    if bot_instance is None or profile is None:
        await callback.answer("Profile not found.", show_alert=True)
        return

    _, _, package_slug, channel = callback.data.split(":")
    package = app.payment_registry.get_package(package_slug)
    if package is None:
        await callback.answer("Package not found.", show_alert=True)
        return

    try:
        session = await app.payment_registry.create_ru_checkout(
            bot_instance=bot_instance,
            profile=profile,
            package=package,
            channel=channel,
        )
    except PaymentNotConfiguredError:
        await callback.answer(app.i18n.t(profile.language_code, "platega_not_configured"), show_alert=True)
        return
    except PaymentError:
        await callback.answer(app.i18n.t(profile.language_code, "payment_create_error"), show_alert=True)
        return

    await render_checkout(
        callback,
        app,
        profile,
        screen_renderer,
        session,
        package,
    )


@router.callback_query(F.data.startswith("client:paycheck:"))
async def cb_client_payment_check(
    callback: CallbackQuery,
    app: AppContext,
    bot_instance: BotInstance | None,
    profile: EndUserProfile | None,
    screen_renderer: ScreenRenderer,
) -> None:
    if bot_instance is None or profile is None:
        await callback.answer("Profile not found.", show_alert=True)
        return

    transaction_id = callback.data.split(":", 2)[-1]
    try:
        session, payment = await app.payment_registry.refresh_ru_checkout(transaction_id)
    except PaymentNotConfiguredError:
        await callback.answer(app.i18n.t(profile.language_code, "platega_not_configured"), show_alert=True)
        return
    except PaymentError:
        await callback.answer(app.i18n.t(profile.language_code, "payment_create_error"), show_alert=True)
        return

    package = package_from_payment(app, payment)
    if payment and payment.status is PaymentStatus.PAID:
        credits = package.credits if package else 0
        await screen_renderer.show(
            callback,
            ScreenPayload(
                text=app.i18n.t(
                    profile.language_code,
                    "client_payment_success",
                    credits=credits,
                ),
                keyboard=profile_keyboard(profile.language_code),
                media_path=app.media.screen("client_done"),
            ),
        )
        return

    if payment and payment.status is PaymentStatus.CANCELED:
        await callback.answer(app.i18n.t(profile.language_code, "client_payment_canceled"), show_alert=True)
    else:
        await callback.answer(app.i18n.t(profile.language_code, "client_payment_pending"))

    await render_checkout(
        callback,
        app,
        profile,
        screen_renderer,
        session,
        package,
    )


@router.callback_query(F.data == "client:language")
async def cb_client_language(
    callback: CallbackQuery,
    app: AppContext,
    bot_instance: BotInstance | None,
    profile: EndUserProfile | None,
    screen_renderer: ScreenRenderer,
) -> None:
    if bot_instance is None or profile is None:
        await callback.answer("Profile not found.", show_alert=True)
        return
    locale = profile.language_code
    await screen_renderer.show(
        callback,
        ScreenPayload(
            text=app.i18n.t(
                locale,
                "client_language",
                language=language_name(locale),
            ),
            keyboard=language_keyboard(locale, bot_instance.audience),
            media_path=app.media.screen("client_language"),
        ),
    )


@router.callback_query(F.data.startswith("client:lang:"))
async def cb_client_set_language(
    callback: CallbackQuery,
    app: AppContext,
    bot_instance: BotInstance | None,
    profile: EndUserProfile | None,
    screen_renderer: ScreenRenderer,
) -> None:
    if bot_instance is None or profile is None:
        await callback.answer("Profile not found.", show_alert=True)
        return
    locale = callback.data.split(":")[-1]
    if locale not in supported_locales(bot_instance.audience):
        await callback.answer("Language is not available for this bot.", show_alert=True)
        return
    await app.users.set_language(bot_instance.id, profile.telegram_id, locale)
    refreshed = await app.users.get_profile(bot_instance.id, profile.telegram_id)
    await callback.answer(app.i18n.t(locale, "language_updated"))
    if refreshed is not None:
        await render_profile(callback, app, bot_instance, refreshed, screen_renderer)


@router.callback_query(F.data == "client:no_op")
async def cb_client_noop(callback: CallbackQuery) -> None:
    await callback.answer()


async def render_client_home(
    target: Message | CallbackQuery,
    app: AppContext,
    bot_instance: BotInstance,
    profile: EndUserProfile,
    screen_renderer: ScreenRenderer,
) -> None:
    locale = profile.language_code
    text = bot_instance.welcome_text or app.i18n.t(
        locale,
        "client_home",
        name=escape(profile.full_name),
        title=escape(bot_instance.title),
    )
    await screen_renderer.show(
        target,
        ScreenPayload(
            text=text,
            keyboard=home_keyboard(locale),
            media_path=app.media.screen("client_home", bot_instance.hero_media),
        ),
    )


async def render_profile(
    target: Message | CallbackQuery,
    app: AppContext,
    bot_instance: BotInstance,
    profile: EndUserProfile,
    screen_renderer: ScreenRenderer,
) -> None:
    locale = profile.language_code
    text = app.i18n.t(
        locale,
        "client_profile",
        balance=f"{profile.balance} 💎",
        success=profile.successful_generations,
        failed=profile.failed_generations,
    )
    await screen_renderer.show(
        target,
        ScreenPayload(
            text=text,
            keyboard=profile_keyboard(locale),
            media_path=app.media.screen("client_profile"),
        ),
    )


async def render_templates(
    target: Message | CallbackQuery,
    app: AppContext,
    bot_instance: BotInstance,
    profile: EndUserProfile,
    screen_renderer: ScreenRenderer,
    page: int = 0,
) -> None:
    locale = profile.language_code
    items, pages = app.templates.page(page)
    text = app.i18n.t(
        locale,
        "client_templates",
        balance=f"{profile.balance} 💎",
    )
    await screen_renderer.show(
        target,
        ScreenPayload(
            text=text,
            keyboard=templates_keyboard(items, locale=locale, page=max(page, 0), pages=pages),
            media_path=app.media.screen("client_templates"),
        ),
    )


async def render_sound_duration(
    target: Message | CallbackQuery,
    app: AppContext,
    bot_instance: BotInstance,
    profile: EndUserProfile,
    screen_renderer: ScreenRenderer,
) -> None:
    locale = profile.language_code
    text = app.i18n.t(
        locale,
        "client_sound_duration",
        balance=f"{profile.balance} 💎",
    )
    await screen_renderer.show(
        target,
        ScreenPayload(
            text=text,
            keyboard=sound_duration_keyboard(locale),
            media_path=app.media.screen("client_sound"),
        ),
    )


async def render_sound_templates(
    target: Message | CallbackQuery,
    app: AppContext,
    bot_instance: BotInstance,
    profile: EndUserProfile,
    screen_renderer: ScreenRenderer,
    video_length: str,
    page: int = 0,
) -> None:
    locale = profile.language_code
    items, pages = app.templates.audio_page(video_length, page)
    text = app.i18n.t(
        locale,
        "client_sound_templates",
        video_length=video_length,
        balance=f"{profile.balance} 💎",
    )
    await screen_renderer.show(
        target,
        ScreenPayload(
            text=text,
            keyboard=templates_keyboard(
                items,
                locale=locale,
                page=max(page, 0),
                pages=pages,
                mode="sound",
                video_length=video_length,
            ),
            media_path=app.media.screen("client_sound"),
        ),
    )


async def render_shop(
    target: Message | CallbackQuery,
    app: AppContext,
    bot_instance: BotInstance,
    profile: EndUserProfile,
    screen_renderer: ScreenRenderer,
) -> None:
    locale = profile.language_code
    text = app.i18n.t(
        locale,
        "client_shop",
        provider=bot_instance.payment_provider.value,
    )
    await screen_renderer.show(
        target,
        ScreenPayload(
            text=text,
            keyboard=shop_keyboard(locale, app.payment_registry.packages_for(bot_instance.audience)),
            media_path=app.media.screen("client_shop"),
        ),
    )


def detect_locale(bot_instance: BotInstance, user_lang: str | None) -> str:
    return normalize_locale(bot_instance.audience, user_lang)


async def render_checkout(
    target: Message | CallbackQuery,
    app: AppContext,
    profile: EndUserProfile,
    screen_renderer: ScreenRenderer,
    session: CheckoutSession,
    package: TopUpPackage | None,
) -> None:
    locale = profile.language_code
    text = build_checkout_text(app, locale, session)
    keyboard = payment_checkout_keyboard(locale, session.transaction_id, session.redirect_url)

    if session.channel == "qr" and (session.qr_bytes or session.qr_url):
        await show_checkout_qr(target, text, keyboard, session)
        return

    await screen_renderer.show(
        target,
        ScreenPayload(
            text=text,
            keyboard=keyboard,
            media_path=app.media.screen("client_shop"),
        ),
    )


def build_checkout_text(app: AppContext, locale: str, session: CheckoutSession) -> str:
    amount = f"{session.amount_cents / 100:.2f} ₽" if locale == "ru" else f"{session.amount_cents / 100:.2f} RUB"
    link_line = (
        f"Ссылка: <a href=\"{escape(session.redirect_url)}\">Оплатить</a>\n"
        if locale == "ru" and session.redirect_url
        else f"Link: <a href=\"{escape(session.redirect_url)}\">Pay</a>\n"
        if session.redirect_url
        else ""
    )
    method_label = session.payment_method or "Platega"
    method_line = (
        f"Метод: <b>{escape(method_label)}</b>\n"
        if locale == "ru"
        else f"Method: <b>{escape(method_label)}</b>\n"
    )
    expires_line = (
        f"Действует: <b>{escape(session.expires_in)}</b>\n"
        if locale == "ru" and session.expires_in
        else f"Expires in: <b>{escape(session.expires_in)}</b>\n"
        if session.expires_in
        else ""
    )
    usdt_line = ""
    if session.amount_usdt is not None:
        if locale == "ru":
            usdt_line = f"Крипто: <b>{session.amount_usdt:.4f} USDT</b>\n"
        else:
            usdt_line = f"Crypto: <b>{session.amount_usdt:.4f} USDT</b>\n"
    status_line = (
        f"Статус: <b>{escape(session.status)}</b>\n"
        if locale == "ru"
        else f"Status: <b>{escape(session.status)}</b>\n"
    )
    return app.i18n.t(
        locale,
        "client_payment_invoice",
        transaction_id=session.transaction_id,
        amount=amount,
        link_line=link_line,
        method_line=method_line,
        expires_line=expires_line,
        usdt_line=usdt_line,
        status_line=status_line,
    )


async def show_checkout_qr(
    target: Message | CallbackQuery,
    text: str,
    keyboard,
    session: CheckoutSession,
) -> None:
    media = None
    if session.qr_bytes:
        media = BufferedInputFile(session.qr_bytes, filename=f"{session.transaction_id}.png")
    elif session.qr_url:
        media = session.qr_url

    if media is None:
        return

    if isinstance(target, CallbackQuery):
        await target.answer()
        if target.message is None:
            return
        try:
            if target.message.content_type == ContentType.PHOTO:
                await target.message.edit_media(
                    media=InputMediaPhoto(media=media, caption=text),
                    reply_markup=keyboard,
                )
            else:
                await target.message.answer_photo(media, caption=text, reply_markup=keyboard)
        except TelegramBadRequest as exc:
            if "message is not modified" not in str(exc).lower():
                raise
        return

    await target.answer_photo(media, caption=text, reply_markup=keyboard)


def package_from_payment(app: AppContext, payment) -> TopUpPackage | None:
    if payment is None or not payment.meta_json:
        return None
    try:
        data = json.loads(payment.meta_json)
    except json.JSONDecodeError:
        return None
    slug = data.get("package_slug")
    if not isinstance(slug, str):
        return None
    return app.payment_registry.get_package(slug)
