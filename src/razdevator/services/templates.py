from __future__ import annotations

from razdevator.core.models import TemplateItem


CREBOTS_VIDEO_PRESETS = [
    "anal",
    "back_doggystyle",
    "blowjob",
    "blowjob_69",
    "blowjob_reverse",
    "breast_massage",
    "breast_massage_nude",
    "butt_smothering",
    "cock_worship",
    "cum_in_mouth",
    "dildo_masturbation",
    "double_blowjob",
    "double_penetration",
    "ejaculation",
    "facefuck",
    "facefuck_pov",
    "facial_cumshot",
    "footjob",
    "front_doggystyle",
    "fuck_machine",
    "full_nelson",
    "handjob",
    "masturbation",
    "missionary_pov",
    "missionary_sideview",
    "nipple_play",
    "nude_posing",
    "orgasm",
    "pronebone",
    "pussy_closeup",
    "reverse_cowgirl",
    "shoejob",
    "spitroast",
    "squatting_cowgirl",
    "throatpie",
    "tiktok_trend",
    "titjob",
    "titty_flash",
    "triple_dicked",
    "twerk",
    "undress",
]

CREBOTS_AUDIO_VIDEO_PRESETS = [
    "blowjob_pov",
    "cumshot",
    "front_doggystyle",
    "missionary_pov",
    "squatting_cowgirl",
    "undress",
]

CREBOTS_AUDIO_VIDEO_PRICES = {
    "5s": 30,
    "10s": 50,
}

RU_TITLES = {
    "anal": "Анал",
    "back_doggystyle": "Догги сзади",
    "blowjob": "Минет",
    "blowjob_69": "Минет 69",
    "blowjob_reverse": "Обратный минет",
    "breast_massage": "Массаж груди",
    "breast_massage_nude": "Массаж груди nude",
    "butt_smothering": "Лицо в ягодицах",
    "cock_worship": "Культ члена",
    "cum_in_mouth": "Финиш в рот",
    "dildo_masturbation": "Мастурбация дилдо",
    "double_blowjob": "Двойной минет",
    "double_penetration": "Двойное проникновение",
    "ejaculation": "Эякуляция",
    "facefuck": "Фейсфак",
    "facefuck_pov": "Фейсфак POV",
    "facial_cumshot": "Камшот на лицо",
    "footjob": "Футджоб",
    "front_doggystyle": "Догги спереди",
    "fuck_machine": "Секс-машина",
    "full_nelson": "Фулл-нельсон",
    "handjob": "Хендджоб",
    "masturbation": "Мастурбация",
    "missionary_pov": "Миссионерская POV",
    "missionary_sideview": "Миссионерская сбоку",
    "nipple_play": "Игры с сосками",
    "nude_posing": "Ню-позинг",
    "orgasm": "Оргазм",
    "pronebone": "Лежа на животе",
    "pussy_closeup": "Крупный план",
    "reverse_cowgirl": "Обратная наездница",
    "shoejob": "Шуджоб",
    "spitroast": "С двух сторон",
    "squatting_cowgirl": "Наездница на корточках",
    "throatpie": "Финиш в горло",
    "tiktok_trend": "TikTok trend",
    "titjob": "Титджоб",
    "titty_flash": "Показ груди",
    "triple_dicked": "Тройное проникновение",
    "twerk": "Тверк",
    "undress": "Раздевание",
    "blowjob_pov": "Минет POV",
    "cumshot": "Камшот",
}

EN_TITLES = {
    "anal": "Anal",
    "back_doggystyle": "Back Doggy",
    "blowjob": "Blowjob",
    "blowjob_69": "69 Blowjob",
    "blowjob_reverse": "Reverse Blowjob",
    "breast_massage": "Breast Massage",
    "breast_massage_nude": "Nude Breast Massage",
    "butt_smothering": "Butt Smothering",
    "cock_worship": "Cock Worship",
    "cum_in_mouth": "Cum In Mouth",
    "dildo_masturbation": "Dildo Play",
    "double_blowjob": "Double Blowjob",
    "double_penetration": "Double Penetration",
    "ejaculation": "Ejaculation",
    "facefuck": "Facefuck",
    "facefuck_pov": "Facefuck POV",
    "facial_cumshot": "Facial Cumshot",
    "footjob": "Footjob",
    "front_doggystyle": "Front Doggy",
    "fuck_machine": "Fuck Machine",
    "full_nelson": "Full Nelson",
    "handjob": "Handjob",
    "masturbation": "Masturbation",
    "missionary_pov": "Missionary POV",
    "missionary_sideview": "Missionary Side",
    "nipple_play": "Nipple Play",
    "nude_posing": "Nude Posing",
    "orgasm": "Orgasm",
    "pronebone": "Pronebone",
    "pussy_closeup": "Close Up",
    "reverse_cowgirl": "Reverse Cowgirl",
    "shoejob": "Shoejob",
    "spitroast": "Spitroast",
    "squatting_cowgirl": "Squatting Cowgirl",
    "throatpie": "Throatpie",
    "tiktok_trend": "TikTok Trend",
    "titjob": "Titjob",
    "titty_flash": "Titty Flash",
    "triple_dicked": "Triple Action",
    "twerk": "Twerk",
    "undress": "Undress",
    "blowjob_pov": "Blowjob POV",
    "cumshot": "Cumshot",
}


def _title_ru(slug: str) -> str:
    return RU_TITLES.get(slug, slug.replace("_", " ").title())


def _title_en(slug: str) -> str:
    return EN_TITLES.get(slug, slug.replace("_", " ").title())


class TemplateCatalog:
    def __init__(self) -> None:
        self._silent_items = [
            TemplateItem(slug, _title_ru(slug), _title_en(slug), 20)
            for slug in CREBOTS_VIDEO_PRESETS
        ]
        self._audio_items = {
            length: [
                TemplateItem(
                    slug,
                    _title_ru(slug),
                    _title_en(slug),
                    CREBOTS_AUDIO_VIDEO_PRICES[length],
                )
                for slug in CREBOTS_AUDIO_VIDEO_PRESETS
            ]
            for length in CREBOTS_AUDIO_VIDEO_PRICES
        }

    def all(self) -> list[TemplateItem]:
        return list(self._silent_items)

    def get(self, slug: str) -> TemplateItem | None:
        return next((item for item in self._silent_items if item.slug == slug), None)

    def audio_all(self, video_length: str) -> list[TemplateItem]:
        return list(self._audio_items.get(video_length, []))

    def get_audio(self, slug: str, video_length: str) -> TemplateItem | None:
        return next((item for item in self.audio_all(video_length) if item.slug == slug), None)

    def page(self, page: int, per_page: int = 8) -> tuple[list[TemplateItem], int]:
        items = self.all()
        pages = max(1, (len(items) + per_page - 1) // per_page)
        safe_page = max(0, min(page, pages - 1))
        start = safe_page * per_page
        end = start + per_page
        return items[start:end], pages

    def audio_page(self, video_length: str, page: int, per_page: int = 6) -> tuple[list[TemplateItem], int]:
        items = self.audio_all(video_length)
        pages = max(1, (len(items) + per_page - 1) // per_page)
        safe_page = max(0, min(page, pages - 1))
        start = safe_page * per_page
        end = start + per_page
        return items[start:end], pages
