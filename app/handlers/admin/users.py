from __future__ import annotations

import asyncio

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import func, select

from app.database.models import QuizAttempt, User
from app.database.session import Database
from app.keyboards.reply import admin_users_keyboard
from app.services.users import search_users
from app.states.admin import AdminBroadcastStates, AdminUserStates
from app.utils.auth import can_manage_users, require_admin
from app.utils.ui import h

router = Router(name="admin_users")


@router.message(F.text == "👥 FOYDALANUVCHILAR")
async def users_home(message: Message, db: Database) -> None:
    if not can_manage_users(await require_admin(message, db)):
        return
    await message.answer("👥 <b>FOYDALANUVCHILAR</b>", reply_markup=admin_users_keyboard())


@router.message(F.text == "🔎 USER QIDIRISH")
async def search_start(message: Message, state: FSMContext, db: Database) -> None:
    if not can_manage_users(await require_admin(message, db)):
        return
    await state.set_state(AdminUserStates.search)
    await message.answer("🔎 Username yoki Telegram ID yuboring.")


@router.message(AdminUserStates.search)
async def search_value(message: Message, state: FSMContext, db: Database) -> None:
    async with db.session() as session:
        users = await search_users(session, message.text or "", limit=10)
    await state.clear()
    if not users:
        await message.answer("📭 User topilmadi.")
        return
    lines = ["👥 <b>TOPILGAN USERLAR</b>", ""]
    for user in users:
        name = f"@{h(user.username)}" if user.username else h(user.first_name or str(user.telegram_id))
        lines.append(f"🆔 <code>{user.telegram_id}</code> — {name} — <b>{user.score}</b> ⭐")
    lines.append("\nAniq Telegram ID yuborib to‘liq statistikani ko‘ring.")
    await message.answer("\n".join(lines))


@router.message(F.text == "📊 USER STATISTIKASI")
async def stats_start(message: Message, state: FSMContext, db: Database) -> None:
    if not can_manage_users(await require_admin(message, db)):
        return
    await state.set_state(AdminUserStates.manage)
    await message.answer("📊 User Telegram ID sini yuboring.")


@router.message(AdminUserStates.manage)
async def stats_value(message: Message, state: FSMContext, db: Database) -> None:
    if not (message.text or "").isdigit():
        await message.answer("⚠️ Telegram ID raqam bo‘lishi kerak.")
        return
    async with db.session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == int(message.text)))
        if not user:
            await message.answer("📭 User topilmadi.")
            return
        attempts = await session.scalar(select(func.count(QuizAttempt.id)).where(QuizAttempt.user_id == user.id, QuizAttempt.completed.is_(True))) or 0
    await state.clear()
    name = f"@{h(user.username)}" if user.username else h(user.first_name or str(user.telegram_id))
    accuracy = round(user.correct_answers / user.total_questions * 100) if user.total_questions else 0
    await message.answer(
        "👤 <b>USER</b>\n\n"
        f"{name}\n🆔 <code>{user.telegram_id}</code>\n"
        f"⭐ Ball: <b>{user.score}</b>\n"
        f"🧠 Tugallangan testlar: <b>{attempts}</b>\n"
        f"✅ To‘g‘ri: <b>{user.correct_answers}</b>\n"
        f"❌ Xato: <b>{user.wrong_answers}</b>\n"
        f"🎯 Aniqlik: <b>{accuracy}%</b>\n"
        f"🔥 Streak: <b>{user.streak}</b>\n"
        f"{'🚫 Bloklangan' if user.is_blocked else '🟢 Faol'}"
    )


@router.message(F.text == "🚫 BLOK / UNBLOK")
async def block_start(message: Message, state: FSMContext, db: Database) -> None:
    if not can_manage_users(await require_admin(message, db)):
        return
    await state.set_state(AdminUserStates.block)
    await message.answer("🚫 Telegram ID yuboring.")


@router.message(AdminUserStates.block)
async def block_value(message: Message, state: FSMContext, db: Database) -> None:
    if not (message.text or "").isdigit():
        await message.answer("⚠️ Telegram ID raqam bo‘lishi kerak.")
        return
    async with db.session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == int(message.text)))
        if not user:
            await message.answer("📭 User topilmadi.")
            return
        user.is_blocked = not user.is_blocked
        status = user.is_blocked
        await session.commit()
    await state.clear()
    await message.answer("✅ Bloklandi." if status else "✅ Blokdan chiqarildi.")


@router.message(F.text == "🧹 USER STATISTIKASINI TOZALASH")
async def clean_start(message: Message, state: FSMContext, db: Database) -> None:
    if not can_manage_users(await require_admin(message, db)):
        return
    await state.set_state(AdminUserStates.clean)
    await message.answer("🧹 Telegram ID yuboring. Ball va test statistikasi 0 ga qaytariladi.")


@router.message(AdminUserStates.clean)
async def clean_value(message: Message, state: FSMContext, db: Database) -> None:
    if not (message.text or "").isdigit():
        await message.answer("⚠️ Telegram ID raqam bo‘lishi kerak.")
        return
    async with db.session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == int(message.text)))
        if not user:
            await message.answer("📭 User topilmadi.")
            return
        user.score = 0
        user.total_questions = 0
        user.correct_answers = 0
        user.wrong_answers = 0
        user.streak = 0
        user.last_quiz_day = None
        await session.commit()
    await state.clear()
    await message.answer("✅ User statistikasi tozalandi.")


@router.message(F.text == "📣 XABAR YUBORISH")
async def broadcast_start(message: Message, state: FSMContext, db: Database) -> None:
    if not can_manage_users(await require_admin(message, db)):
        return
    await state.set_state(AdminBroadcastStates.text)
    await message.answer("📣 Barcha bloklanmagan userlarga yuboriladigan xabarni yuboring. /cancel bilan bekor qilinadi.")


@router.message(AdminBroadcastStates.text)
async def broadcast_send(message: Message, state: FSMContext, db: Database, bot) -> None:
    async with db.session() as session:
        ids = [int(x) for x in (await session.execute(select(User.telegram_id).where(User.is_blocked.is_(False)))).scalars().all()]
    sent = failed = 0
    for telegram_id in ids:
        try:
            await bot.send_message(telegram_id, h(message.text or ""))
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)
    await state.clear()
    await message.answer(f"📣 <b>YUBORISH YAKUNLANDI</b>\n\n✅ Yetkazildi: <b>{sent}</b>\n⚠️ Yetkazilmadi: <b>{failed}</b>")
