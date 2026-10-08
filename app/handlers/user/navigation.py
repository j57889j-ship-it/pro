from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.database.session import Database
from app.keyboards.reply import admin_keyboard, books_keyboard, help_keyboard, main_keyboard, profile_keyboard, quiz_keyboard
from app.services.admins import is_admin
from app.utils.ui import menu_text, require_callback_subscription, require_subscription

router = Router(name="user_navigation")

@router.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext, db: Database, bot) -> None:
    await state.clear()
    await message.answer("✅ <b>Joriy amal bekor qilindi.</b>")
    await _main(message, state, db, bot)



async def _main(message: Message, state: FSMContext, db: Database, bot) -> None:
    await state.clear()
    if not await require_subscription(message, bot, db):
        return
    async with db.session() as session:
        admin = await is_admin(session, message.from_user.id)
    await message.answer(menu_text(), reply_markup=main_keyboard(admin))


@router.message(F.text.in_({"⬅️ ASOSIY MENYU", "🏠 BOSH MENYU"}))
async def main_back(message: Message, state: FSMContext, db: Database, bot) -> None:
    await _main(message, state, db, bot)


@router.message(F.text == "❌ BEKOR")
async def cancel_all(message: Message, state: FSMContext, db: Database, bot) -> None:
    await state.clear()
    await message.answer("✅ Joriy amal bekor qilindi.")
    await _main(message, state, db, bot)


@router.message(F.text == "⬅️ KITOBLAR")
async def back_books(message: Message, state: FSMContext, db: Database, bot) -> None:
    await state.clear()
    if not await require_subscription(message, bot, db):
        return
    await message.answer("📚 <b>KITOBLAR</b>\n\n<i>Nom yoki muallif bo‘yicha toping.</i>", reply_markup=books_keyboard())


@router.message(F.text == "⬅️ TESTLAR")
async def back_tests(message: Message, state: FSMContext, db: Database, bot) -> None:
    await state.clear()
    if not await require_subscription(message, bot, db):
        return
    await message.answer("🧠 <b>TEST MARKAZI</b>\n\n<i>Rejimni tanlang.</i>", reply_markup=quiz_keyboard())


@router.message(F.text == "⬅️ PROFIL")
async def back_profile(message: Message, state: FSMContext, db: Database, bot) -> None:
    await state.clear()
    if not await require_subscription(message, bot, db):
        return
    await message.answer("👤 <b>PROFIL</b>\n\n<i>Shaxsiy natijalaringiz.</i>", reply_markup=profile_keyboard())


@router.message(F.text == "⬅️ YORDAM")
async def back_help(message: Message, state: FSMContext, db: Database, bot) -> None:
    await state.clear()
    if not await require_subscription(message, bot, db):
        return
    await message.answer("ℹ️ <b>YORDAM</b>\n\n<i>Kerakli bo‘limni tanlang.</i>", reply_markup=help_keyboard())


@router.callback_query(F.data == "main:home")
async def callback_main(callback: CallbackQuery, state: FSMContext, db: Database, bot) -> None:
    await state.clear()
    if not await require_callback_subscription(callback, bot, db):
        await callback.answer()
        return
    await callback.answer()
    if callback.message:
        async with db.session() as session:
            admin = await is_admin(session, callback.from_user.id)
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(menu_text(), reply_markup=main_keyboard(admin))


@router.callback_query(F.data == "books:home")
async def callback_books(callback: CallbackQuery, state: FSMContext, db: Database, bot) -> None:
    await state.clear()
    if not await require_callback_subscription(callback, bot, db):
        await callback.answer()
        return
    await callback.answer()
    if callback.message:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer("📚 <b>KITOBLAR</b>\n\n<i>Kitobni qidiring yoki ro‘yxatdan tanlang.</i>", reply_markup=books_keyboard())


@router.callback_query(F.data == "quiz:home")
async def callback_quiz(callback: CallbackQuery, state: FSMContext, db: Database, bot) -> None:
    await state.clear()
    if not await require_callback_subscription(callback, bot, db):
        await callback.answer()
        return
    await callback.answer()
    if callback.message:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer("🧠 <b>TEST MARKAZI</b>\n\n<i>Rejimni tanlang.</i>", reply_markup=quiz_keyboard())
