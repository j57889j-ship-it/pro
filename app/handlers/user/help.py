from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import select

from app.database.models import Admin
from app.database.session import Database
from app.keyboards.reply import help_keyboard
from app.states.user import UserStates
from app.utils.ui import h, require_subscription

router = Router(name="user_help")


@router.message(F.text == "ℹ️ YORDAM")
async def help_home(message: Message, state: FSMContext, db: Database, bot) -> None:
    if not await require_subscription(message, bot, db):
        return
    await state.clear()
    await message.answer("ℹ️ <b>YORDAM</b>\n\n<i>Kerakli bo‘limni tanlang.</i>", reply_markup=help_keyboard())


@router.message(F.text == "📖 BOT HAQIDA")
async def about(message: Message, db: Database, bot) -> None:
    if not await require_subscription(message, bot, db):
        return
    await message.answer(
        "📚 <b>SAHIFA QUIZ</b>\n\n"
        "<i>Kitobni toping, kanalimizdagi ma’lumotni o‘qing va asar bo‘yicha bilimingizni sinang.</i>\n\n"
        "✨ <b>O‘qing. Sinang. Yangi sahifa oching.</b>"
    )


@router.message(F.text == "❓ QANDAY ISHLAYDI")
async def how(message: Message, db: Database, bot) -> None:
    if not await require_subscription(message, bot, db):
        return
    await message.answer(
        "🧭 <b>QANDAY ISHLAYDI?</b>\n\n"
        "1️⃣ 📚 Kitobni toping\n"
        "2️⃣ 📖 Batafsil ma’lumotni oching\n"
        "3️⃣ 🧠 Testni boshlang\n"
        "4️⃣ 🏆 Natijangizni TOP bilan solishtiring"
    )


@router.message(F.text == "💬 ADMIN BILAN BOG‘LANISH")
async def contact_admin(message: Message, state: FSMContext, db: Database, bot) -> None:
    if not await require_subscription(message, bot, db):
        return
    await state.set_state(UserStates.contact_admin)
    await message.answer("💬 <b>ADMIN BILAN BOG‘LANISH</b>\n\nXabaringizni yozing.")


@router.message(UserStates.contact_admin)
async def contact_message(message: Message, state: FSMContext, db: Database, bot) -> None:
    if not await require_subscription(message, bot, db):
        return
    text = (message.text or "").strip()
    if not text:
        await message.answer("⚠️ <b>Matnli xabar yuboring.</b>")
        return
    async with db.session() as session:
        admin_ids = list((await session.execute(select(Admin.telegram_id).where(Admin.is_active.is_(True)))).scalars().all())
    user_line = (
        "💬 <b>FOYDALANUVCHI XABARI</b>\n\n"
        f"🆔 <code>{message.from_user.id}</code>\n"
        f"👤 @{h(message.from_user.username or 'username_yok')}\n\n"
        f"{h(text)}"
    )
    sent = 0
    for admin_id in admin_ids:
        try:
            await bot.send_message(int(admin_id), user_line)
            sent += 1
        except Exception:
            pass
    await state.clear()
    await message.answer("✅ <b>Xabaringiz yuborildi.</b>" if sent else "⚠️ <b>Faol admin topilmadi.</b>")


@router.message(Command("help"))
async def help_command(message: Message, db: Database, bot) -> None:
    if not await require_subscription(message, bot, db):
        return
    await message.answer("ℹ️ <b>YORDAM</b>\n\nKerakli bo‘limni tanlang.", reply_markup=help_keyboard())


@router.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext, db: Database, bot) -> None:
    await state.clear()
    if await require_subscription(message, bot, db):
        await message.answer("✅ Joriy amal bekor qilindi.")
