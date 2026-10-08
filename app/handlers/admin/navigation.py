from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.database.session import Database
from app.keyboards.reply import (
    admin_books_keyboard,
    admin_channels_keyboard,
    admin_content_keyboard,
    admin_keyboard,
    admin_leaderboard_keyboard,
    admin_questions_keyboard,
    admin_quiz_keyboard,
    admin_settings_keyboard,
    admin_users_keyboard,
    main_keyboard,
)
from app.services.admins import is_admin
from app.utils.auth import require_admin

router = Router(name="admin_navigation")


async def _guard(obj, db: Database) -> bool:
    role = await require_admin(obj, db)
    return role is not None


@router.message(F.text == "🛠 ADMIN")
async def admin_home(message: Message, state: FSMContext, db: Database) -> None:
    if not await _guard(message, db):
        return
    await state.clear()
    await message.answer("🛠 <b>ADMIN PANEL</b>\n\n<i>Sahifa Quiz boshqaruv markazi.</i>", reply_markup=admin_keyboard())


@router.message(F.text.in_({"⬅️ ADMIN PANEL", "⬅️ ASOSIY MENYU"}))
async def back_admin_or_main(message: Message, state: FSMContext, db: Database) -> None:
    if not await _guard(message, db):
        return
    await state.clear()
    if message.text == "⬅️ ASOSIY MENYU":
        await message.answer("📚 <b>SAHIFA QUIZ</b>", reply_markup=main_keyboard(True))
    else:
        await message.answer("🛠 <b>ADMIN PANEL</b>\n\n<i>Boshqaruv markazi.</i>", reply_markup=admin_keyboard())


@router.message(F.text == "⬅️ KONTENT")
async def back_content(message: Message, state: FSMContext, db: Database) -> None:
    if not await _guard(message, db):
        return
    await state.clear()
    await message.answer("📚 <b>KONTENT</b>\n\nKitoblar, savollar va TXT import.", reply_markup=admin_content_keyboard())


@router.message(F.text == "⬅️ KITOBLAR BOSHQARUVI")
async def back_books_manage(message: Message, state: FSMContext, db: Database) -> None:
    if not await _guard(message, db):
        return
    await state.clear()
    await message.answer("📖 <b>KITOBLARNI BOSHQARISH</b>", reply_markup=admin_books_keyboard())


@router.message(F.text == "⬅️ SAVOLLAR BOSHQARUVI")
async def back_questions_manage(message: Message, state: FSMContext, db: Database) -> None:
    if not await _guard(message, db):
        return
    await state.clear()
    await message.answer("❓ <b>SAVOLLARNI BOSHQARISH</b>", reply_markup=admin_questions_keyboard())


@router.message(F.text == "⬅️ FOYDALANUVCHILAR")
async def back_users(message: Message, state: FSMContext, db: Database) -> None:
    if not await _guard(message, db):
        return
    await state.clear()
    await message.answer("👥 <b>FOYDALANUVCHILAR</b>", reply_markup=admin_users_keyboard())


@router.message(F.text == "⬅️ KANALLAR")
async def back_channels(message: Message, state: FSMContext, db: Database) -> None:
    if not await _guard(message, db):
        return
    await state.clear()
    await message.answer("📢 <b>KANALLAR</b>", reply_markup=admin_channels_keyboard())


@router.message(F.text == "⬅️ REYTING")
async def back_leaderboard(message: Message, state: FSMContext, db: Database) -> None:
    if not await _guard(message, db):
        return
    await state.clear()
    await message.answer("🏆 <b>REYTING</b>", reply_markup=admin_leaderboard_keyboard())


@router.message(F.text == "⬅️ TEST BOSHQARUVI")
async def back_quiz_management(message: Message, state: FSMContext, db: Database) -> None:
    if not await _guard(message, db):
        return
    await state.clear()
    await message.answer("🧠 <b>TEST BOSHQARUVI</b>", reply_markup=admin_quiz_keyboard())


@router.message(F.text == "⬅️ SOZLAMALAR")
async def back_settings(message: Message, state: FSMContext, db: Database) -> None:
    if not await _guard(message, db):
        return
    await state.clear()
    await message.answer("⚙️ <b>SOZLAMALAR</b>", reply_markup=admin_settings_keyboard())


@router.callback_query(F.data == "adm:content")
async def callback_content(callback: CallbackQuery, db: Database) -> None:
    if not await _guard(callback, db):
        await callback.answer()
        return
    await callback.answer()
    await callback.message.answer("📚 <b>KONTENT</b>", reply_markup=admin_content_keyboard())


@router.callback_query(F.data == "adm:books")
async def callback_books(callback: CallbackQuery, db: Database) -> None:
    if not await _guard(callback, db):
        await callback.answer()
        return
    await callback.answer()
    await callback.message.answer("📖 <b>KITOBLARNI BOSHQARISH</b>", reply_markup=admin_books_keyboard())


@router.callback_query(F.data == "adm:questions")
async def callback_questions(callback: CallbackQuery, db: Database) -> None:
    if not await _guard(callback, db):
        await callback.answer()
        return
    await callback.answer()
    await callback.message.answer("❓ <b>SAVOLLARNI BOSHQARISH</b>", reply_markup=admin_questions_keyboard())


@router.callback_query(F.data == "adm:settings")
async def callback_settings(callback: CallbackQuery, db: Database) -> None:
    if not await _guard(callback, db):
        await callback.answer()
        return
    await callback.answer()
    await callback.message.answer("⚙️ <b>SOZLAMALAR</b>", reply_markup=admin_settings_keyboard())


@router.callback_query(F.data == "adm:channels")
async def callback_channels(callback: CallbackQuery, db: Database) -> None:
    if not await _guard(callback, db):
        await callback.answer()
        return
    await callback.answer()
    await callback.message.answer("📢 <b>KANALLAR</b>", reply_markup=admin_channels_keyboard())
