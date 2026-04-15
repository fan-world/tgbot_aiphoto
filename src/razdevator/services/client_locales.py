from __future__ import annotations

from razdevator.core.enums import Audience


LANGUAGE_OPTIONS: dict[Audience, tuple[tuple[str, str], ...]] = {
    Audience.RU: (
        ("ru", "🇷🇺 Русский"),
        ("en", "🇬🇧 English"),
    ),
    Audience.EN: (
        ("en", "🇬🇧 English"),
        ("hi", "🇮🇳 हिन्दी"),
        ("ar", "🇸🇦 العربية"),
        ("es", "🇪🇸 Español"),
        ("pt", "🇵🇹 Português"),
        ("tr", "🇹🇷 Türkçe"),
        ("fr", "🇫🇷 Français"),
        ("de", "🇩🇪 Deutsch"),
        ("id", "🇮🇩 Bahasa Indonesia"),
        ("vi", "🇻🇳 Tiếng Việt"),
    ),
}

LANGUAGE_NAMES: dict[str, str] = {
    "ru": "Русский",
    "en": "English",
    "hi": "हिन्दी",
    "ar": "العربية",
    "es": "Español",
    "pt": "Português",
    "tr": "Türkçe",
    "fr": "Français",
    "de": "Deutsch",
    "id": "Bahasa Indonesia",
    "vi": "Tiếng Việt",
}

BUTTON_LABELS: dict[str, dict[str, str]] = {
    "ru": {
        "profile": "👤 Профиль",
        "animate_photo": "✨ Оживить фото",
        "animate_photo_sound": "🎙 Оживить со звуком",
        "shop": "🛍 Магазин",
        "topup": "💎 Пополнить баланс",
        "language": "🌐 Язык",
        "back": "← Назад",
        "close": "✖ Закрыть",
        "pay": "💳 Оплатить",
        "check_payment": "🔄 Проверить оплату",
        "sound_short": "🎧 Быстрый ролик • 5 сек",
        "sound_long": "🎬 Длинный ролик • 10 сек",
    },
    "en": {
        "profile": "👤 Profile",
        "animate_photo": "✨ Animate Photo",
        "animate_photo_sound": "🎙 Animate With Sound",
        "shop": "🛍 Shop",
        "topup": "💎 Top Up",
        "language": "🌐 Language",
        "back": "← Back",
        "close": "✖ Close",
        "pay": "💳 Pay",
        "check_payment": "🔄 Check Payment",
        "sound_short": "🎧 Quick Clip • 5 sec",
        "sound_long": "🎬 Long Clip • 10 sec",
    },
    "hi": {
        "profile": "👤 प्रोफ़ाइल",
        "animate_photo": "✨ फोटो एनिमेट करें",
        "shop": "🛍 स्टोर",
        "topup": "💎 बैलेंस भरें",
        "language": "🌐 भाषा",
        "back": "← वापस",
        "close": "✖ बंद करें",
        "pay": "💳 भुगतान करें",
        "check_payment": "🔄 भुगतान जांचें",
    },
    "ar": {
        "profile": "👤 الملف الشخصي",
        "animate_photo": "✨ تحريك الصورة",
        "shop": "🛍 المتجر",
        "topup": "💎 شحن الرصيد",
        "language": "🌐 اللغة",
        "back": "← رجوع",
        "close": "✖ إغلاق",
        "pay": "💳 ادفع",
        "check_payment": "🔄 تحقق من الدفع",
    },
    "es": {
        "profile": "👤 Perfil",
        "animate_photo": "✨ Animar foto",
        "shop": "🛍 Tienda",
        "topup": "💎 Recargar saldo",
        "language": "🌐 Idioma",
        "back": "← Atrás",
        "close": "✖ Cerrar",
        "pay": "💳 Pagar",
        "check_payment": "🔄 Verificar pago",
    },
    "pt": {
        "profile": "👤 Perfil",
        "animate_photo": "✨ Animar foto",
        "shop": "🛍 Loja",
        "topup": "💎 Recarregar saldo",
        "language": "🌐 Idioma",
        "back": "← Voltar",
        "close": "✖ Fechar",
        "pay": "💳 Pagar",
        "check_payment": "🔄 Verificar pagamento",
    },
    "tr": {
        "profile": "👤 Profil",
        "animate_photo": "✨ Fotoyu canlandır",
        "shop": "🛍 Mağaza",
        "topup": "💎 Bakiye yükle",
        "language": "🌐 Dil",
        "back": "← Geri",
        "close": "✖ Kapat",
        "pay": "💳 Öde",
        "check_payment": "🔄 Ödemeyi kontrol et",
    },
    "fr": {
        "profile": "👤 Profil",
        "animate_photo": "✨ Animer la photo",
        "shop": "🛍 Boutique",
        "topup": "💎 Recharger le solde",
        "language": "🌐 Langue",
        "back": "← Retour",
        "close": "✖ Fermer",
        "pay": "💳 Payer",
        "check_payment": "🔄 Vérifier le paiement",
    },
    "de": {
        "profile": "👤 Profil",
        "animate_photo": "✨ Foto animieren",
        "shop": "🛍 Shop",
        "topup": "💎 Guthaben aufladen",
        "language": "🌐 Sprache",
        "back": "← Zurück",
        "close": "✖ Schließen",
        "pay": "💳 Bezahlen",
        "check_payment": "🔄 Zahlung prüfen",
    },
    "id": {
        "profile": "👤 Profil",
        "animate_photo": "✨ Animasikan foto",
        "shop": "🛍 Toko",
        "topup": "💎 Isi saldo",
        "language": "🌐 Bahasa",
        "back": "← Kembali",
        "close": "✖ Tutup",
        "pay": "💳 Bayar",
        "check_payment": "🔄 Cek pembayaran",
    },
    "vi": {
        "profile": "👤 Hồ sơ",
        "animate_photo": "✨ Làm ảnh chuyển động",
        "shop": "🛍 Cửa hàng",
        "topup": "💎 Nạp số dư",
        "language": "🌐 Ngôn ngữ",
        "back": "← Quay lại",
        "close": "✖ Đóng",
        "pay": "💳 Thanh toán",
        "check_payment": "🔄 Kiểm tra thanh toán",
    },
}


def supported_locales(audience: Audience) -> tuple[str, ...]:
    return tuple(code for code, _ in LANGUAGE_OPTIONS[audience])


def language_options(audience: Audience) -> tuple[tuple[str, str], ...]:
    return LANGUAGE_OPTIONS[audience]


def language_name(locale: str) -> str:
    return LANGUAGE_NAMES.get(locale, LANGUAGE_NAMES["en"])


def button_label(locale: str, key: str) -> str:
    labels = BUTTON_LABELS.get(locale) or BUTTON_LABELS["en"]
    return labels.get(key, BUTTON_LABELS["en"][key])


def normalize_locale(audience: Audience, user_lang: str | None) -> str:
    if audience is Audience.RU:
        if user_lang and user_lang.lower().startswith("en"):
            return "en"
        return "ru"

    if not user_lang:
        return "en"

    normalized = user_lang.lower()
    prefixes = (
        ("hi", "hi"),
        ("ar", "ar"),
        ("es", "es"),
        ("pt", "pt"),
        ("tr", "tr"),
        ("fr", "fr"),
        ("de", "de"),
        ("id", "id"),
        ("in", "id"),
        ("vi", "vi"),
        ("en", "en"),
    )
    for prefix, locale in prefixes:
        if normalized.startswith(prefix):
            return locale
    return "en"
