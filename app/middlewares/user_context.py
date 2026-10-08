from __future__ import annotations

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from redis.asyncio import Redis

from app.config import Settings
from app.database.session import Database
from app.services.admins import is_admin
from app.services.users import get_or_create_user


class UserContextMiddleware(BaseMiddleware):
    def __init__(self, db: Database, settings: Settings, redis: Redis) -> None:
        self.db = db
        self.settings = settings
        self.redis = redis

    async def __call__(self, handler, event: TelegramObject, data: dict):
        user = getattr(event, "from_user", None)
        data["db"] = self.db
        data["settings"] = self.settings
        data["redis"] = self.redis
        if user:
            async with self.db.session() as session:
                db_user = await get_or_create_user(session, user)
                admin = await is_admin(session, user.id)
                if db_user.is_blocked and not admin:
                    return None
                data["db_user"] = db_user
        return await handler(event, data)
