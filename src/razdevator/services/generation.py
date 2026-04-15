from __future__ import annotations

import asyncio
import base64
from dataclasses import dataclass, field
from html import escape
import logging
from typing import Any

import aiohttp
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BufferedInputFile, Message

from razdevator.core.config import Settings
from razdevator.core.enums import GenerationFeature, GenerationStatus
from razdevator.core.models import BotInstance, EndUserProfile, GenerationJob, TemplateItem
from razdevator.db.repositories import GenerationRepository, UserRepository
from razdevator.services.i18n import I18n


logger = logging.getLogger(__name__)

CREBOTS_FINAL_SUCCESS = {"COMPLETED", "DOWNLOADED"}
CREBOTS_FINAL_FAILURE = {"FAILED", "UNKNOWN_TASK_STATUS"}
CREBOTS_POLL_INTERVAL = 8
CREBOTS_POLL_ATTEMPTS = 90
CREBOTS_VIDEO_QUALITY = "high"
CREBOTS_VIDEO_LENGTH = "10s"
CREBOTS_AUDIO_VIDEO_LENGTHS = {"5s", "10s", "15s", "20s"}
CREBOTS_PROGRESS_STEPS = (7, 15, 29, 44, 58, 71, 82, 90, 95)
PROGRESS_BAR_WIDTH = 12


class GenerationError(RuntimeError):
    pass


@dataclass(slots=True)
class CreBotsTask:
    task_id: str
    status: str
    output_url: str | None
    task_message: str | None


@dataclass(slots=True)
class ProgressMessageRef:
    chat_id: int
    message_id: int
    has_media: bool

    @classmethod
    def from_message(cls, message: Message) -> "ProgressMessageRef":
        return cls(
            chat_id=message.chat.id,
            message_id=message.message_id,
            has_media=bool(message.photo),
        )


@dataclass(slots=True)
class GenerationService:
    settings: Settings
    i18n: I18n | None = None
    users: UserRepository | None = None
    generations: GenerationRepository | None = None
    background_tasks: set[asyncio.Task[Any]] = field(default_factory=set, init=False)

    async def submit(
        self,
        *,
        bot_instance: BotInstance,
        profile: EndUserProfile,
        template: TemplateItem,
        job: GenerationJob,
        video_length: str | None = None,
    ) -> dict[str, str]:
        provider = self.settings.generation_provider.lower()
        if provider != "crebots":
            return {
                "provider": provider,
                "status": "queued",
                "message": (
                    f"Stub provider accepted job #{job.id} "
                    f"for bot {bot_instance.title} and user {profile.telegram_id}."
                ),
            }

        if not self.settings.crebots_configured:
            raise GenerationError(self._t(profile.language_code, "generation_submit_error"))
        if not job.source_file_id:
            raise GenerationError(self._t(profile.language_code, "generation_submit_error"))

        if job.feature is GenerationFeature.AUDIO_IMAGE_TO_VIDEO:
            task = await self._create_crebots_audio_generation(
                bot_instance,
                template,
                job.source_file_id,
                video_length=video_length or "5s",
            )
        else:
            task = await self._create_crebots_generation(bot_instance, template, job.source_file_id)
        return {
            "provider": "crebots",
            "status": task.status,
            "task_id": task.task_id,
        }

    def track(
        self,
        *,
        bot_instance: BotInstance,
        profile: EndUserProfile,
        template: TemplateItem,
        job: GenerationJob,
        task_id: str,
        initial_status: str = "NEW",
        progress_message: ProgressMessageRef | None = None,
    ) -> None:
        if self.settings.generation_provider.lower() != "crebots" or not task_id:
            return
        background = asyncio.create_task(
            self._poll_crebots_task(
                bot_instance=bot_instance,
                profile=profile,
                template=template,
                job=job,
                task=CreBotsTask(
                    task_id=task_id,
                    status=initial_status or "NEW",
                    output_url=None,
                    task_message=None,
                ),
                progress_message=progress_message,
            )
        )
        self.background_tasks.add(background)
        background.add_done_callback(self.background_tasks.discard)

    async def _create_crebots_generation(
        self,
        bot_instance: BotInstance,
        template: TemplateItem,
        source_file_id: str,
    ) -> CreBotsTask:
        image_bytes = await self._download_telegram_file(bot_instance.token, source_file_id)
        payload = {
            "preset_name": template.slug,
            "input_image_base64": base64.b64encode(image_bytes).decode("ascii"),
            "quality": CREBOTS_VIDEO_QUALITY,
            "video_length": CREBOTS_VIDEO_LENGTH,
        }
        logger.info(
            "Submitting CreBots silent generation preset=%s quality=%s video_length=%s bot=%s",
            template.slug,
            CREBOTS_VIDEO_QUALITY,
            CREBOTS_VIDEO_LENGTH,
            bot_instance.username,
        )
        data = await self._crebots_request("POST", "/create_video", json=payload)
        task = self._parse_crebots_task(data)
        if not task.task_id:
            raise GenerationError("CreBots did not return a task id.")
        logger.info(
            "CreBots accepted task task_id=%s status=%s preset=%s",
            task.task_id,
            task.status,
            template.slug,
        )
        return task

    async def _create_crebots_audio_generation(
        self,
        bot_instance: BotInstance,
        template: TemplateItem,
        source_file_id: str,
        *,
        video_length: str,
    ) -> CreBotsTask:
        normalized_length = video_length if video_length in CREBOTS_AUDIO_VIDEO_LENGTHS else "5s"
        image_bytes = await self._download_telegram_file(bot_instance.token, source_file_id)
        payload = {
            "preset_name": template.slug,
            "input_image_base64": base64.b64encode(image_bytes).decode("ascii"),
            "quality": CREBOTS_VIDEO_QUALITY,
            "video_length": normalized_length,
        }
        logger.info(
            "Submitting CreBots audio generation preset=%s quality=%s video_length=%s bot=%s",
            template.slug,
            CREBOTS_VIDEO_QUALITY,
            normalized_length,
            bot_instance.username,
        )
        data = await self._crebots_request("POST", "/create_audio_video", json=payload)
        task = self._parse_crebots_task(data)
        if not task.task_id:
            raise GenerationError("CreBots did not return a task id.")
        logger.info(
            "CreBots accepted audio task task_id=%s status=%s preset=%s",
            task.task_id,
            task.status,
            template.slug,
        )
        return task

    async def _poll_crebots_task(
        self,
        *,
        bot_instance: BotInstance,
        profile: EndUserProfile,
        template: TemplateItem,
        job: GenerationJob,
        task: CreBotsTask,
        progress_message: ProgressMessageRef | None = None,
    ) -> None:
        try:
            last_progress = -1
            if progress_message is not None:
                last_progress = self._progress_percent(task.status, 0)
                await self._edit_progress_message(
                    bot_instance=bot_instance,
                    progress_message=progress_message,
                    text=self._loader_active_text(
                        locale=profile.language_code,
                        template=template,
                        task_id=task.task_id,
                        progress=last_progress,
                    ),
                )

            for attempt in range(CREBOTS_POLL_ATTEMPTS):
                current = await self._get_crebots_task(task.task_id)
                if current.status in CREBOTS_FINAL_SUCCESS:
                    if not current.output_url:
                        raise GenerationError("CreBots completed the task without output_url.")
                    file_id = await self._deliver_video(
                        bot_instance=bot_instance,
                        profile=profile,
                        template=template,
                        output_url=current.output_url,
                    )
                    if self.generations is not None:
                        await self.generations.update_status(
                            job.id,
                            GenerationStatus.DONE,
                            result_file_id=file_id,
                    )
                    if self.users is not None:
                        await self.users.mark_generation_result(profile.id, True)
                    if progress_message is not None:
                        await self._edit_progress_message(
                            bot_instance=bot_instance,
                            progress_message=progress_message,
                            text=self._loader_ready_text(
                                locale=profile.language_code,
                                template=template,
                                task_id=task.task_id,
                            ),
                        )
                    return

                if current.status in CREBOTS_FINAL_FAILURE:
                    raise GenerationError(current.task_message or "CreBots failed to generate the video.")

                progress = self._progress_percent(current.status, attempt + 1)
                if progress_message is not None and progress > last_progress:
                    last_progress = progress
                    await self._edit_progress_message(
                        bot_instance=bot_instance,
                        progress_message=progress_message,
                        text=self._loader_active_text(
                            locale=profile.language_code,
                            template=template,
                            task_id=task.task_id,
                            progress=progress,
                        ),
                    )

                await asyncio.sleep(CREBOTS_POLL_INTERVAL)

            raise GenerationError("CreBots generation timed out.")
        except Exception as exc:
            logger.exception("CreBots generation failed for job %s", job.id)
            if self.generations is not None:
                await self.generations.update_status(
                    job.id,
                    GenerationStatus.FAILED,
                    error_text=str(exc),
                )
            if self.users is not None:
                await self.users.add_balance(profile.id, template.credits)
                await self.users.mark_generation_result(profile.id, False)
            if progress_message is not None and task.task_id:
                await self._edit_progress_message(
                    bot_instance=bot_instance,
                    progress_message=progress_message,
                    text=self._loader_failed_text(
                        locale=profile.language_code,
                        template=template,
                        task_id=task.task_id,
                        reason=str(exc),
                    ),
                )
            else:
                await self._send_failure_message(bot_instance, profile, str(exc))

    async def _get_crebots_task(self, task_id: str) -> CreBotsTask:
        data = await self._crebots_request("GET", f"/task/{task_id}")
        return self._parse_crebots_task(data)

    async def _crebots_request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        timeout = aiohttp.ClientTimeout(total=90)
        headers = {
            "accept": "application/json",
            "API-KEY": self.settings.crebots_api_key,
        }
        if json is not None:
            headers["content-type"] = "application/json"
        url = f"{self.settings.crebots_base_url}{path}"
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.request(method, url, headers=headers, json=json) as response:
                raw_text = await response.text()
                if response.status >= 400:
                    raise GenerationError(
                        f"CreBots API error {response.status}: {raw_text[:300]}"
                    )
                try:
                    data = await response.json()
                except aiohttp.ContentTypeError as exc:
                    raise GenerationError(
                        f"CreBots returned non-JSON response: {raw_text[:300]}"
                    ) from exc
        if not isinstance(data, dict):
            raise GenerationError("CreBots returned an unexpected payload.")
        return data

    def _parse_crebots_task(self, data: dict[str, Any]) -> CreBotsTask:
        task_id = str(data.get("id") or "").strip()
        status = str(data.get("status") or "NEW").strip().upper()
        output_url = data.get("output_url")
        task_message = data.get("task_message")
        return CreBotsTask(
            task_id=task_id,
            status=status,
            output_url=output_url if isinstance(output_url, str) and output_url else None,
            task_message=task_message if isinstance(task_message, str) and task_message else None,
        )

    async def _download_telegram_file(self, bot_token: str, file_id: str) -> bytes:
        bot = Bot(
            token=bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        try:
            file = await bot.get_file(file_id)
        finally:
            await bot.session.close()
        if not file.file_path:
            raise GenerationError("Telegram did not return file_path for the uploaded image.")
        telegram_file_url = f"https://api.telegram.org/file/bot{bot_token}/{file.file_path}"
        return await self._download_binary(telegram_file_url)

    async def _download_binary(self, url: str) -> bytes:
        timeout = aiohttp.ClientTimeout(total=180)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status >= 400:
                    raise GenerationError(f"Could not download file from {url}.")
                return await response.read()

    async def _deliver_video(
        self,
        *,
        bot_instance: BotInstance,
        profile: EndUserProfile,
        template: TemplateItem,
        output_url: str,
    ) -> str | None:
        video_bytes = await self._download_binary(output_url)
        filename = f"generation-{profile.telegram_id}-{template.slug}.mp4"
        bot = Bot(
            token=bot_instance.token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        try:
            message = await bot.send_video(
                profile.telegram_id,
                BufferedInputFile(video_bytes, filename=filename),
                caption=self._t(
                    profile.language_code,
                    "generation_ready",
                    template=template.title(profile.language_code),
                ),
            )
        finally:
            await bot.session.close()
        if message.video is not None:
            return message.video.file_id
        return None

    async def _send_failure_message(
        self,
        bot_instance: BotInstance,
        profile: EndUserProfile,
        reason: str,
    ) -> None:
        bot = Bot(
            token=bot_instance.token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        try:
            await bot.send_message(
                profile.telegram_id,
                self._t(
                    profile.language_code,
                    "generation_failed",
                    reason=reason,
                ),
            )
        finally:
            await bot.session.close()

    async def _edit_progress_message(
        self,
        *,
        bot_instance: BotInstance,
        progress_message: ProgressMessageRef,
        text: str,
    ) -> None:
        bot = Bot(
            token=bot_instance.token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        try:
            if progress_message.has_media:
                await bot.edit_message_caption(
                    chat_id=progress_message.chat_id,
                    message_id=progress_message.message_id,
                    caption=text,
                )
            else:
                await bot.edit_message_text(
                    chat_id=progress_message.chat_id,
                    message_id=progress_message.message_id,
                    text=text,
                )
        except TelegramBadRequest as exc:
            if "message is not modified" in str(exc).lower():
                return
            logger.warning(
                "Could not update generation loader chat=%s message=%s: %s",
                progress_message.chat_id,
                progress_message.message_id,
                exc,
            )
        finally:
            await bot.session.close()

    def _loader_active_text(
        self,
        *,
        locale: str,
        template: TemplateItem,
        task_id: str,
        progress: int,
    ) -> str:
        return self._t(
            locale,
            "generation_loader_active",
            template=escape(template.title(locale)),
            task_id=escape(task_id),
            progress=progress,
            bar=self._progress_bar(progress),
        )

    def _loader_ready_text(
        self,
        *,
        locale: str,
        template: TemplateItem,
        task_id: str,
    ) -> str:
        return self._t(
            locale,
            "generation_loader_ready",
            template=escape(template.title(locale)),
            task_id=escape(task_id),
            bar=self._progress_bar(100),
        )

    def _loader_failed_text(
        self,
        *,
        locale: str,
        template: TemplateItem,
        task_id: str,
        reason: str,
    ) -> str:
        return self._t(
            locale,
            "generation_loader_failed",
            template=escape(template.title(locale)),
            task_id=escape(task_id),
            reason=escape(reason),
        )

    def _progress_percent(self, status: str, step: int) -> int:
        progress = CREBOTS_PROGRESS_STEPS[min(step, len(CREBOTS_PROGRESS_STEPS) - 1)]
        if status == "NEW":
            return min(progress, 25)
        if status == "PROCESSING":
            return progress
        return min(progress, 12)

    def _progress_bar(self, progress: int) -> str:
        filled = round(PROGRESS_BAR_WIDTH * max(0, min(progress, 100)) / 100)
        return "[" + ("█" * filled) + ("░" * (PROGRESS_BAR_WIDTH - filled)) + "]"

    def _t(self, locale: str, key: str, **kwargs: object) -> str:
        if self.i18n is None:
            return key
        return self.i18n.t(locale, key, **kwargs)
