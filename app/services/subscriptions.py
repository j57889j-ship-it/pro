from __future__ import annotations

from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import MandatoryChannel


async def active_channels(session: AsyncSession) -> list[MandatoryChannel]:
    result = await session.execute(
        select(MandatoryChannel)
        .where(MandatoryChannel.is_active.is_(True))
        .order_by(MandatoryChannel.id)
    )
    return list(result.scalars().all())


async def is_subscribed_to_all(session: AsyncSession, bot: Bot, user_id: int) -> bool:
    channels = await active_channels(session)
    if not channels:
        return True
    for channel in channels:
        try:
            member = await bot.get_chat_member(channel.chat_id, user_id)
        except (TelegramBadRequest, TelegramForbiddenError):
            return False
        if member.status in {ChatMemberStatus.LEFT, ChatMemberStatus.KICKED}:
            return False
        if member.status == ChatMemberStatus.RESTRICTED and not getattr(member, "is_member", True):
            return False
    return True
