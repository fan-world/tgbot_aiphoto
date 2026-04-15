from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aiogram.enums import ContentType
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Message,
)


@dataclass(slots=True)
class ScreenPayload:
    text: str
    keyboard: InlineKeyboardMarkup | None = None
    media_path: Path | None = None


class ScreenRenderer:
    async def show(
        self,
        target: Message | CallbackQuery,
        payload: ScreenPayload,
    ) -> Message:
        if isinstance(target, CallbackQuery):
            await target.answer()
            return await self._edit_or_answer(target.message, payload)
        return await self._send(target, payload)

    async def _send(self, message: Message, payload: ScreenPayload) -> Message:
        if payload.media_path:
            return await message.answer_photo(
                FSInputFile(payload.media_path),
                caption=payload.text,
                reply_markup=payload.keyboard,
            )
        return await message.answer(payload.text, reply_markup=payload.keyboard)

    async def _edit_or_answer(self, message: Message | None, payload: ScreenPayload) -> Message:
        if message is None:
            raise RuntimeError("Callback message is missing.")

        try:
            if payload.media_path:
                if message.content_type == ContentType.PHOTO:
                    await message.edit_media(
                        media=InputMediaPhoto(
                            media=FSInputFile(payload.media_path),
                            caption=payload.text,
                        ),
                        reply_markup=payload.keyboard,
                    )
                    return message
                return await message.answer_photo(
                    FSInputFile(payload.media_path),
                    caption=payload.text,
                    reply_markup=payload.keyboard,
                )

            if message.content_type == ContentType.PHOTO:
                await message.edit_caption(
                    caption=payload.text,
                    reply_markup=payload.keyboard,
                )
                return message

            await message.edit_text(payload.text, reply_markup=payload.keyboard)
            return message
        except TelegramBadRequest as exc:
            if "message is not modified" in str(exc).lower():
                return message
            raise
