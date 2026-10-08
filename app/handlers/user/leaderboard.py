from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import select

from app.config import Settings
from app.database.models import User
from app.database.session import Database
from app.keyboards.inline import quiz_finish_keyboard
from app.services.quizzes import top_users, user_rank
from app.utils.ui import h, require_subscription

router = Router(name="user_leaderboard")


@router.message(F.text == "🏆 TOP")
async def top_home(message: Message, state: FSMContext, db: Database, bot, settings: Settings) -> None:
    if not await require_subscription(message, bot, db):
        return
    await state.clear()
    async with db.session() as session:
        users = await top_users(session, settings.top_limit)
        me = await session.scalar(select(User).where(User.telegram_id == message.from_user.id))
        rank = await user_rank(session, me.id) if me else 0
    if not users:
        body = "📭 <b>Hali reyting mavjud emas.</b>"
    else:
        rows = []
        medals = ["🥇", "🥈", "🥉"]
        for i, user in enumerate(users, 1):
            name = f"@{h(user.username)}" if user.username else h(user.first_name or str(user.telegram_id))
            rows.append(f"{medals[i-1] if i <= 3 else f'{i}️⃣'} {name} — <b>{user.score}</b> ⭐")
        body = "\n".join(rows)
    await message.answer(
        "🏆 <b>TOP KITOBXONLAR</b>\n\n"
        f"{body}\n\n━━━━━━━━━━━━━━━━\n"
        f"👤 Sizning o‘rningiz: <b>#{rank}</b>"
    )
