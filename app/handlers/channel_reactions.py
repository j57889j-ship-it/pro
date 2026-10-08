from __future__ import annotations

import logging

from aiogram import Router
from aiogram.types import Message, ReactionTypeEmoji
from sqlalchemy import select

from app.config import Settings
from app.constants import SUPPORTED_REACTION_EMOJIS
from app.database.session import Database
from app.services.settings import get_setting, set_setting

logger = logging.getLogger("sahifa_quiz.reactions")
router = Router(name="channel_reactions")


def normalize_reaction(value: str) -> str:
    return {"❤️": "❤", "♥️": "❤"}.get(value.strip(), value.strip())


@router.channel_post()
async def auto_react_to_channel_post(message: Message, db: Database, bot, settings: Settings) -> None:
    if not settings.target_channel_id or message.chat.id != settings.target_channel_id:
        return

    async with db.session() as session:
        await set_setting(session, "last_channel_post_id", str(message.message_id))
        enabled = await get_setting(session, "reaction_enabled", "1") == "1"
        emoji = normalize_reaction(await get_setting(session, "reaction_emoji", "🔥"))

    if not enabled:
        return
    if emoji not in SUPPORTED_REACTION_EMOJIS:
        logger.error("Unsupported reaction configured: %s", emoji)
        async with db.session() as session:
            await set_setting(session, "reaction_last_error", f"Unsupported emoji: {emoji}")
        return

    try:
        chat = await bot.get_chat(settings.target_channel_id)
        if chat.available_reactions:
            allowed = {getattr(item, "emoji", None) for item in chat.available_reactions}
            if emoji not in allowed:
                reason = f"Reaction {emoji} is not enabled in target channel"
                logger.warning(reason)
                async with db.session() as session:
                    await set_setting(session, "reaction_last_error", reason)
                return

        await bot.set_message_reaction(
            chat_id=settings.target_channel_id,
            message_id=message.message_id,
            reaction=[ReactionTypeEmoji(type="emoji", emoji=emoji)],
            is_big=True,
        )
        async with db.session() as session:
            await set_setting(session, "reaction_last_error", "")
        logger.info("Reaction %s added to channel post %s", emoji, message.message_id)
    except Exception as exc:
        logger.exception("Reaction failed for channel post %s: %s", message.message_id, exc)
        async with db.session() as session:
            await set_setting(session, "reaction_last_error", str(exc)[:500])
