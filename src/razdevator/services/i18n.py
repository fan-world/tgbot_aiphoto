from __future__ import annotations


MESSAGES = {
    "ru": {
        "back": "← Назад",
        "close": "✖ Закрыть",
        "profile": "👤 Профиль",
        "animate_photo": "✨ Оживить фото",
        "shop": "🛍 Магазин",
        "topup": "💎 Пополнить баланс",
        "language": "🌐 Язык",
        "general_bot": "🔗 Общий бот",
        "personal_bots": "🤖 Личные боты",
        "owner_panel": "🛡 Панель владельца",
        "admin_profile": "👤 Профиль",
        "create_bot": "＋ Создать бота",
        "broadcast": "📣 Рассылка",
        "links": "🔗 Ссылки",
        "greeting": "👋 Приветствие",
        "farewell": "🖤 Прощание",
        "delete": "🗑 Удалить",
        "toggle_on": "⏻ Выключить",
        "toggle_off": "⏻ Включить",
        "set_rate": "💸 Ставка",
        "set_main_link": "🔗 Главный бот",
        "owner_stats": "📊 Финансы и статистика",
        "global_broadcast": "📣 Рассылка по всем ботам",
        "ru_bot": "🇷🇺 Русский бот",
        "en_bot": "🌍 International bot",
        "admin_home": (
            "<b>⚡ Партнерская панель Razdevashka AI 18+</b>\n\n"
            "Управляйте ботами, реферальными ссылками, ставкой и статистикой из одного меню."
        ),
        "admin_general_hint": (
            "Лейте трафик на общий бот и используйте персональную start-ссылку для отслеживания."
        ),
        "admin_profile_text": (
            "<b>👤 Ваш профиль</b>\n\n"
            "Тег: <code>{tag}</code>\n"
            "Ставка: <b>{rate}%</b>\n"
            "Личных ботов: <b>{bots}</b>\n"
            "Заработано: <b>{earned}</b>"
        ),
        "admin_owner_text": (
            "<b>🛡 Панель владельца</b>\n\n"
            "Админы: <b>{admins}</b>\n"
            "Клиентские боты: <b>{bots}</b>\n"
            "Пользователи: <b>{users}</b>\n"
            "Генерации: <b>{generations}</b>\n"
            "Доход: <b>{revenue}</b>\n"
            "Выплаты: <b>{payouts}</b>"
        ),
        "admin_general_text": (
            "<b>🔗 Общий бот и трафик</b>\n\n"
            "{hint}\n\n"
            "Start-ссылка: {raw_link}\n"
            "Постоянная ссылка: {permanent_link}\n\n"
            "<b>👥 Пользователи</b>\n"
            "Всего: <b>{users_total}</b>\n"
            "Месяц: <b>{users_month}</b>\n"
            "Неделя: <b>{users_week}</b>\n"
            "Сегодня: <b>{users_today}</b>\n\n"
            "<b>💳 Платежи</b>\n"
            "Всего: <b>{paid_total} / {payment_total}</b>\n"
            "Месяц: <b>{paid_month} / {payment_month}</b>\n"
            "Неделя: <b>{paid_week} / {payment_week}</b>\n"
            "Сегодня: <b>{paid_today} / {payment_today}</b>\n\n"
            "Заработано: <b>{earned}</b>"
        ),
        "admin_personal_text": (
            "<b>🤖 Ваши клиентские боты</b>\n\n"
            "Здесь можно создать новый бот, включить или выключить его, поменять тексты и отправить рассылку."
        ),
        "admin_bot_detail": (
            "<b>📊 Статистика бота {title}</b>\n\n"
            "Статус: <b>{status}</b>\n"
            "Аудитория: <b>{audience}</b>\n"
            "Ссылка: {link}\n\n"
            "<b>👥 Пользователи</b>\n"
            "Всего: <b>{users_total}</b>\n"
            "Месяц: <b>{users_month}</b>\n"
            "Неделя: <b>{users_week}</b>\n"
            "Сегодня: <b>{users_today}</b>\n\n"
            "<b>💳 Платежи</b>\n"
            "Всего: <b>{paid_total} / {payment_total}</b>\n"
            "Месяц: <b>{paid_month} / {payment_month}</b>\n"
            "Неделя: <b>{paid_week} / {payment_week}</b>\n"
            "Сегодня: <b>{paid_today} / {payment_today}</b>\n\n"
            "Заработано: <b>{earned}</b>"
        ),
        "choose_bot_locale": "Выберите аудиторию для нового бота.",
        "send_bot_token": "Отправьте токен нового бота из BotFather. Название подтянется автоматически.",
        "send_bot_title": "Теперь отправьте отображаемое название бота.",
        "bot_created": "Бот <b>{title}</b> добавлен и запущен.",
        "send_welcome_text": "Пришлите новый welcome-текст для этого бота.",
        "send_farewell_text": "Пришлите новый farewell-текст для этого бота.",
        "send_bot_broadcast": "Пришлите текст рассылки для этого бота.",
        "send_global_broadcast": "Пришлите текст глобальной рассылки по всем клиентским ботам.",
        "send_rate_tag": "Пришлите тег админа без @ или его referral tag.",
        "send_rate_value": "Пришлите новый процент от 0 до 100.",
        "send_referral_stats_tag": "Пришлите тег админа без @ или его referral tag, чтобы открыть статистику.",
        "send_main_bot_link": "Пришлите ссылку на главного бота в формате https://t.me/...",
        "rate_updated": "Ставка обновлена: <b>{rate}%</b>.",
        "main_link_updated": "Ссылка на главного бота обновлена.",
        "admin_referral_stats_text": (
            "<b>📈 Статистика реферала</b>\n\n"
            "Имя: <b>{name}</b>\n"
            "Username: <b>{username}</b>\n"
            "Тег: <code>{tag}</code>\n"
            "Ставка: <b>{rate}%</b>\n"
            "Личных ботов: <b>{bots}</b>\n"
            "{bot_list_block}"
            "<b>👥 Пользователи</b>\n"
            "Всего: <b>{users_total}</b>\n"
            "Месяц: <b>{users_month}</b>\n"
            "Неделя: <b>{users_week}</b>\n"
            "Сегодня: <b>{users_today}</b>\n\n"
            "<b>💳 Платежи</b>\n"
            "Всего: <b>{paid_total} / {payment_total}</b>\n"
            "Месяц: <b>{paid_month} / {payment_month}</b>\n"
            "Неделя: <b>{paid_week} / {payment_week}</b>\n"
            "Сегодня: <b>{paid_today} / {payment_today}</b>\n\n"
            "Генерации: <b>{generations}</b>\n"
            "Заработано: <b>{earned}</b>"
        ),
        "broadcast_done": (
            "📣 Рассылка завершена.\n"
            "Доставлено: <b>{sent}</b>\n"
            "Ошибок: <b>{failed}</b>"
        ),
        "client_home": (
            "🔥 <b>Добро пожаловать, {name}!</b>\n\n"
            "Ты в <b>{title}</b> — AI 18+ боте для оживления фото.\n"
            "Выбирай нужный режим ниже и запускай генерацию."
        ),
        "client_profile": (
            "<b>👤 Твой профиль</b>\n\n"
            "Баланс: <b>{balance}</b>\n"
            "Успешно: <b>{success}</b>\n"
            "Неудачно: <b>{failed}</b>"
        ),
        "client_templates": (
            "<b>🎞 Оживление фото</b>\n\n"
            "Выбери стиль анимации для фото.\n"
            "Баланс: <b>{balance}</b>"
        ),
        "client_sound_duration": (
            "<b>🎙 Видео со звуком</b>\n\n"
            "Выбери длительность ролика.\n"
            "Баланс: <b>{balance}</b>"
        ),
        "client_sound_templates": (
            "<b>🎙 Видео со звуком</b>\n\n"
            "Длительность: <b>{video_length}</b>\n"
            "Выбери звуковой сценарий.\n"
            "Баланс: <b>{balance}</b>"
        ),
        "client_shop": (
            "<b>🛍 Магазин монет</b>\n\n"
            "Выбери пакет пополнения для новых генераций.\n"
            "Платежный провайдер: <b>{provider}</b>"
        ),
        "client_payment_methods": (
            "💰 <b>Выбор способа оплаты</b>\n"
            "Выбери удобный вариант.\n\n"
            "После оплаты на баланс поступит <b>{credits}</b> монет."
        ),
        "client_payment_invoice": (
            "💳 <b>Счет на оплату</b>\n"
            "ID: <code>{transaction_id}</code>\n\n"
            "Сумма: <b>{amount}</b>\n"
            "{link_line}"
            "{method_line}"
            "{expires_line}"
            "{usdt_line}"
            "{status_line}"
        ),
        "client_payment_success": (
            "✅ <b>Оплата подтверждена</b>\n\n"
            "На баланс зачислено <b>{credits}</b> монет."
        ),
        "client_payment_pending": "Платеж еще в обработке. Нажми проверку чуть позже.",
        "client_payment_canceled": "Платеж был отменен или отклонен.",
        "platega_not_configured": "Platega пока не настроена: нужны merchant id и secret.",
        "payment_create_error": "Не удалось создать платеж. Попробуйте немного позже.",
        "client_language": (
            "<b>🌐 Язык интерфейса</b>\n\n"
            "Сейчас выбран язык: <b>{language}</b>"
        ),
        "send_photo_for_template": (
            "✨ Выбран шаблон <b>{template}</b>.\n"
            "Теперь отправь фото для генерации."
        ),
        "send_photo_for_audio_template": (
            "🎙 Выбран шаблон <b>{template}</b>.\n"
            "Длительность: <b>{video_length}</b>\n"
            "Теперь отправь фото для генерации."
        ),
        "generation_queued": (
            "⏳ Заявка принята в очередь.\n"
            "Шаблон: <b>{template}</b>\n"
            "Списано: <b>{credits}</b>"
        ),
        "generation_loader_active": (
            "⏳ <b>Генерация видео</b>\n"
            "🎞 Сценарий: <b>{template}</b>\n\n"
            "Прогресс: <code>{bar}</code> <b>{progress}%</b>\n"
            "ID: <code>{task_id}</code>\n\n"
            "Обычно это занимает 1-3 минуты."
        ),
        "generation_loader_ready": (
            "✅ <b>Видео готово</b>\n"
            "🎞 Сценарий: <b>{template}</b>\n\n"
            "Прогресс: <code>{bar}</code> <b>100%</b>\n"
            "ID: <code>{task_id}</code>\n\n"
            "Ролик уже отправлен ниже."
        ),
        "generation_loader_failed": (
            "❌ <b>Генерация не удалась</b>\n"
            "🎞 Сценарий: <b>{template}</b>\n\n"
            "ID: <code>{task_id}</code>\n\n"
            "{reason}\n"
            "Кредиты возвращены на баланс."
        ),
        "generation_ready": (
            "✅ <b>Твое видео готово</b>\n\n"
            "Шаблон: <b>{template}</b>"
        ),
        "generation_failed": (
            "❌ <b>Генерация не удалась</b>\n\n"
            "{reason}\n"
            "Кредиты возвращены на баланс."
        ),
        "generation_submit_error": (
            "Сервис генерации сейчас недоступен.\n"
            "Попробуй еще раз позже."
        ),
        "audio_generation_unavailable": (
            "Генерация со звуком временно недоступна на стороне провайдера.\n"
            "Попробуй позже или используй обычное оживление фото."
        ),
        "not_enough_balance": "Недостаточно монет на балансе.",
        "payment_placeholder": (
            "Сейчас подключена заглушка оплаты.\n"
            "Провайдер: <b>{provider}</b>\n"
            "Сумма: <b>{amount}</b>"
        ),
        "language_updated": "Язык обновлен.",
        "unknown_bot": "Бот не найден или у вас нет доступа.",
        "owner_only": "Этот раздел доступен только владельцу.",
        "invalid_rate": "Нужен процент от 0 до 100.",
        "invalid_link": "Нужна ссылка формата https://t.me/...",
        "invalid_token": "Токен не прошел проверку. Проверьте его и попробуйте снова.",
        "unsupported_message": "Сейчас ожидается текстовое сообщение.",
    },
    "en": {
        "back": "← Back",
        "close": "✖ Close",
        "profile": "👤 Profile",
        "animate_photo": "✨ Animate Photo",
        "shop": "🛍 Shop",
        "topup": "💎 Top Up",
        "language": "🌐 Language",
        "client_home": (
            "🔥 <b>Welcome, {name}!</b>\n\n"
            "You are inside <b>{title}</b> — an AI 18+ bot that turns photos into animated scenes.\n"
            "Choose a mode below and start generating."
        ),
        "client_profile": (
            "<b>👤 Your profile</b>\n\n"
            "Balance: <b>{balance}</b>\n"
            "Success: <b>{success}</b>\n"
            "Failed: <b>{failed}</b>"
        ),
        "client_templates": (
            "<b>🎞 Photo Animation</b>\n\n"
            "Choose an animation style for your photo.\n"
            "Balance: <b>{balance}</b>"
        ),
        "client_sound_duration": (
            "<b>🎙 Video With Sound</b>\n\n"
            "Choose the clip duration.\n"
            "Balance: <b>{balance}</b>"
        ),
        "client_sound_templates": (
            "<b>🎙 Video With Sound</b>\n\n"
            "Length: <b>{video_length}</b>\n"
            "Choose a sound scenario.\n"
            "Balance: <b>{balance}</b>"
        ),
        "client_shop": (
            "<b>🛍 Coin Shop</b>\n\n"
            "Choose a top-up package for new generations.\n"
            "Payment provider: <b>{provider}</b>"
        ),
        "client_payment_methods": (
            "💰 <b>Choose payment method</b>\n"
            "Pick the most convenient option.\n\n"
            "After payment you will receive <b>{credits}</b> coins."
        ),
        "client_payment_invoice": (
            "💳 <b>Payment invoice</b>\n"
            "ID: <code>{transaction_id}</code>\n\n"
            "Amount: <b>{amount}</b>\n"
            "{link_line}"
            "{method_line}"
            "{expires_line}"
            "{usdt_line}"
            "{status_line}"
        ),
        "client_payment_success": (
            "✅ <b>Payment confirmed</b>\n\n"
            "<b>{credits}</b> coins were added to your balance."
        ),
        "client_payment_pending": "Payment is still pending. Check again in a moment.",
        "client_payment_canceled": "Payment was canceled or declined.",
        "platega_not_configured": "Platega is not configured yet: merchant id and secret are required.",
        "payment_create_error": "Could not create the payment. Please try again later.",
        "client_language": (
            "<b>🌐 Interface language</b>\n\n"
            "Current language: <b>{language}</b>"
        ),
        "send_photo_for_template": (
            "✨ Template <b>{template}</b> selected.\n"
            "Now send the photo for generation."
        ),
        "send_photo_for_audio_template": (
            "🎙 Template <b>{template}</b> selected.\n"
            "Length: <b>{video_length}</b>\n"
            "Now send the photo for generation."
        ),
        "generation_queued": (
            "⏳ Your generation is queued.\n"
            "Template: <b>{template}</b>\n"
            "Debited: <b>{credits}</b>"
        ),
        "generation_loader_active": (
            "⏳ <b>Video Generation</b>\n"
            "🎞 Scenario: <b>{template}</b>\n\n"
            "Progress: <code>{bar}</code> <b>{progress}%</b>\n"
            "ID: <code>{task_id}</code>\n\n"
            "This usually takes 1-3 minutes."
        ),
        "generation_loader_ready": (
            "✅ <b>Video Ready</b>\n"
            "🎞 Scenario: <b>{template}</b>\n\n"
            "Progress: <code>{bar}</code> <b>100%</b>\n"
            "ID: <code>{task_id}</code>\n\n"
            "The clip has already been sent below."
        ),
        "generation_loader_failed": (
            "❌ <b>Generation failed</b>\n"
            "🎞 Scenario: <b>{template}</b>\n\n"
            "ID: <code>{task_id}</code>\n\n"
            "{reason}\n"
            "Credits were returned to your balance."
        ),
        "generation_ready": (
            "✅ <b>Your video is ready</b>\n\n"
            "Template: <b>{template}</b>"
        ),
        "generation_failed": (
            "❌ <b>Generation failed</b>\n\n"
            "{reason}\n"
            "Credits were returned to your balance."
        ),
        "generation_submit_error": (
            "The generation service is unavailable right now.\n"
            "Please try again later."
        ),
        "audio_generation_unavailable": (
            "Audio generation is temporarily unavailable on the provider side.\n"
            "Please try again later or use the regular animation mode."
        ),
        "not_enough_balance": "Not enough balance.",
        "payment_placeholder": (
            "A payment stub is connected for now.\n"
            "Provider: <b>{provider}</b>\n"
            "Amount: <b>{amount}</b>"
        ),
        "language_updated": "Language updated.",
        "unsupported_message": "A text message is expected right now.",
    },
}


class I18n:
    def t(self, locale: str, key: str, **kwargs: object) -> str:
        lang = locale if locale in MESSAGES else ("ru" if locale == "ru" else "en")
        fallback_lang = "ru" if lang == "ru" else "en"
        template = (
            MESSAGES.get(lang, {}).get(key)
            or MESSAGES.get(fallback_lang, {}).get(key)
            or MESSAGES["ru"].get(key, key)
        )
        return template.format(**kwargs)
