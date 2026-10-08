from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy import func, select

from app.database.models import Book, Question, QuizAttempt, User
from app.database.session import Database
from app.utils.auth import require_admin

router = Router(name="admin_dashboard")


@router.message(F.text == "📊 DASHBOARD")
async def dashboard(message: Message, db: Database) -> None:
    if not await require_admin(message, db):
        return
    async with db.session() as session:
        users = await session.scalar(select(func.count(User.id))) or 0
        books = await session.scalar(select(func.count(Book.id)).where(Book.is_active.is_(True))) or 0
        questions = await session.scalar(select(func.count(Question.id)).where(Question.is_active.is_(True))) or 0
        attempts = await session.scalar(select(func.count(QuizAttempt.id)).where(QuizAttempt.completed.is_(True))) or 0
    await message.answer(
        "📊 <b>BOSHQARUV</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{users}</b>\n"
        f"📖 Kitoblar: <b>{books}</b>\n"
        f"❓ Savollar: <b>{questions}</b>\n"
        f"🏁 Tugallangan testlar: <b>{attempts}</b>"
    )
