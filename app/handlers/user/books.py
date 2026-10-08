from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.database.session import Database
from app.keyboards.inline import book_detail_keyboard, book_list_keyboard
from app.keyboards.reply import books_keyboard
from app.services.books import book_question_count, get_book, list_books, search_books
from app.states.user import UserStates
from app.utils.ui import book_text, h, require_callback_subscription, require_subscription

router = Router(name="user_books")
PAGE_SIZE = 8


async def _show_book_list(target: Message, db: Database, *, page: int = 0) -> None:
    async with db.session() as session:
        books = await list_books(session, offset=page * PAGE_SIZE, limit=PAGE_SIZE + 1)
    has_next = len(books) > PAGE_SIZE
    books = books[:PAGE_SIZE]
    text = "📚 <b>KITOBLAR RO‘YXATI</b>\n\n<i>O‘qishni istagan asaringizni tanlang.</i>"
    await target.answer(text, reply_markup=book_list_keyboard(books, page=page, has_next=has_next, back_callback="books:home"))


async def _replace_with_book_list(callback: CallbackQuery, db: Database, *, page: int = 0) -> None:
    try:
        await callback.message.delete()
    except Exception:
        pass
    await _show_book_list(callback.message, db, page=page)


@router.message(F.text == "📚 KITOBLAR")
async def books_home(message: Message, state: FSMContext, db: Database, bot) -> None:
    if not await require_subscription(message, bot, db):
        return
    await state.clear()
    await message.answer("📚 <b>KITOBLAR</b>\n\n<i>Nom yoki muallif bo‘yicha toping.</i>", reply_markup=books_keyboard())


@router.message(F.text == "🔎 KITOB QIDIRISH")
async def ask_book_search(message: Message, state: FSMContext, db: Database, bot) -> None:
    if not await require_subscription(message, bot, db):
        return
    await state.set_state(UserStates.search_book)
    await message.answer("🔎 <b>KITOB QIDIRISH</b>\n\nKitob nomi yoki muallifini yozing.\n<i>Masalan: O‘tkan kunlar</i>")


@router.message(UserStates.search_book)
async def search_book_handler(message: Message, state: FSMContext, db: Database, bot) -> None:
    if not await require_subscription(message, bot, db):
        return
    query = (message.text or "").strip()
    if len(query) < 2:
        await message.answer("⚠️ <b>Kamida 2 ta belgi yozing.</b>")
        return
    async with db.session() as session:
        books = await search_books(session, query, limit=PAGE_SIZE)
    await state.clear()
    if not books:
        await message.answer("📭 <b>Kitob topilmadi</b>\n\nBoshqa nom yoki muallif bilan urinib ko‘ring.", reply_markup=books_keyboard())
        return
    await message.answer(
        f"🔎 <b>QIDIRUV NATIJASI</b>\n\n{len(books)} ta mos kitob topildi.",
        reply_markup=book_list_keyboard(books, back_callback="books:home"),
    )


@router.message(F.text == "📖 BARCHA KITOBLAR")
async def all_books(message: Message, state: FSMContext, db: Database, bot) -> None:
    if not await require_subscription(message, bot, db):
        return
    await state.clear()
    await _show_book_list(message, db, page=0)


@router.callback_query(F.data.startswith("books:page:"))
async def books_page(callback: CallbackQuery, db: Database, bot) -> None:
    if not await require_callback_subscription(callback, bot, db):
        await callback.answer()
        return
    try:
        page = max(0, int(callback.data.rsplit(":", 1)[1]))
    except (ValueError, IndexError):
        await callback.answer("Sahifa noto‘g‘ri.", show_alert=True)
        return
    await callback.answer()
    await _replace_with_book_list(callback, db, page=page)


@router.callback_query(F.data == "books:list:0")
async def books_list_first(callback: CallbackQuery, db: Database, bot) -> None:
    if not await require_callback_subscription(callback, bot, db):
        await callback.answer()
        return
    await callback.answer()
    await _replace_with_book_list(callback, db, page=0)


@router.callback_query(F.data.startswith("book:"))
async def show_book(callback: CallbackQuery, db: Database, bot) -> None:
    if not await require_callback_subscription(callback, bot, db):
        await callback.answer()
        return
    try:
        book_id = int(callback.data.split(":", 1)[1])
    except ValueError:
        await callback.answer("Noto‘g‘ri kitob.", show_alert=True)
        return
    async with db.session() as session:
        book = await get_book(session, book_id)
        if not book or not book.is_active:
            await callback.answer("Kitob topilmadi.", show_alert=True)
            return
        count = await book_question_count(session, book.id)
    await callback.answer()
    try:
        await callback.message.delete()
    except Exception:
        pass
    text = book_text(book.title, book.author, book.description, count)
    markup = book_detail_keyboard(book, back_callback="books:list:0")
    if book.cover_file_id:
        await callback.message.answer_photo(book.cover_file_id, caption=text, reply_markup=markup)
    else:
        await callback.message.answer(text, reply_markup=markup)
