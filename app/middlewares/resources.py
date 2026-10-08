from __future__ import annotations

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from redis.asyncio import Redis

from app.config import Settings
from app.database.session import Database


class ResourcesMiddleware(BaseMiddleware):
    def __init__(self, db: Database, settings: Settings, redis: Redis) -> None:
        self.db = db
        self.settings = settings
        self.redis = redis

    async def __call__(self, handler, event: TelegramObject, data: dict):
        data["db"] = self.db
        data["settings"] = self.settings
        data["redis"] = self.redis
        return await handler(event, data)
