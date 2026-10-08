from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import func, select

from app.database.models import QuizAttempt, User
from app.database.session import Database
from app.keyboards.reply import profile_keyboard
from app.services.quizzes import user_rank
from app.utils.ui import require_subscription

router = Router(name="user_profile")


@router.message(F.text == "👤 PROFIL")
async def profile_home(message: Message, state: FSMContext, db: Database, bot) -> None:
    if not await require_subscription(message, bot, db):
        return
    await state.clear()
    await message.answer("👤 <b>PROFILIM</b>\n\nNatijalaringiz shu yerda.", reply_markup=profile_keyboard())


@router.message(F.text == "📊 STATISTIKA")
async def stats(message: Message, db: Database, bot) -> None:
    if not await require_subscription(message, bot, db):
        return
    async with db.session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == message.from_user.id))
        attempts = await session.scalar(select(func.count(QuizAttempt.id)).where(QuizAttempt.user_id == user.id, QuizAttempt.completed.is_(True))) if user else 0
        rank = await user_rank(session, user.id) if user else 0
    if not user:
        await message.answer("⚠️ Profil topilmadi.")
        return
    accuracy = round(user.correct_answers / user.total_questions * 100) if user.total_questions else 0
    await message.answer(
        "📊 <b>MENING STATISTIKAM</b>\n\n"
        f"⭐ Ball: <b>{user.score}</b>\n"
        f"🧠 Tugallangan testlar: <b>{attempts}</b>\n"
        f"✅ To‘g‘ri: <b>{user.correct_answers}</b>\n"
        f"❌ Xato: <b>{user.wrong_answers}</b>\n"
        f"🎯 Aniqlik: <b>{accuracy}%</b>\n"
        f"🏆 TOP: <b>#{rank}</b>\n"
        f"🔥 Streak: <b>{user.streak} kun</b>"
    )


@router.message(F.text == "❌ XATOLARIM")
async def wrong_profile(message: Message, db: Database, bot) -> None:
    if not await require_subscription(message, bot, db):
        return
    await message.answer("❌ <b>Xato savollar</b>\n\n🧠 Test bo‘limidagi “XATO SAVOLLARIM” tugmasi orqali qayta ishlashingiz mumkin.")


@router.message(F.text == "🔥 STREAK")
async def streak(message: Message, db: Database, bot) -> None:
    if not await require_subscription(message, bot, db):
        return
    async with db.session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == message.from_user.id))
    await message.answer(f"🔥 <b>SIZNING STREAKINGIZ</b>\n\n🔥 {user.streak if user else 0} kun\n\n<i>Har kuni kamida bitta testni tugating.</i>")
