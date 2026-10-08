from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import select, update

from app.config import Settings
from app.database.models import User
from app.database.session import Database
from app.keyboards.reply import admin_leaderboard_keyboard
from app.services.quizzes import top_users
from app.services.settings import get_setting, set_setting
from app.states.admin import AdminSettingStates
from app.utils.auth import can_manage_users, require_admin
from app.utils.ui import h

router = Router(name="admin_leaderboard")


@router.message(F.text == "🏆 REYTING")
async def home(message: Message, db: Database) -> None:
    if not can_manage_users(await require_admin(message, db)):
        return
    await message.answer("🏆 <b>REYTING</b>", reply_markup=admin_leaderboard_keyboard())


@router.message(F.text == "👑 TOP KITOBXONLAR")
async def top_list(message: Message, db: Database, settings: Settings) -> None:
    if not can_manage_users(await require_admin(message, db)):
        return
    async with db.session() as session:
        users = await top_users(session, settings.top_limit)
    rows = []
    for i, user in enumerate(users, 1):
        name = f"@{h(user.username)}" if user.username else h(user.first_name or str(user.telegram_id))
        rows.append(f"{i}. {name} — <b>{user.score}</b> ⭐")
    await message.answer("🏆 <b>TOP KITOBXONLAR</b>\n\n" + ("\n".join(rows) if rows else "📭 Reyting bo‘sh."))


@router.message(F.text == "⚙️ TOP SOZLAMALARI")
async def top_settings(message: Message, db: Database, settings: Settings) -> None:
    if not can_manage_users(await require_admin(message, db)):
        return
    await message.answer(f"⚙️ <b>TOP SOZLAMALARI</b>\n\nKo‘rsatiladigan userlar: <b>{settings.top_limit}</b> ta\nBall: <b>{settings.points_per_correct}</b> / to‘g‘ri javob")


@router.message(F.text == "🧹 TOP RESET")
async def top_reset(message: Message, db: Database) -> None:
    if not (await require_admin(message, db) == "superadmin"):
        return
    async with db.session() as session:
        await session.execute(update(User).values(score=0, total_questions=0, correct_answers=0, wrong_answers=0, streak=0, last_quiz_day=None))
        await session.commit()
    await message.answer("🧹 <b>TOP VA USER STATISTIKASI RESET QILINDI.</b>")
