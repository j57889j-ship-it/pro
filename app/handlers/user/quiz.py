from __future__ import annotations

import asyncio

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from app.config import Settings
from app.database.models import Question, User
from app.database.session import Database
from app.keyboards.inline import answers_keyboard, book_list_keyboard, quiz_count_keyboard, quiz_finish_keyboard
from app.keyboards.reply import quiz_keyboard
from app.services.books import get_book, list_books
from app.services.quizzes import create_attempt, finish_attempt, get_questions, get_random_questions, get_wrong_questions, record_answer
from app.services.settings import get_setting
from app.states.user import UserStates
from app.utils.ui import answer_feedback_text, h, question_text, quiz_intro, require_callback_subscription, require_subscription, result_text

router = Router(name="user_quiz")


async def start_questions(message: Message, state: FSMContext, db: Database, question_ids: list[int], book_id: int | None, title: str) -> None:
    if not question_ids:
        await message.answer("📭 <b>SAVOLLAR TOPILMADI</b>\n\nBu rejim uchun faol savollar mavjud emas.", reply_markup=quiz_keyboard())
        return
    async with db.session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == message.from_user.id))
        if not user:
            await message.answer("⚠️ <b>Profil topilmadi.</b> /start ni bosing.")
            return
        attempt = await create_attempt(session, user.id, book_id, len(question_ids))
    await state.set_state(UserStates.answering_quiz)
    await state.update_data(question_ids=question_ids, index=0, attempt_id=attempt.id, book_id=book_id, title=title)
    await send_current_question(message, state, db)


async def send_current_question(message: Message, state: FSMContext, db: Database) -> None:
    data = await state.get_data()
    ids = [int(x) for x in data.get("question_ids", [])]
    index = int(data.get("index", 0))
    title = str(data.get("title", "SAHIFA QUIZ"))
    attempt_id = int(data.get("attempt_id", 0))
    if index >= len(ids):
        await _finish(message, state, db, attempt_id)
        return
    async with db.session() as session:
        question = await session.get(Question, ids[index])
    if not question:
        await state.update_data(index=index + 1)
        await send_current_question(message, state, db)
        return
    text = question_text(title, question, index, len(ids))
    await message.answer(text, reply_markup=answers_keyboard(attempt_id, index))


async def _finish(message: Message, state: FSMContext, db: Database, attempt_id: int) -> None:
    async with db.session() as session:
        correct, total, score = await finish_attempt(session, attempt_id, completed=True)
    await state.clear()
    await message.answer(result_text(correct, total, score), reply_markup=quiz_finish_keyboard())


@router.message(F.text == "🧠 TEST")
async def quiz_home(message: Message, state: FSMContext, db: Database, bot) -> None:
    if not await require_subscription(message, bot, db):
        return
    await state.clear()
    await message.answer("🧠 <b>TEST MARKAZI</b>\n\n<i>Kitobni tanlang yoki boshqa rejimni sinab ko‘ring.</i>", reply_markup=quiz_keyboard())


@router.message(F.text == "📖 KITOB BO‘YICHA")
async def quiz_by_book(message: Message, state: FSMContext, db: Database, bot) -> None:
    if not await require_subscription(message, bot, db):
        return
    async with db.session() as session:
        books = await list_books(session, limit=50)
    if not books:
        await message.answer("📭 <b>Hozircha kitoblar yo‘q.</b>", reply_markup=quiz_keyboard())
        return
    await state.set_state(UserStates.select_quiz_book)
    await message.answer("📖 <b>TEST UCHUN KITOB</b>\n\n<i>Kitobni tanlang.</i>", reply_markup=book_list_keyboard(books, back_callback="quiz:home", item_callback_prefix="quizbook"))


@router.callback_query(F.data.startswith("quizbook:"))
async def quiz_book_callback(callback: CallbackQuery, state: FSMContext, db: Database, bot) -> None:
    if not await require_callback_subscription(callback, bot, db):
        await callback.answer()
        return
    try:
        book_id = int(callback.data.split(":", 1)[1])
    except ValueError:
        await callback.answer("Kitob noto‘g‘ri.", show_alert=True)
        return
    async with db.session() as session:
        book = await get_book(session, book_id)
        if not book or not book.is_active:
            await callback.answer("Kitob topilmadi.", show_alert=True)
            return
        questions = await get_questions(session, book_id, 1)
        available = await session.scalar(select(Question.id).where(Question.book_id == book_id, Question.is_active.is_(True)).limit(1))
    await state.update_data(book_id=book.id, title=book.title)
    await state.set_state(UserStates.select_quiz_count)
    await callback.answer()
    await callback.message.answer(quiz_intro(book.title, 1 if questions else 0), reply_markup=quiz_count_keyboard(book.id))


@router.callback_query(F.data.startswith("quiz_count:"))
async def quiz_count_callback(callback: CallbackQuery, state: FSMContext, db: Database, bot) -> None:
    if not await require_callback_subscription(callback, bot, db):
        await callback.answer()
        return
    parts = callback.data.split(":")
    if len(parts) != 3 or not parts[1].isdigit() or not parts[2].isdigit():
        await callback.answer("Test parametri noto‘g‘ri.", show_alert=True)
        return
    book_id, count = int(parts[1]), int(parts[2])
    count = max(1, min(count, 100))
    data = await state.get_data()
    title = str(data.get("title", "KITOB"))
    async with db.session() as session:
        questions = await get_questions(session, book_id, count)
    if not questions:
        await callback.answer("Bu kitobda savollar yo‘q.", show_alert=True)
        return
    await callback.answer("🧠 Test boshlandi!")
    await state.clear()
    await start_questions(callback.message, state, db, [q.id for q in questions], book_id, title)


@router.message(F.text == "🎲 TASODIFIY TEST")
async def random_quiz(message: Message, state: FSMContext, db: Database, bot, settings: Settings) -> None:
    if not await require_subscription(message, bot, db):
        return
    async with db.session() as session:
        questions = await get_random_questions(session, settings.default_quiz_questions)
    await state.clear()
    await start_questions(message, state, db, [q.id for q in questions], None, "TASODIFIY TEST")


@router.message(F.text == "🔥 BUGUNGI SAVOL")
async def daily_question(message: Message, state: FSMContext, db: Database, bot) -> None:
    if not await require_subscription(message, bot, db):
        return
    raw_id = ""
    async with db.session() as session:
        raw_id = await get_setting(session, "daily_question_id", "")
        question = await session.get(Question, int(raw_id)) if raw_id.isdigit() else None
    if not question or not question.is_active:
        await message.answer("📅 <b>Bugungi savol hali belgilanmagan.</b>", reply_markup=quiz_keyboard())
        return
    await state.clear()
    await start_questions(message, state, db, [question.id], question.book_id, "BUGUNGI SAVOL")


@router.message(F.text == "❌ XATO SAVOLLARIM")
async def wrong_questions(message: Message, state: FSMContext, db: Database, bot) -> None:
    if not await require_subscription(message, bot, db):
        return
    async with db.session() as session:
        user = await session.scalar(select(User).where(User.telegram_id == message.from_user.id))
        questions = await get_wrong_questions(session, user.id, 20) if user else []
    await state.clear()
    await start_questions(message, state, db, [q.id for q in questions], None, "XATO SAVOLLARIM")


@router.callback_query(F.data.startswith("quiz_stop:"))
async def stop_quiz_callback(callback: CallbackQuery, state: FSMContext, db: Database, bot) -> None:
    if not await require_callback_subscription(callback, bot, db):
        await callback.answer()
        return
    try:
        attempt_id = int(callback.data.split(":", 1)[1])
    except ValueError:
        await callback.answer("Test topilmadi.", show_alert=True)
        return
    data = await state.get_data()
    if int(data.get("attempt_id", 0)) != attempt_id:
        await callback.answer("Bu test oynasi faol emas.", show_alert=True)
        return
    async with db.session() as session:
        await finish_attempt(session, attempt_id, completed=False)
    await state.clear()
    await callback.answer("Test to‘xtatildi")
    await callback.message.edit_text("⏹ <b>TEST TO‘XTATILDI</b>\n\n<i>Natija TOP balliga qo‘shilmaydi.</i>", reply_markup=quiz_finish_keyboard())


@router.callback_query(F.data.startswith("quiz_answer:"))
async def answer_question_callback(callback: CallbackQuery, state: FSMContext, db: Database, bot, redis, settings: Settings) -> None:
    if not await require_callback_subscription(callback, bot, db):
        await callback.answer()
        return
    parts = callback.data.split(":")
    if len(parts) != 4 or not parts[1].isdigit() or not parts[2].isdigit() or parts[3] not in {"A", "B", "C", "D"}:
        await callback.answer("Javob noto‘g‘ri.", show_alert=True)
        return
    attempt_id, callback_index, selected = int(parts[1]), int(parts[2]), parts[3]
    data = await state.get_data()
    ids = [int(x) for x in data.get("question_ids", [])]
    current_index = int(data.get("index", 0))
    if int(data.get("attempt_id", 0)) != attempt_id or callback_index != current_index or not ids:
        await callback.answer("Bu savol allaqachon yopilgan.", show_alert=True)
        return
    qid = ids[current_index]
    lock = redis.lock(f"quiz-answer:{callback.from_user.id}:{attempt_id}:{callback_index}", timeout=settings.quiz_answer_lock_seconds, blocking_timeout=0)
    if not await lock.acquire():
        await callback.answer("⏳ Javob qayta ishlanmoqda…")
        return
    try:
        current = await state.get_data()
        if int(current.get("index", 0)) != callback_index:
            await callback.answer("Bu savol allaqachon qabul qilingan.")
            return
        async with db.session() as session:
            q = await session.get(Question, qid)
        if not q:
            await callback.answer("Savol topilmadi.", show_alert=True)
            return
        async with db.session() as session:
            points = int(await get_setting(session, "points_per_correct", str(settings.points_per_correct)))
            outcome = await record_answer(session, attempt_id, qid, selected, points)
            user = await session.scalar(select(User).where(User.telegram_id == callback.from_user.id))
            streak = user.streak if user else 0
        if outcome is None:
            await callback.answer("Bu javob allaqachon qabul qilingan.", show_alert=True)
            return
        correct, _, score, _ = outcome
        await callback.answer("✅ To‘g‘ri!" if correct else "❌ Noto‘g‘ri!")
        await callback.message.edit_text(answer_feedback_text(q, selected, correct, points if correct else 0, streak))
        await asyncio.sleep(0.65)
        next_index = callback_index + 1
        await state.update_data(index=next_index)
        if next_index >= len(ids):
            await _finish(callback.message, state, db, attempt_id)
            return
        async with db.session() as session:
            next_q = await session.get(Question, ids[next_index])
        if not next_q:
            await state.update_data(index=next_index + 1)
            await callback.message.answer("⚠️ Savol topilmadi, keyingisiga o‘tilmoqda.")
            await send_current_question(callback.message, state, db)
            return
        data = await state.get_data()
        await callback.message.edit_text(
            question_text(str(data.get("title", "SAHIFA QUIZ")), next_q, next_index, len(ids)),
            reply_markup=answers_keyboard(attempt_id, next_index),
        )
    finally:
        try:
            await lock.release()
        except Exception:
            pass
