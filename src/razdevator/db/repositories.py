from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
import json
from typing import Any

from aiogram.types import User

from razdevator.core.config import Settings
from razdevator.core.enums import (
    Audience,
    BotKind,
    BroadcastScope,
    GenerationFeature,
    GenerationStatus,
    PaymentProvider,
    PaymentStatus,
    StaffRole,
    TransactionDirection,
)
from razdevator.core.models import (
    BotInstance,
    BotStats,
    EndUserProfile,
    GenerationJob,
    OwnerStats,
    PaymentRecord,
    StaffUser,
)
from razdevator.db.database import Database
from razdevator.utils.referral import generate_referral_tag


def _ts(value: str) -> datetime:
    return datetime.fromisoformat(value)


class StaffRepository:
    def __init__(self, db: Database, settings: Settings) -> None:
        self.db = db
        self.settings = settings

    async def ensure_staff(self, tg_user: User) -> StaffUser:
        role = (
            StaffRole.OWNER
            if tg_user.id in self.settings.owner_ids
            else StaffRole.ADMIN
        )
        row = await self.db.fetchone(
            """
            SELECT * FROM staff_users
            WHERE telegram_id = ?
            """,
            [tg_user.id],
        )
        if row is None:
            referral_tag = generate_referral_tag()
            await self.db.execute(
                """
                INSERT INTO staff_users (
                    telegram_id, username, full_name, role, referral_tag, commission_rate
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    tg_user.id,
                    tg_user.username,
                    tg_user.full_name,
                    role.value,
                    referral_tag,
                    self.settings.default_admin_rate,
                ],
            )
            row = await self.db.fetchone(
                "SELECT * FROM staff_users WHERE telegram_id = ?",
                [tg_user.id],
            )
        elif row["role"] != role.value:
            await self.db.execute(
                """
                UPDATE staff_users
                SET role = ?, username = ?, full_name = ?, updated_at = CURRENT_TIMESTAMP
                WHERE telegram_id = ?
                """,
                [role.value, tg_user.username, tg_user.full_name, tg_user.id],
            )
            row = await self.db.fetchone(
                "SELECT * FROM staff_users WHERE telegram_id = ?",
                [tg_user.id],
            )
        else:
            await self.db.execute(
                """
                UPDATE staff_users
                SET username = ?, full_name = ?, updated_at = CURRENT_TIMESTAMP
                WHERE telegram_id = ?
                """,
                [tg_user.username, tg_user.full_name, tg_user.id],
            )
            row = await self.db.fetchone(
                "SELECT * FROM staff_users WHERE telegram_id = ?",
                [tg_user.id],
            )
        return self._map(row)

    async def get_by_telegram_id(self, telegram_id: int) -> StaffUser | None:
        row = await self.db.fetchone(
            "SELECT * FROM staff_users WHERE telegram_id = ?",
            [telegram_id],
        )
        return self._map(row) if row else None

    async def get_by_id(self, staff_id: int) -> StaffUser | None:
        row = await self.db.fetchone(
            "SELECT * FROM staff_users WHERE id = ?",
            [staff_id],
        )
        return self._map(row) if row else None

    async def get_by_referral_tag(self, tag: str) -> StaffUser | None:
        row = await self.db.fetchone(
            "SELECT * FROM staff_users WHERE referral_tag = ?",
            [tag],
        )
        return self._map(row) if row else None

    async def list_admins(self) -> list[StaffUser]:
        rows = await self.db.fetchall(
            """
            SELECT * FROM staff_users
            ORDER BY
                CASE role WHEN 'owner' THEN 0 ELSE 1 END,
                created_at ASC
            """
        )
        return [self._map(row) for row in rows]

    async def update_rate(self, staff_id: int, rate: int) -> None:
        await self.db.execute(
            """
            UPDATE staff_users
            SET commission_rate = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            [rate, staff_id],
        )

    def _map(self, row: Any) -> StaffUser:
        return StaffUser(
            id=row["id"],
            telegram_id=row["telegram_id"],
            username=row["username"],
            full_name=row["full_name"],
            role=StaffRole(row["role"]),
            referral_tag=row["referral_tag"],
            commission_rate=row["commission_rate"],
            created_at=_ts(row["created_at"]),
        )


class BotRepository:
    def __init__(self, db: Database, settings: Settings) -> None:
        self.db = db
        self.settings = settings

    async def create_bot_instance(
        self,
        *,
        token: str,
        bot_id: int,
        username: str | None,
        title: str,
        kind: BotKind,
        audience: Audience,
        owner_staff_id: int | None,
        hero_media: str | None = None,
    ) -> BotInstance:
        provider = (
            self.settings.default_ru_payment_provider
            if audience is Audience.RU
            else self.settings.default_en_payment_provider
        )
        await self.db.execute(
            """
            INSERT INTO bot_instances (
                bot_id, token, username, title, kind, audience, owner_staff_id, hero_media, payment_provider
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                bot_id,
                token,
                username,
                title,
                kind.value,
                audience.value,
                owner_staff_id,
                hero_media,
                provider.value,
            ],
        )
        row = await self.db.fetchone(
            """
            SELECT * FROM bot_instances
            WHERE token = ?
            """,
            [token],
        )
        return self._map(row)

    async def list_personal_bots(self, owner_staff_id: int) -> list[BotInstance]:
        rows = await self.db.fetchall(
            """
            SELECT * FROM bot_instances
            WHERE owner_staff_id = ? AND is_archived = 0
            ORDER BY created_at DESC
            """,
            [owner_staff_id],
        )
        return [self._map(row) for row in rows]

    async def list_active_client_bots(self) -> list[BotInstance]:
        rows = await self.db.fetchall(
            """
            SELECT * FROM bot_instances
            WHERE is_active = 1 AND is_archived = 0
            ORDER BY created_at ASC
            """
        )
        return [self._map(row) for row in rows]

    async def get_by_id(self, bot_instance_id: int) -> BotInstance | None:
        row = await self.db.fetchone(
            "SELECT * FROM bot_instances WHERE id = ?",
            [bot_instance_id],
        )
        return self._map(row) if row else None

    async def get_by_token(self, token: str) -> BotInstance | None:
        row = await self.db.fetchone(
            "SELECT * FROM bot_instances WHERE token = ?",
            [token],
        )
        return self._map(row) if row else None

    async def get_by_bot_id(self, bot_id: int) -> BotInstance | None:
        row = await self.db.fetchone(
            "SELECT * FROM bot_instances WHERE bot_id = ?",
            [bot_id],
        )
        return self._map(row) if row else None

    async def toggle_active(self, bot_instance_id: int) -> BotInstance | None:
        await self.db.execute(
            """
            UPDATE bot_instances
            SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            [bot_instance_id],
        )
        return await self.get_by_id(bot_instance_id)

    async def archive(self, bot_instance_id: int) -> None:
        await self.db.execute(
            """
            UPDATE bot_instances
            SET is_archived = 1, is_active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            [bot_instance_id],
        )

    async def update_welcome_text(self, bot_instance_id: int, text: str) -> None:
        await self.db.execute(
            """
            UPDATE bot_instances
            SET welcome_text = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            [text, bot_instance_id],
        )

    async def update_farewell_text(self, bot_instance_id: int, text: str) -> None:
        await self.db.execute(
            """
            UPDATE bot_instances
            SET farewell_text = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            [text, bot_instance_id],
        )

    async def update_hero_media(self, bot_instance_id: int, media: str) -> None:
        await self.db.execute(
            """
            UPDATE bot_instances
            SET hero_media = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            [media, bot_instance_id],
        )

    def _map(self, row: Any) -> BotInstance:
        return BotInstance(
            id=row["id"],
            bot_id=row["bot_id"],
            token=row["token"],
            username=row["username"],
            title=row["title"],
            kind=BotKind(row["kind"]),
            audience=Audience(row["audience"]),
            owner_staff_id=row["owner_staff_id"],
            is_active=bool(row["is_active"]),
            is_archived=bool(row["is_archived"]),
            welcome_text=row["welcome_text"],
            farewell_text=row["farewell_text"],
            hero_media=row["hero_media"],
            payment_provider=PaymentProvider(row["payment_provider"]),
            created_at=_ts(row["created_at"]),
        )


class UserRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def upsert_user(
        self,
        *,
        bot_instance_id: int,
        telegram_id: int,
        username: str | None,
        full_name: str,
        language_code: str,
        referred_by_staff_id: int | None = None,
    ) -> EndUserProfile:
        await self.db.execute(
            """
            INSERT INTO end_users (
                bot_instance_id, telegram_id, username, full_name, language_code, referred_by_staff_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(bot_instance_id, telegram_id) DO UPDATE SET
                username = excluded.username,
                full_name = excluded.full_name,
                language_code = COALESCE(end_users.language_code, excluded.language_code),
                referred_by_staff_id = COALESCE(end_users.referred_by_staff_id, excluded.referred_by_staff_id),
                updated_at = CURRENT_TIMESTAMP
            """,
            [
                bot_instance_id,
                telegram_id,
                username,
                full_name,
                language_code,
                referred_by_staff_id,
            ],
        )
        row = await self.db.fetchone(
            """
            SELECT * FROM end_users
            WHERE bot_instance_id = ? AND telegram_id = ?
            """,
            [bot_instance_id, telegram_id],
        )
        return self._map(row)

    async def get_profile(self, bot_instance_id: int, telegram_id: int) -> EndUserProfile | None:
        row = await self.db.fetchone(
            """
            SELECT * FROM end_users
            WHERE bot_instance_id = ? AND telegram_id = ?
            """,
            [bot_instance_id, telegram_id],
        )
        return self._map(row) if row else None

    async def set_language(
        self,
        bot_instance_id: int,
        telegram_id: int,
        language_code: str,
    ) -> None:
        await self.db.execute(
            """
            UPDATE end_users
            SET language_code = ?, updated_at = CURRENT_TIMESTAMP
            WHERE bot_instance_id = ? AND telegram_id = ?
            """,
            [language_code, bot_instance_id, telegram_id],
        )

    async def add_balance(
        self,
        profile_id: int,
        amount: int,
    ) -> None:
        await self.db.execute(
            """
            UPDATE end_users
            SET balance = balance + ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            [amount, profile_id],
        )

    async def consume_balance(self, profile_id: int, amount: int) -> None:
        await self.db.execute(
            """
            UPDATE end_users
            SET balance = MAX(balance - ?, 0), updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            [amount, profile_id],
        )

    async def mark_generation_result(self, profile_id: int, success: bool) -> None:
        field = "successful_generations" if success else "failed_generations"
        await self.db.execute(
            f"""
            UPDATE end_users
            SET {field} = {field} + 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            [profile_id],
        )

    async def list_for_bot(self, bot_instance_id: int) -> list[EndUserProfile]:
        rows = await self.db.fetchall(
            """
            SELECT * FROM end_users
            WHERE bot_instance_id = ?
            ORDER BY id ASC
            """,
            [bot_instance_id],
        )
        return [self._map(row) for row in rows]

    async def list_all(self) -> list[EndUserProfile]:
        rows = await self.db.fetchall(
            """
            SELECT * FROM end_users
            ORDER BY id ASC
            """
        )
        return [self._map(row) for row in rows]

    def _map(self, row: Any) -> EndUserProfile:
        return EndUserProfile(
            id=row["id"],
            bot_instance_id=row["bot_instance_id"],
            telegram_id=row["telegram_id"],
            username=row["username"],
            full_name=row["full_name"],
            language_code=row["language_code"],
            balance=row["balance"],
            successful_generations=row["successful_generations"],
            failed_generations=row["failed_generations"],
            referred_by_staff_id=row["referred_by_staff_id"],
            created_at=_ts(row["created_at"]),
        )


class PaymentRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def create_payment(
        self,
        *,
        bot_instance_id: int,
        end_user_id: int,
        amount_cents: int,
        currency: str,
        provider: PaymentProvider,
        direction: TransactionDirection,
        status: PaymentStatus,
        external_id: str | None = None,
        meta_json: str | None = None,
    ) -> int:
        cursor = await self.db.execute(
            """
            INSERT INTO payments (
                bot_instance_id, end_user_id, amount_cents, currency, provider, direction, status, external_id, meta_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                bot_instance_id,
                end_user_id,
                amount_cents,
                currency,
                provider.value,
                direction.value,
                status.value,
                external_id,
                meta_json,
            ],
        )
        return int(cursor.lastrowid)

    async def get_payment_by_external_id(self, external_id: str) -> PaymentRecord | None:
        row = await self.db.fetchone(
            """
            SELECT * FROM payments
            WHERE external_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            [external_id],
        )
        return self._map(row) if row else None

    async def update_status_by_external_id(
        self,
        external_id: str,
        status: PaymentStatus,
    ) -> None:
        await self.db.execute(
            """
            UPDATE payments
            SET status = ?
            WHERE external_id = ?
            """,
            [status.value, external_id],
        )

    def _map(self, row: Any) -> PaymentRecord:
        return PaymentRecord(
            id=row["id"],
            bot_instance_id=row["bot_instance_id"],
            end_user_id=row["end_user_id"],
            amount_cents=row["amount_cents"],
            currency=row["currency"],
            provider=PaymentProvider(row["provider"]),
            direction=TransactionDirection(row["direction"]),
            status=PaymentStatus(row["status"]),
            external_id=row["external_id"],
            meta_json=row["meta_json"],
            created_at=_ts(row["created_at"]),
        )

    async def create_payout(
        self,
        *,
        staff_user_id: int,
        amount_cents: int,
        currency: str,
        note: str | None = None,
    ) -> None:
        await self.db.execute(
            """
            INSERT INTO payouts (staff_user_id, amount_cents, currency, note)
            VALUES (?, ?, ?, ?)
            """,
            [staff_user_id, amount_cents, currency, note],
        )


class GenerationRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def create_job(
        self,
        *,
        bot_instance_id: int,
        end_user_id: int,
        feature: GenerationFeature = GenerationFeature.IMAGE_TO_VIDEO,
        template_slug: str,
        cost_credits: int,
        source_file_id: str | None = None,
    ) -> GenerationJob:
        await self.db.execute(
            """
            INSERT INTO generation_jobs (
                bot_instance_id, end_user_id, feature, template_slug, status, source_file_id, cost_credits
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                bot_instance_id,
                end_user_id,
                feature.value,
                template_slug,
                GenerationStatus.QUEUED.value,
                source_file_id,
                cost_credits,
            ],
        )
        row = await self.db.fetchone(
            """
            SELECT * FROM generation_jobs
            WHERE rowid = last_insert_rowid()
            """
        )
        return self._map(row)

    async def update_status(
        self,
        job_id: int,
        status: GenerationStatus,
        *,
        result_file_id: str | None = None,
        error_text: str | None = None,
    ) -> None:
        await self.db.execute(
            """
            UPDATE generation_jobs
            SET status = ?, result_file_id = COALESCE(?, result_file_id),
                error_text = COALESCE(?, error_text),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            [status.value, result_file_id, error_text, job_id],
        )

    def _map(self, row: Any) -> GenerationJob:
        return GenerationJob(
            id=row["id"],
            bot_instance_id=row["bot_instance_id"],
            end_user_id=row["end_user_id"],
            feature=GenerationFeature(row["feature"]),
            template_slug=row["template_slug"],
            status=GenerationStatus(row["status"]),
            cost_credits=row["cost_credits"],
            source_file_id=row["source_file_id"],
            result_file_id=row["result_file_id"],
            error_text=row["error_text"],
            created_at=_ts(row["created_at"]),
        )


class SettingsRepository:
    def __init__(self, db: Database, settings: Settings) -> None:
        self.db = db
        self.settings = settings

    async def ensure_defaults(self) -> None:
        if self.settings.main_bot_link:
            await self.set("main_bot_link", self.settings.main_bot_link)

    async def get(self, key: str, default: str = "") -> str:
        value = await self.db.fetchval(
            "SELECT value FROM app_settings WHERE key = ?",
            [key],
            default,
        )
        return value

    async def set(self, key: str, value: str) -> None:
        await self.db.execute(
            """
            INSERT INTO app_settings (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            [key, value],
        )


class StatsRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    async def get_bot_stats(self, bot_instance_id: int) -> BotStats:
        return BotStats(
            total_users=await self._count(
                "SELECT COUNT(*) FROM end_users WHERE bot_instance_id = ?",
                [bot_instance_id],
            ),
            month_users=await self._count(
                """
                SELECT COUNT(*) FROM end_users
                WHERE bot_instance_id = ? AND created_at >= datetime('now', '-30 days')
                """,
                [bot_instance_id],
            ),
            week_users=await self._count(
                """
                SELECT COUNT(*) FROM end_users
                WHERE bot_instance_id = ? AND created_at >= datetime('now', '-7 days')
                """,
                [bot_instance_id],
            ),
            today_users=await self._count(
                """
                SELECT COUNT(*) FROM end_users
                WHERE bot_instance_id = ? AND created_at >= datetime('now', 'start of day')
                """,
                [bot_instance_id],
            ),
            paid_payments=await self._count(
                """
                SELECT COUNT(*) FROM payments
                WHERE bot_instance_id = ? AND status = 'paid'
                """,
                [bot_instance_id],
            ),
            total_payments=await self._count(
                "SELECT COUNT(*) FROM payments WHERE bot_instance_id = ?",
                [bot_instance_id],
            ),
            month_paid_payments=await self._count(
                """
                SELECT COUNT(*) FROM payments
                WHERE bot_instance_id = ? AND status = 'paid'
                  AND created_at >= datetime('now', '-30 days')
                """,
                [bot_instance_id],
            ),
            month_total_payments=await self._count(
                """
                SELECT COUNT(*) FROM payments
                WHERE bot_instance_id = ? AND created_at >= datetime('now', '-30 days')
                """,
                [bot_instance_id],
            ),
            week_paid_payments=await self._count(
                """
                SELECT COUNT(*) FROM payments
                WHERE bot_instance_id = ? AND status = 'paid'
                  AND created_at >= datetime('now', '-7 days')
                """,
                [bot_instance_id],
            ),
            week_total_payments=await self._count(
                """
                SELECT COUNT(*) FROM payments
                WHERE bot_instance_id = ? AND created_at >= datetime('now', '-7 days')
                """,
                [bot_instance_id],
            ),
            today_paid_payments=await self._count(
                """
                SELECT COUNT(*) FROM payments
                WHERE bot_instance_id = ? AND status = 'paid'
                  AND created_at >= datetime('now', 'start of day')
                """,
                [bot_instance_id],
            ),
            today_total_payments=await self._count(
                """
                SELECT COUNT(*) FROM payments
                WHERE bot_instance_id = ? AND created_at >= datetime('now', 'start of day')
                """,
                [bot_instance_id],
            ),
            earned_cents=await self._count(
                """
                SELECT COALESCE(SUM(amount_cents), 0) FROM payments
                WHERE bot_instance_id = ? AND status = 'paid'
                  AND direction = 'deposit'
                """,
                [bot_instance_id],
            ),
            total_generations=await self._count(
                """
                SELECT COUNT(*) FROM generation_jobs
                WHERE bot_instance_id = ?
                """,
                [bot_instance_id],
            ),
        )

    async def get_staff_overview(self, staff_id: int) -> BotStats:
        owned_bots = """
            SELECT id FROM bot_instances
            WHERE owner_staff_id = ? AND is_archived = 0
        """
        user_scope = f"""
            (referred_by_staff_id = ? OR bot_instance_id IN ({owned_bots}))
        """
        payment_scope = f"""
            (u.referred_by_staff_id = ? OR p.bot_instance_id IN ({owned_bots}))
        """
        generation_scope = f"""
            (u.referred_by_staff_id = ? OR g.bot_instance_id IN ({owned_bots}))
        """
        scope_params = [staff_id, staff_id]
        return BotStats(
            total_users=await self._count(
                """
                SELECT COUNT(*) FROM end_users
                WHERE """ + user_scope,
                scope_params,
            ),
            month_users=await self._count(
                """
                SELECT COUNT(*) FROM end_users
                WHERE """ + user_scope + """
                AND created_at >= datetime('now', '-30 days')
                """,
                scope_params,
            ),
            week_users=await self._count(
                """
                SELECT COUNT(*) FROM end_users
                WHERE """ + user_scope + """
                AND created_at >= datetime('now', '-7 days')
                """,
                scope_params,
            ),
            today_users=await self._count(
                """
                SELECT COUNT(*) FROM end_users
                WHERE """ + user_scope + """
                AND created_at >= datetime('now', 'start of day')
                """,
                scope_params,
            ),
            paid_payments=await self._count(
                """
                SELECT COUNT(*) FROM payments p
                LEFT JOIN end_users u ON u.id = p.end_user_id
                WHERE """ + payment_scope + """
                AND p.status = 'paid'
                """,
                scope_params,
            ),
            total_payments=await self._count(
                """
                SELECT COUNT(*) FROM payments p
                LEFT JOIN end_users u ON u.id = p.end_user_id
                WHERE """ + payment_scope,
                scope_params,
            ),
            month_paid_payments=await self._count(
                """
                SELECT COUNT(*) FROM payments p
                LEFT JOIN end_users u ON u.id = p.end_user_id
                WHERE """ + payment_scope + """
                AND p.status = 'paid'
                AND p.created_at >= datetime('now', '-30 days')
                """,
                scope_params,
            ),
            month_total_payments=await self._count(
                """
                SELECT COUNT(*) FROM payments p
                LEFT JOIN end_users u ON u.id = p.end_user_id
                WHERE """ + payment_scope + """
                AND p.created_at >= datetime('now', '-30 days')
                """,
                scope_params,
            ),
            week_paid_payments=await self._count(
                """
                SELECT COUNT(*) FROM payments p
                LEFT JOIN end_users u ON u.id = p.end_user_id
                WHERE """ + payment_scope + """
                AND p.status = 'paid'
                AND p.created_at >= datetime('now', '-7 days')
                """,
                scope_params,
            ),
            week_total_payments=await self._count(
                """
                SELECT COUNT(*) FROM payments p
                LEFT JOIN end_users u ON u.id = p.end_user_id
                WHERE """ + payment_scope + """
                AND p.created_at >= datetime('now', '-7 days')
                """,
                scope_params,
            ),
            today_paid_payments=await self._count(
                """
                SELECT COUNT(*) FROM payments p
                LEFT JOIN end_users u ON u.id = p.end_user_id
                WHERE """ + payment_scope + """
                AND p.status = 'paid'
                AND p.created_at >= datetime('now', 'start of day')
                """,
                scope_params,
            ),
            today_total_payments=await self._count(
                """
                SELECT COUNT(*) FROM payments p
                LEFT JOIN end_users u ON u.id = p.end_user_id
                WHERE """ + payment_scope + """
                AND p.created_at >= datetime('now', 'start of day')
                """,
                scope_params,
            ),
            earned_cents=await self._count(
                """
                SELECT COALESCE(SUM(amount_cents), 0) FROM payments p
                LEFT JOIN end_users u ON u.id = p.end_user_id
                WHERE """ + payment_scope + """
                AND p.status = 'paid'
                AND p.direction = 'deposit'
                """,
                scope_params,
            ),
            total_generations=await self._count(
                """
                SELECT COUNT(*) FROM generation_jobs g
                LEFT JOIN end_users u ON u.id = g.end_user_id
                WHERE """ + generation_scope,
                scope_params,
            ),
        )

    async def get_owner_stats(self) -> OwnerStats:
        return OwnerStats(
            admins=await self._count(
                "SELECT COUNT(*) FROM staff_users WHERE role = 'admin'"
            ),
            client_bots=await self._count(
                "SELECT COUNT(*) FROM bot_instances WHERE is_archived = 0"
            ),
            users=await self._count("SELECT COUNT(*) FROM end_users"),
            generations=await self._count("SELECT COUNT(*) FROM generation_jobs"),
            revenue_cents=await self._count(
                """
                SELECT COALESCE(SUM(amount_cents), 0) FROM payments
                WHERE status = 'paid' AND direction = 'deposit'
                """
            ),
            payouts_cents=await self._count(
                "SELECT COALESCE(SUM(amount_cents), 0) FROM payouts"
            ),
        )

    async def _count(
        self,
        query: str,
        params: list[Any] | None = None,
    ) -> int:
        result = await self.db.fetchval(query, params or [], 0)
        return int(result or 0)
