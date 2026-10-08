from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Setting


DEFAULT_SETTINGS = {
    "reaction_enabled": "1",
    "reaction_emoji": "🔥",
    "last_channel_post_id": "",
    "reaction_last_error": "",
    "daily_question_id": "",
    "points_per_correct": "10",
}


async def get_setting(session: AsyncSession, key: str, default: str = "") -> str:
    result = await session.execute(select(Setting).where(Setting.key == key))
    row = result.scalar_one_or_none()
    return row.value if row else default


async def set_setting(session: AsyncSession, key: str, value: str) -> None:
    result = await session.execute(select(Setting).where(Setting.key == key))
    row = result.scalar_one_or_none()
    if row is None:
        session.add(Setting(key=key, value=value))
    else:
        row.value = value
    await session.commit()


async def ensure_default_settings(session: AsyncSession) -> None:
    result = await session.execute(select(Setting.key))
    existing = set(result.scalars().all())
    for key, value in DEFAULT_SETTINGS.items():
        if key not in existing:
            session.add(Setting(key=key, value=value))
    await session.commit()
