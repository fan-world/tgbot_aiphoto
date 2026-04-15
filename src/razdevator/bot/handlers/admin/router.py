from __future__ import annotations

from html import escape
from urllib.parse import quote

from aiogram import Bot, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from razdevator.bot.keyboards.admin import (
    back_home_keyboard,
    bot_detail_keyboard,
    create_bot_locale_keyboard,
    home_keyboard,
    owner_keyboard,
    personal_bots_keyboard,
)
from razdevator.bot.states.admin import (
    BotBroadcastState,
    CreateBotState,
    EditBotTextState,
    OwnerBroadcastState,
    OwnerMainLinkState,
    OwnerReferralStatsState,
    OwnerRateState,
)
from razdevator.core.context import AppContext
from razdevator.core.enums import Audience, BotKind
from razdevator.core.models import BotInstance, StaffUser
from razdevator.services.screens import ScreenPayload, ScreenRenderer
from razdevator.utils.formatting import format_money


router = Router(name="admin-router")


@router.message(CommandStart())
async def start_admin(
    message: Message,
    state: FSMContext,
    app: AppContext,
    staff_user: StaffUser,
    screen_renderer: ScreenRenderer,
) -> None:
    await state.clear()
    await render_admin_home(message, app, staff_user, screen_renderer)


@router.callback_query(F.data == "admin:home")
async def cb_admin_home(
    callback: CallbackQuery,
    app: AppContext,
    staff_user: StaffUser,
    screen_renderer: ScreenRenderer,
) -> None:
    await render_admin_home(callback, app, staff_user, screen_renderer)


@router.callback_query(F.data == "admin:general")
async def cb_admin_general(
    callback: CallbackQuery,
    app: AppContext,
    staff_user: StaffUser,
    screen_renderer: ScreenRenderer,
) -> None:
    overview = await app.stats.get_staff_overview(staff_user.id)
    raw_link = await app.app_settings.get("main_bot_link", app.settings.main_bot_link)
    start_link, permanent_link = build_referral_links(raw_link, staff_user.referral_tag)
    text = app.i18n.t(
        "ru",
        "admin_general_text",
        hint=app.i18n.t("ru", "admin_general_hint"),
        raw_link=start_link or "не задано",
        permanent_link=permanent_link or "не задано",
        users_total=overview.total_users,
        users_month=overview.month_users,
        users_week=overview.week_users,
        users_today=overview.today_users,
        paid_total=overview.paid_payments,
        payment_total=overview.total_payments,
        paid_month=overview.month_paid_payments,
        payment_month=overview.month_total_payments,
        paid_week=overview.week_paid_payments,
        payment_week=overview.week_total_payments,
        paid_today=overview.today_paid_payments,
        payment_today=overview.today_total_payments,
        earned=format_money(overview.earned_cents),
    )
    await screen_renderer.show(
        callback,
        ScreenPayload(
            text=text,
            keyboard=back_home_keyboard(),
            media_path=app.media.screen("admin_general"),
        ),
    )


@router.callback_query(F.data == "admin:bots")
async def cb_admin_bots(
    callback: CallbackQuery,
    app: AppContext,
    staff_user: StaffUser,
    screen_renderer: ScreenRenderer,
) -> None:
    await render_personal_bots(callback, app, staff_user, screen_renderer)


@router.callback_query(F.data == "admin:profile")
async def cb_admin_profile(
    callback: CallbackQuery,
    app: AppContext,
    staff_user: StaffUser,
    screen_renderer: ScreenRenderer,
) -> None:
    personal_bots = await app.bots.list_personal_bots(staff_user.id)
    overview = await app.stats.get_staff_overview(staff_user.id)
    text = app.i18n.t(
        "ru",
        "admin_profile_text",
        tag=staff_user.referral_tag,
        rate=staff_user.commission_rate,
        bots=len(personal_bots),
        earned=format_money(overview.earned_cents),
    )
    await screen_renderer.show(
        callback,
        ScreenPayload(
            text=text,
            keyboard=back_home_keyboard(),
            media_path=app.media.screen("admin_profile"),
        ),
    )


@router.callback_query(F.data == "admin:owner")
async def cb_admin_owner(
    callback: CallbackQuery,
    app: AppContext,
    staff_user: StaffUser,
    screen_renderer: ScreenRenderer,
) -> None:
    if not staff_user.is_owner:
        await callback.answer(app.i18n.t("ru", "owner_only"), show_alert=True)
        return
    await render_owner_panel(callback, app, screen_renderer)


@router.callback_query(F.data == "admin:create")
async def cb_admin_create(
    callback: CallbackQuery,
    app: AppContext,
    screen_renderer: ScreenRenderer,
) -> None:
    await screen_renderer.show(
        callback,
        ScreenPayload(
            text=app.i18n.t("ru", "choose_bot_locale"),
            keyboard=create_bot_locale_keyboard(),
            media_path=app.media.screen("admin_bots"),
        ),
    )


@router.callback_query(F.data.in_({"admin:create:ru", "admin:create:en"}))
async def cb_admin_create_locale(
    callback: CallbackQuery,
    state: FSMContext,
    app: AppContext,
    screen_renderer: ScreenRenderer,
) -> None:
    audience = callback.data.rsplit(":", 1)[-1]
    await state.set_state(CreateBotState.waiting_token)
    await state.update_data(audience=audience)
    await screen_renderer.show(
        callback,
        ScreenPayload(
            text=app.i18n.t("ru", "send_bot_token"),
            keyboard=back_home_keyboard(),
            media_path=app.media.screen("admin_bots"),
        ),
    )


@router.message(CreateBotState.waiting_token)
async def admin_create_waiting_token(
    message: Message,
    state: FSMContext,
    app: AppContext,
    staff_user: StaffUser,
    screen_renderer: ScreenRenderer,
) -> None:
    if not message.text:
        await message.answer(app.i18n.t("ru", "unsupported_message"))
        return

    token = message.text.strip()
    await delete_message_safe(message)
    test_bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    try:
        me = await test_bot.get_me()
    except Exception:
        await message.answer(app.i18n.t("ru", "invalid_token"))
        return
    finally:
        await test_bot.session.close()

    data = await state.get_data()
    audience = Audience(data["audience"])
    title = me.full_name or me.first_name or me.username or f"Bot {me.id}"
    existing = await app.bots.get_by_bot_id(int(me.id))
    if existing is not None:
        await message.answer("Этот бот уже добавлен в систему.")
        await state.clear()
        return
    instance = await app.bots.create_bot_instance(
        token=token,
        bot_id=me.id,
        username=me.username,
        title=title,
        kind=BotKind.PERSONAL,
        audience=audience,
        owner_staff_id=staff_user.id,
        hero_media=str(app.media.assets_dir / "client_home.png"),
    )
    runner = app.runner
    if runner and hasattr(runner, "launch_client_bot"):
        await runner.launch_client_bot(instance)
    await state.clear()
    await message.answer(app.i18n.t("ru", "bot_created", title=title))
    await render_bot_detail(message, app, staff_user, screen_renderer, instance)


@router.callback_query(F.data.startswith("admin:bot:"))
async def cb_admin_bot_detail(
    callback: CallbackQuery,
    app: AppContext,
    staff_user: StaffUser,
    screen_renderer: ScreenRenderer,
) -> None:
    bot_id = int(callback.data.split(":")[-1])
    bot_instance = await get_allowed_bot(app, staff_user, bot_id)
    if bot_instance is None:
        await callback.answer(app.i18n.t("ru", "unknown_bot"), show_alert=True)
        return
    await render_bot_detail(callback, app, staff_user, screen_renderer, bot_instance)


@router.callback_query(F.data.startswith("admin:bot_links:"))
async def cb_admin_bot_links(
    callback: CallbackQuery,
    app: AppContext,
    staff_user: StaffUser,
) -> None:
    bot_id = int(callback.data.split(":")[-1])
    bot_instance = await get_allowed_bot(app, staff_user, bot_id)
    if bot_instance is None:
        await callback.answer(app.i18n.t("ru", "unknown_bot"), show_alert=True)
        return
    await callback.answer(bot_instance.start_link or "Ссылка пока недоступна", show_alert=True)


@router.callback_query(F.data.startswith("admin:bot_toggle:"))
async def cb_admin_bot_toggle(
    callback: CallbackQuery,
    app: AppContext,
    staff_user: StaffUser,
    screen_renderer: ScreenRenderer,
) -> None:
    bot_id = int(callback.data.split(":")[-1])
    bot_instance = await get_allowed_bot(app, staff_user, bot_id)
    if bot_instance is None:
        await callback.answer(app.i18n.t("ru", "unknown_bot"), show_alert=True)
        return

    updated = await app.bots.toggle_active(bot_instance.id)
    if updated is None:
        await callback.answer(app.i18n.t("ru", "unknown_bot"), show_alert=True)
        return

    runner = app.runner
    if runner and hasattr(runner, "launch_client_bot") and hasattr(runner, "stop_client_bot"):
        if updated.is_active:
            await runner.launch_client_bot(updated)
        else:
            await runner.stop_client_bot(updated.id)
    await render_bot_detail(callback, app, staff_user, screen_renderer, updated)


@router.callback_query(F.data.startswith("admin:bot_delete:"))
async def cb_admin_bot_delete(
    callback: CallbackQuery,
    app: AppContext,
    staff_user: StaffUser,
    screen_renderer: ScreenRenderer,
) -> None:
    bot_id = int(callback.data.split(":")[-1])
    bot_instance = await get_allowed_bot(app, staff_user, bot_id)
    if bot_instance is None:
        await callback.answer(app.i18n.t("ru", "unknown_bot"), show_alert=True)
        return

    await app.bots.archive(bot_instance.id)
    runner = app.runner
    if runner and hasattr(runner, "stop_client_bot"):
        await runner.stop_client_bot(bot_instance.id)
    await render_personal_bots(callback, app, staff_user, screen_renderer)


@router.callback_query(F.data.startswith("admin:bot_welcome:"))
async def cb_admin_bot_welcome(
    callback: CallbackQuery,
    state: FSMContext,
    app: AppContext,
    staff_user: StaffUser,
    screen_renderer: ScreenRenderer,
) -> None:
    bot_id = int(callback.data.split(":")[-1])
    bot_instance = await get_allowed_bot(app, staff_user, bot_id)
    if bot_instance is None:
        await callback.answer(app.i18n.t("ru", "unknown_bot"), show_alert=True)
        return
    await state.set_state(EditBotTextState.waiting_welcome)
    await state.update_data(bot_id=bot_instance.id)
    await screen_renderer.show(
        callback,
        ScreenPayload(
            text=app.i18n.t("ru", "send_welcome_text"),
            keyboard=back_home_keyboard(),
            media_path=app.media.screen("admin_bot"),
        ),
    )


@router.callback_query(F.data.startswith("admin:bot_farewell:"))
async def cb_admin_bot_farewell(
    callback: CallbackQuery,
    state: FSMContext,
    app: AppContext,
    staff_user: StaffUser,
    screen_renderer: ScreenRenderer,
) -> None:
    bot_id = int(callback.data.split(":")[-1])
    bot_instance = await get_allowed_bot(app, staff_user, bot_id)
    if bot_instance is None:
        await callback.answer(app.i18n.t("ru", "unknown_bot"), show_alert=True)
        return
    await state.set_state(EditBotTextState.waiting_farewell)
    await state.update_data(bot_id=bot_instance.id)
    await screen_renderer.show(
        callback,
        ScreenPayload(
            text=app.i18n.t("ru", "send_farewell_text"),
            keyboard=back_home_keyboard(),
            media_path=app.media.screen("admin_bot"),
        ),
    )


@router.message(EditBotTextState.waiting_welcome)
async def admin_waiting_welcome(
    message: Message,
    state: FSMContext,
    app: AppContext,
    staff_user: StaffUser,
    screen_renderer: ScreenRenderer,
) -> None:
    if not message.text:
        await message.answer(app.i18n.t("ru", "unsupported_message"))
        return
    data = await state.get_data()
    bot_instance = await get_allowed_bot(app, staff_user, int(data["bot_id"]))
    if bot_instance is None:
        await message.answer(app.i18n.t("ru", "unknown_bot"))
        await state.clear()
        return
    await app.bots.update_welcome_text(bot_instance.id, message.text)
    await state.clear()
    refreshed = await app.bots.get_by_id(bot_instance.id)
    if refreshed is not None:
        await render_bot_detail(message, app, staff_user, screen_renderer, refreshed)


@router.message(EditBotTextState.waiting_farewell)
async def admin_waiting_farewell(
    message: Message,
    state: FSMContext,
    app: AppContext,
    staff_user: StaffUser,
    screen_renderer: ScreenRenderer,
) -> None:
    if not message.text:
        await message.answer(app.i18n.t("ru", "unsupported_message"))
        return
    data = await state.get_data()
    bot_instance = await get_allowed_bot(app, staff_user, int(data["bot_id"]))
    if bot_instance is None:
        await message.answer(app.i18n.t("ru", "unknown_bot"))
        await state.clear()
        return
    await app.bots.update_farewell_text(bot_instance.id, message.text)
    await state.clear()
    refreshed = await app.bots.get_by_id(bot_instance.id)
    if refreshed is not None:
        await render_bot_detail(message, app, staff_user, screen_renderer, refreshed)


@router.callback_query(F.data.startswith("admin:bot_broadcast:"))
async def cb_admin_bot_broadcast(
    callback: CallbackQuery,
    state: FSMContext,
    app: AppContext,
    staff_user: StaffUser,
    screen_renderer: ScreenRenderer,
) -> None:
    bot_id = int(callback.data.split(":")[-1])
    bot_instance = await get_allowed_bot(app, staff_user, bot_id)
    if bot_instance is None:
        await callback.answer(app.i18n.t("ru", "unknown_bot"), show_alert=True)
        return
    await state.set_state(BotBroadcastState.waiting_text)
    await state.update_data(bot_id=bot_instance.id)
    await screen_renderer.show(
        callback,
        ScreenPayload(
            text=app.i18n.t("ru", "send_bot_broadcast"),
            keyboard=back_home_keyboard(),
            media_path=app.media.screen("admin_bot"),
        ),
    )


@router.message(BotBroadcastState.waiting_text)
async def admin_waiting_bot_broadcast(
    message: Message,
    state: FSMContext,
    app: AppContext,
    staff_user: StaffUser,
    screen_renderer: ScreenRenderer,
) -> None:
    if not message.text:
        await message.answer(app.i18n.t("ru", "unsupported_message"))
        return
    data = await state.get_data()
    bot_instance = await get_allowed_bot(app, staff_user, int(data["bot_id"]))
    if bot_instance is None:
        await message.answer(app.i18n.t("ru", "unknown_bot"))
        await state.clear()
        return
    user_ids = [profile.telegram_id for profile in await app.users.list_for_bot(bot_instance.id)]
    sent, failed = await broadcast_with_instance(bot_instance, user_ids, message.text, app)
    await state.clear()
    await message.answer(app.i18n.t("ru", "broadcast_done", sent=sent, failed=failed))
    refreshed = await app.bots.get_by_id(bot_instance.id)
    if refreshed is not None:
        await render_bot_detail(message, app, staff_user, screen_renderer, refreshed)


@router.callback_query(F.data == "admin:owner:rate")
async def cb_owner_rate(
    callback: CallbackQuery,
    state: FSMContext,
    app: AppContext,
    staff_user: StaffUser,
    screen_renderer: ScreenRenderer,
) -> None:
    if not staff_user.is_owner:
        await callback.answer(app.i18n.t("ru", "owner_only"), show_alert=True)
        return
    await state.set_state(OwnerRateState.waiting_staff_ref)
    await screen_renderer.show(
        callback,
        ScreenPayload(
            text=app.i18n.t("ru", "send_rate_tag"),
            keyboard=back_home_keyboard(),
            media_path=app.media.screen("admin_owner"),
        ),
    )


@router.callback_query(F.data == "admin:owner:referral_stats")
async def cb_owner_referral_stats(
    callback: CallbackQuery,
    state: FSMContext,
    app: AppContext,
    staff_user: StaffUser,
    screen_renderer: ScreenRenderer,
) -> None:
    if not staff_user.is_owner:
        await callback.answer(app.i18n.t("ru", "owner_only"), show_alert=True)
        return
    await state.set_state(OwnerReferralStatsState.waiting_staff_ref)
    await screen_renderer.show(
        callback,
        ScreenPayload(
            text=app.i18n.t("ru", "send_referral_stats_tag"),
            keyboard=back_home_keyboard(),
            media_path=app.media.screen("admin_owner"),
        ),
    )


@router.message(OwnerRateState.waiting_staff_ref)
async def owner_waiting_staff_ref(
    message: Message,
    state: FSMContext,
    app: AppContext,
    staff_user: StaffUser,
) -> None:
    if not staff_user.is_owner:
        await state.clear()
        return
    if not message.text:
        await message.answer(app.i18n.t("ru", "unsupported_message"))
        return
    target = await resolve_staff_by_reference(app, message.text)
    if target is None:
        await message.answer("Админ не найден.")
        return
    await state.update_data(staff_id=target.id)
    await state.set_state(OwnerRateState.waiting_rate)
    await message.answer(app.i18n.t("ru", "send_rate_value"))


@router.message(OwnerRateState.waiting_rate)
async def owner_waiting_rate(
    message: Message,
    state: FSMContext,
    app: AppContext,
    staff_user: StaffUser,
    screen_renderer: ScreenRenderer,
) -> None:
    if not staff_user.is_owner:
        await state.clear()
        return
    if not message.text:
        await message.answer(app.i18n.t("ru", "unsupported_message"))
        return
    try:
        rate = int(message.text.strip())
    except ValueError:
        await message.answer(app.i18n.t("ru", "invalid_rate"))
        return
    if not 0 <= rate <= 100:
        await message.answer(app.i18n.t("ru", "invalid_rate"))
        return
    data = await state.get_data()
    await app.staff.update_rate(int(data["staff_id"]), rate)
    await state.clear()
    await message.answer(app.i18n.t("ru", "rate_updated", rate=rate))
    await render_owner_panel(message, app, screen_renderer)


@router.message(OwnerReferralStatsState.waiting_staff_ref)
async def owner_waiting_referral_stats(
    message: Message,
    state: FSMContext,
    app: AppContext,
    staff_user: StaffUser,
    screen_renderer: ScreenRenderer,
) -> None:
    if not staff_user.is_owner:
        await state.clear()
        return
    if not message.text:
        await message.answer(app.i18n.t("ru", "unsupported_message"))
        return
    target = await resolve_staff_by_reference(app, message.text)
    if target is None:
        await message.answer("Админ не найден.")
        return
    await state.clear()
    await render_referral_stats(message, app, screen_renderer, target)


@router.callback_query(F.data == "admin:owner:broadcast")
async def cb_owner_broadcast(
    callback: CallbackQuery,
    state: FSMContext,
    app: AppContext,
    staff_user: StaffUser,
    screen_renderer: ScreenRenderer,
) -> None:
    if not staff_user.is_owner:
        await callback.answer(app.i18n.t("ru", "owner_only"), show_alert=True)
        return
    await state.set_state(OwnerBroadcastState.waiting_text)
    await screen_renderer.show(
        callback,
        ScreenPayload(
            text=app.i18n.t("ru", "send_global_broadcast"),
            keyboard=back_home_keyboard(),
            media_path=app.media.screen("admin_owner"),
        ),
    )


@router.message(OwnerBroadcastState.waiting_text)
async def owner_waiting_broadcast(
    message: Message,
    state: FSMContext,
    app: AppContext,
    staff_user: StaffUser,
    screen_renderer: ScreenRenderer,
) -> None:
    if not staff_user.is_owner:
        await state.clear()
        return
    if not message.text:
        await message.answer(app.i18n.t("ru", "unsupported_message"))
        return
    sent = 0
    failed = 0
    for bot_instance in await app.bots.list_active_client_bots():
        user_ids = [profile.telegram_id for profile in await app.users.list_for_bot(bot_instance.id)]
        item_sent, item_failed = await broadcast_with_instance(bot_instance, user_ids, message.text, app)
        sent += item_sent
        failed += item_failed
    await state.clear()
    await message.answer(app.i18n.t("ru", "broadcast_done", sent=sent, failed=failed))
    await render_owner_panel(message, app, screen_renderer)


@router.callback_query(F.data == "admin:owner:main_link")
async def cb_owner_main_link(
    callback: CallbackQuery,
    state: FSMContext,
    app: AppContext,
    staff_user: StaffUser,
    screen_renderer: ScreenRenderer,
) -> None:
    if not staff_user.is_owner:
        await callback.answer(app.i18n.t("ru", "owner_only"), show_alert=True)
        return
    await state.set_state(OwnerMainLinkState.waiting_link)
    await screen_renderer.show(
        callback,
        ScreenPayload(
            text=app.i18n.t("ru", "send_main_bot_link"),
            keyboard=back_home_keyboard(),
            media_path=app.media.screen("admin_owner"),
        ),
    )


@router.message(OwnerMainLinkState.waiting_link)
async def owner_waiting_link(
    message: Message,
    state: FSMContext,
    app: AppContext,
    staff_user: StaffUser,
    screen_renderer: ScreenRenderer,
) -> None:
    if not staff_user.is_owner:
        await state.clear()
        return
    if not message.text:
        await message.answer(app.i18n.t("ru", "unsupported_message"))
        return
    link = message.text.strip()
    if not link.startswith("https://t.me/"):
        await message.answer(app.i18n.t("ru", "invalid_link"))
        return
    await app.app_settings.set("main_bot_link", link)
    await state.clear()
    await message.answer(app.i18n.t("ru", "main_link_updated"))
    await render_owner_panel(message, app, screen_renderer)


async def render_admin_home(
    target: Message | CallbackQuery,
    app: AppContext,
    staff_user: StaffUser,
    screen_renderer: ScreenRenderer,
) -> None:
    overview = await app.stats.get_staff_overview(staff_user.id)
    text = (
        f"{app.i18n.t('ru', 'admin_home')}\n\n"
        f"Тег: <code>{staff_user.referral_tag}</code>\n"
        f"Ставка: <b>{staff_user.commission_rate}%</b>\n"
        f"Заработано: <b>{format_money(overview.earned_cents)}</b>"
    )
    await screen_renderer.show(
        target,
        ScreenPayload(
            text=text,
            keyboard=home_keyboard(is_owner=staff_user.is_owner),
            media_path=app.media.screen("admin_home"),
        ),
    )


async def render_personal_bots(
    target: Message | CallbackQuery,
    app: AppContext,
    staff_user: StaffUser,
    screen_renderer: ScreenRenderer,
) -> None:
    bots = await app.bots.list_personal_bots(staff_user.id)
    text = app.i18n.t("ru", "admin_personal_text")
    if bots:
        lines = "\n".join(
            f"• <b>{escape(item.title)}</b> — {'вкл' if item.is_active else 'выкл'}"
            for item in bots
        )
        text = f"{text}\n\n{lines}"
    await screen_renderer.show(
        target,
        ScreenPayload(
            text=text,
            keyboard=personal_bots_keyboard(bots),
            media_path=app.media.screen("admin_bots"),
        ),
    )


async def render_bot_detail(
    target: Message | CallbackQuery,
    app: AppContext,
    staff_user: StaffUser,
    screen_renderer: ScreenRenderer,
    bot_instance: BotInstance,
) -> None:
    if not (staff_user.is_owner or bot_instance.owner_staff_id == staff_user.id):
        return
    stats = await app.stats.get_bot_stats(bot_instance.id)
    audience = "RU" if bot_instance.audience is Audience.RU else "Бурж"
    text = app.i18n.t(
        "ru",
        "admin_bot_detail",
        title=escape(bot_instance.title),
        status="Включен" if bot_instance.is_active else "Выключен",
        audience=audience,
        link=bot_instance.start_link or "не определена",
        users_total=stats.total_users,
        users_month=stats.month_users,
        users_week=stats.week_users,
        users_today=stats.today_users,
        paid_total=stats.paid_payments,
        payment_total=stats.total_payments,
        paid_month=stats.month_paid_payments,
        payment_month=stats.month_total_payments,
        paid_week=stats.week_paid_payments,
        payment_week=stats.week_total_payments,
        paid_today=stats.today_paid_payments,
        payment_today=stats.today_total_payments,
        earned=format_money(stats.earned_cents),
    )
    await screen_renderer.show(
        target,
        ScreenPayload(
            text=text,
            keyboard=bot_detail_keyboard(bot_instance),
            media_path=app.media.screen("admin_bot"),
        ),
    )


async def render_owner_panel(
    target: Message | CallbackQuery,
    app: AppContext,
    screen_renderer: ScreenRenderer,
) -> None:
    stats = await app.stats.get_owner_stats()
    text = app.i18n.t(
        "ru",
        "admin_owner_text",
        admins=stats.admins,
        bots=stats.client_bots,
        users=stats.users,
        generations=stats.generations,
        revenue=format_money(stats.revenue_cents),
        payouts=format_money(stats.payouts_cents),
    )
    await screen_renderer.show(
        target,
        ScreenPayload(
            text=text,
            keyboard=owner_keyboard(),
            media_path=app.media.screen("admin_owner"),
        ),
    )


async def render_referral_stats(
    target: Message | CallbackQuery,
    app: AppContext,
    screen_renderer: ScreenRenderer,
    staff_member: StaffUser,
) -> None:
    overview = await app.stats.get_staff_overview(staff_member.id)
    personal_bots = await app.bots.list_personal_bots(staff_member.id)
    username = f"@{escape(staff_member.username)}" if staff_member.username else "не указан"
    bot_list_block = ""
    if personal_bots:
        bot_lines = "\n".join(
            f"• <b>{escape(item.title)}</b> — {'вкл' if item.is_active else 'выкл'}"
            for item in personal_bots
        )
        bot_list_block = f"Боты:\n{bot_lines}\n\n"
    text = app.i18n.t(
        "ru",
        "admin_referral_stats_text",
        name=escape(staff_member.full_name),
        username=username,
        tag=staff_member.referral_tag,
        rate=staff_member.commission_rate,
        bots=len(personal_bots),
        bot_list_block=bot_list_block,
        users_total=overview.total_users,
        users_month=overview.month_users,
        users_week=overview.week_users,
        users_today=overview.today_users,
        paid_total=overview.paid_payments,
        payment_total=overview.total_payments,
        paid_month=overview.month_paid_payments,
        payment_month=overview.month_total_payments,
        paid_week=overview.week_paid_payments,
        payment_week=overview.week_total_payments,
        paid_today=overview.today_paid_payments,
        payment_today=overview.today_total_payments,
        generations=overview.total_generations,
        earned=format_money(overview.earned_cents),
    )
    await screen_renderer.show(
        target,
        ScreenPayload(
            text=text,
            keyboard=owner_keyboard(),
            media_path=app.media.screen("admin_owner"),
        ),
    )


async def get_allowed_bot(
    app: AppContext,
    staff_user: StaffUser,
    bot_instance_id: int,
) -> BotInstance | None:
    bot_instance = await app.bots.get_by_id(bot_instance_id)
    if bot_instance is None:
        return None
    if staff_user.is_owner or bot_instance.owner_staff_id == staff_user.id:
        return bot_instance
    return None


async def resolve_staff_by_reference(
    app: AppContext,
    reference: str,
) -> StaffUser | None:
    value = reference.strip().lstrip("@")
    target = await app.staff.get_by_referral_tag(value)
    if target is not None:
        return target
    admins = await app.staff.list_admins()
    return next((item for item in admins if item.username == value), None)


def build_referral_links(raw_link: str, tag: str) -> tuple[str, str]:
    if not raw_link:
        return "", ""
    base = raw_link.rstrip("/")
    start_link = f"{base}?start={quote(tag)}"
    permanent = start_link
    if base.startswith("https://t.me/"):
        permanent = start_link.replace("https://t.me/", "https://telegram.dog/")
    return start_link, permanent


async def broadcast_with_instance(
    bot_instance: BotInstance,
    user_ids: list[int],
    text: str,
    app: AppContext,
) -> tuple[int, int]:
    runner = app.runner
    bot: Bot | None = None
    temp_bot: Bot | None = None
    if runner and hasattr(runner, "get_client_bot"):
        bot = runner.get_client_bot(bot_instance.id)
    if bot is None:
        temp_bot = Bot(
            token=bot_instance.token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        bot = temp_bot

    sent = 0
    failed = 0
    try:
        for user_id in user_ids:
            try:
                await bot.send_message(user_id, text)
                sent += 1
            except Exception:
                failed += 1
    finally:
        if temp_bot is not None:
            await temp_bot.session.close()
    return sent, failed


async def delete_message_safe(message: Message) -> None:
    try:
        await message.delete()
    except Exception:
        return
