from __future__ import annotations

from aiogram.types import CallbackQuery, Message

from app.constants import ROLE_ADMIN, ROLE_MODERATOR, ROLE_SUPERADMIN
from app.database.session import Database
from app.services.admins import get_admin


async def get_admin_role(db: Database, telegram_id: int) -> str | None:
    async with db.session() as session:
        admin = await get_admin(session, telegram_id)
        return admin.role if admin else None


async def require_admin(message_or_callback: Message | CallbackQuery, db: Database) -> str | None:
    user = message_or_callback.from_user
    if not user:
        return None
    return await get_admin_role(db, user.id)


def can_manage_content(role: str | None) -> bool:
    return role in {ROLE_SUPERADMIN, ROLE_ADMIN, ROLE_MODERATOR}


def can_manage_users(role: str | None) -> bool:
    return role in {ROLE_SUPERADMIN, ROLE_ADMIN}


def is_super(role: str | None) -> bool:
    return role == ROLE_SUPERADMIN
