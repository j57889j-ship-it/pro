from __future__ import annotations

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.database.session import Database
from app.services.admins import is_admin


class AdminOnlyMiddleware(BaseMiddleware):
    def __init__(self, db: Database) -> None:
        self.db = db

    async def __call__(self, handler, event: TelegramObject, data: dict):
        user = getattr(event, "from_user", None)
        if not user:
            return None
        async with self.db.session() as session:
            if not await is_admin(session, user.id):
                return None
        return await handler(event, data)
