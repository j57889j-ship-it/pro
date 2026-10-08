from __future__ import annotations

from aiogram.types import User as TgUser
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User


async def get_or_create_user(session: AsyncSession, tg_user: TgUser) -> User:
    result = await session.execute(select(User).where(User.telegram_id == tg_user.id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name or "",
            last_name=tg_user.last_name,
        )
        session.add(user)
    else:
        user.username = tg_user.username
        user.first_name = tg_user.first_name or ""
        user.last_name = tg_user.last_name
    await session.commit()
    await session.refresh(user)
    return user


async def search_users(session: AsyncSession, query: str, limit: int = 10) -> list[User]:
    q = query.strip()
    if not q:
        return []
    if q.startswith("@"): 
        q = q[1:]
    conditions = [User.username.ilike(f"%{q}%")]
    if q.isdigit():
        conditions.insert(0, User.telegram_id == int(q))
    result = await session.execute(select(User).where(or_(*conditions)).order_by(User.id.desc()).limit(limit))
    return list(result.scalars().all())
