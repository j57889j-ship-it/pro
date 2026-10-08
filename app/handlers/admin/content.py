from __future__ import annotations

from io import BytesIO

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError

from app.config import Settings
from app.database.models import Book, Question
from app.database.session import Database
from app.keyboards.inline import (
    admin_book_detail_keyboard,
    admin_books_list_keyboard,
    import_book_picker_keyboard,
    question_book_picker_keyboard,
    question_list_keyboard,
)
from app.keyboards.reply import admin_books_keyboard, admin_content_keyboard, admin_questions_keyboard
from app.services.books import delete_book, normalize_text, search_books
from app.states.admin import AdminBookStates, AdminImportStates, AdminQuestionStates
from app.utils.auth import can_manage_content, require_admin
from app.utils.ui import h
from app.utils.txt_import import parse_txt

router = Router(name="admin_content")


@router.message(F.text == "📚 KONTENT")
async def content_home(message: Message, db: Database) -> None:
    if not can_manage_content(await require_admin(message, db)):
        return
    await message.answer("📚 <b>KONTENT</b>\n\nKitoblar, savollar va TXT import shu bo‘limda.", reply_markup=admin_content_keyboard())


@router.message(F.text == "📖 KITOBLARNI BOSHQARISH")
async def books_manage(message: Message, db: Database) -> None:
    if not can_manage_content(await require_admin(message, db)):
        return
    await message.answer("📖 <b>KITOBLARNI BOSHQARISH</b>", reply_markup=admin_books_keyboard())


@router.message(F.text == "➕ KITOB QO‘SHISH")
async def add_book_start(message: Message, state: FSMContext, db: Database) -> None:
    if not can_manage_content(await require_admin(message, db)):
        return
    await state.set_state(AdminBookStates.title)
    await message.answer("1/6 📖 <b>Kitob nomi</b>ni yuboring.")


@router.message(AdminBookStates.title)
async def add_book_title(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    if len(value) < 2:
        await message.answer("⚠️ Kitob nomi juda qisqa.")
        return
    await state.update_data(title=value)
    await state.set_state(AdminBookStates.author)
    await message.answer("2/6 ✍️ <b>Muallif</b>ni yuboring.")


@router.message(AdminBookStates.author)
async def add_book_author(message: Message, state: FSMContext) -> None:
    await state.update_data(author=(message.text or "").strip())
    await state.set_state(AdminBookStates.description)
    await message.answer("3/6 📝 <b>Qisqa ma’lumot</b>ni yuboring.")


@router.message(AdminBookStates.description)
async def add_book_description(message: Message, state: FSMContext) -> None:
    await state.update_data(description=(message.text or "").strip())
    await state.set_state(AdminBookStates.channel_url)
    await message.answer("4/6 🔗 <b>Asosiy kanal posti havolasi</b>. Kerak bo‘lmasa `-` yuboring.")


@router.message(AdminBookStates.channel_url)
async def add_book_channel_url(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    await state.update_data(channel_url=None if value == "-" else value)
    await state.set_state(AdminBookStates.detail_url)
    await message.answer("5/6 🔗 <b>Batafsil ma’lumot havolasi</b>. Kerak bo‘lmasa `-` yuboring.")


@router.message(AdminBookStates.detail_url)
async def add_book_detail_url(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    await state.update_data(detail_url=None if value == "-" else value)
    await state.set_state(AdminBookStates.cover)
    await message.answer("6/6 🖼 <b>Muqova rasmini</b> yuboring yoki O‘TKAZISH deb yozing.")


@router.message(AdminBookStates.cover)
async def add_book_cover(message: Message, state: FSMContext, db: Database) -> None:
    data = await state.get_data()
    cover_file_id = message.photo[-1].file_id if message.photo else None
    if not message.photo and (message.text or "").strip().upper() not in {"O‘TKAZISH", "SKIP", "-"}:
        await message.answer("🖼 Rasm yuboring yoki O‘TKAZISH deb yozing.")
        return
    async with db.session() as session:
        duplicate = await session.scalar(select(Book).where(Book.title.ilike(data["title"])))
        if duplicate:
            await state.clear()
            await message.answer("⚠️ Bu nomdagi kitob allaqachon mavjud.", reply_markup=admin_books_keyboard())
            return
        session.add(Book(
            title=data["title"], author=data["author"], description=data["description"],
            channel_url=data.get("channel_url"), detail_url=data.get("detail_url"),
            cover_file_id=cover_file_id, is_active=True,
        ))
        await session.commit()
    await state.clear()
    await message.answer("✅ <b>Kitob muvaffaqiyatli qo‘shildi.</b>", reply_markup=admin_books_keyboard())


@router.message(F.text == "🔎 KITOB TOPISH")
async def find_book(message: Message, state: FSMContext, db: Database) -> None:
    if not can_manage_content(await require_admin(message, db)):
        return
    await state.set_state(AdminBookStates.find)
    await message.answer("🔎 Kitob nomini yoki muallifini yuboring.")


@router.message(AdminBookStates.find)
async def find_book_value(message: Message, state: FSMContext, db: Database) -> None:
    async with db.session() as session:
        books = await search_books(session, (message.text or "").strip(), limit=20)
    await state.clear()
    if not books:
        await message.answer("📭 Kitob topilmadi.", reply_markup=admin_books_keyboard())
        return
    await message.answer("📚 <b>TOPILDI</b>", reply_markup=admin_books_list_keyboard(books))


@router.callback_query(F.data.startswith("admbook:"))
async def admin_book_details(callback: CallbackQuery, db: Database) -> None:
    if not can_manage_content(await require_admin(callback, db)):
        await callback.answer()
        return
    try:
        book_id = int(callback.data.split(":", 1)[1])
    except ValueError:
        await callback.answer("Kitob ID noto‘g‘ri.", show_alert=True)
        return
    async with db.session() as session:
        book = await session.get(Book, book_id)
        if not book:
            await callback.answer("Kitob topilmadi.", show_alert=True)
            return
        qcount = int(await session.scalar(select(func.count(Question.id)).where(Question.book_id == book.id, Question.is_active.is_(True))) or 0)
    await callback.answer()
    count_text = str(qcount)
    text = (
        f"📖 <b>{h(book.title)}</b>\n\n"
        f"✍️ <i>{h(book.author or 'Noma’lum')}</i>\n\n"
        f"<blockquote>{h(book.description or 'Ma’lumot kiritilmagan.')}</blockquote>\n\n"
        f"🧠 Faol savollar: <b>{count_text}</b>"
    )
    await callback.message.answer(text, reply_markup=admin_book_detail_keyboard(book))


@router.message(F.text == "🗑 KITOB O‘CHIRISH")
async def delete_book_start(message: Message, state: FSMContext, db: Database) -> None:
    if not can_manage_content(await require_admin(message, db)):
        return
    await state.set_state(AdminBookStates.delete)
    await message.answer("🗑 O‘chiriladigan kitob nomini yuboring.")


@router.message(AdminBookStates.delete)
async def delete_book_value(message: Message, state: FSMContext, db: Database) -> None:
    async with db.session() as session:
        books = await search_books(session, (message.text or "").strip(), limit=10)
        if not books:
            await message.answer("📭 Kitob topilmadi.")
            return
        if len(books) > 1:
            await state.clear()
            await message.answer("Bir nechta kitob topildi. Keraklisini tanlang.", reply_markup=admin_books_list_keyboard(books, "deletebook"))
            return
        title = books[0].title
        await delete_book(session, books[0].id)
    await state.clear()
    await message.answer(f"✅ <b>{h(title)}</b> o‘chirildi.", reply_markup=admin_books_keyboard())


@router.callback_query(F.data.startswith("deletebook:"))
async def delete_book_callback(callback: CallbackQuery, db: Database) -> None:
    if not can_manage_content(await require_admin(callback, db)):
        await callback.answer()
        return
    book_id = int(callback.data.split(":", 1)[1])
    async with db.session() as session:
        book = await session.get(Book, book_id)
        if not book:
            await callback.answer("Kitob topilmadi.", show_alert=True)
            return
        title = book.title
        await delete_book(session, book_id)
    await callback.answer("O‘chirildi ✅")
    await callback.message.answer(f"✅ <b>{h(title)}</b> o‘chirildi.", reply_markup=admin_books_keyboard())


@router.message(F.text == "❓ SAVOLLARNI BOSHQARISH")
async def questions_manage(message: Message, db: Database) -> None:
    if not can_manage_content(await require_admin(message, db)):
        return
    await message.answer("❓ <b>SAVOLLARNI BOSHQARISH</b>", reply_markup=admin_questions_keyboard())


@router.message(F.text == "➕ SAVOL QO‘SHISH")
async def add_question_start(message: Message, state: FSMContext, db: Database) -> None:
    if not can_manage_content(await require_admin(message, db)):
        return
    async with db.session() as session:
        books = list((await session.execute(select(Book).where(Book.is_active.is_(True)).order_by(Book.title).limit(50))).scalars().all())
    if not books:
        await message.answer("📭 <b>Avval kitob qo‘shing.</b>")
        return
    await state.set_state(AdminQuestionStates.book)
    await message.answer("📖 <b>SAVOL UCHUN KITOBNI TANLANG</b>", reply_markup=question_book_picker_keyboard(books))


@router.callback_query(AdminQuestionStates.book, F.data.startswith("admqbook:"))
async def add_question_book(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    book_id = int(callback.data.split(":", 1)[1])
    async with db.session() as session:
        book = await session.get(Book, book_id)
    if not book or not book.is_active:
        await callback.answer("Kitob topilmadi.", show_alert=True)
        return
    await state.update_data(book_id=book.id)
    await state.set_state(AdminQuestionStates.text)
    await callback.answer()
    await callback.message.answer(f"❓ <b>{h(book.title)}</b> uchun savol matnini yuboring.")


@router.message(AdminQuestionStates.text)
async def add_question_text(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    if len(value) < 3:
        await message.answer("⚠️ Savol juda qisqa.")
        return
    await state.update_data(text=value)
    await state.set_state(AdminQuestionStates.option_a)
    await message.answer("🅰️ A variantni yuboring.")


@router.message(AdminQuestionStates.option_a)
async def add_question_a(message: Message, state: FSMContext) -> None:
    await state.update_data(option_a=(message.text or "").strip())
    await state.set_state(AdminQuestionStates.option_b)
    await message.answer("🅱️ B variantni yuboring.")


@router.message(AdminQuestionStates.option_b)
async def add_question_b(message: Message, state: FSMContext) -> None:
    await state.update_data(option_b=(message.text or "").strip())
    await state.set_state(AdminQuestionStates.option_c)
    await message.answer("©️ C variantni yuboring.")


@router.message(AdminQuestionStates.option_c)
async def add_question_c(message: Message, state: FSMContext) -> None:
    await state.update_data(option_c=(message.text or "").strip())
    await state.set_state(AdminQuestionStates.option_d)
    await message.answer("🆎 D variantni yuboring.")


@router.message(AdminQuestionStates.option_d)
async def add_question_d(message: Message, state: FSMContext) -> None:
    await state.update_data(option_d=(message.text or "").strip())
    await state.set_state(AdminQuestionStates.correct)
    await message.answer("✅ To‘g‘ri javob harfini yuboring: A / B / C / D")


@router.message(AdminQuestionStates.correct)
async def add_question_correct(message: Message, state: FSMContext, db: Database) -> None:
    value = (message.text or "").strip().upper()
    if value not in {"A", "B", "C", "D"}:
        await message.answer("⚠️ Faqat A, B, C yoki D.")
        return
    data = await state.get_data()
    async with db.session() as session:
        duplicate = await session.scalar(
            select(Question).where(Question.book_id == int(data["book_id"]), Question.normalized_text == normalize_text(data["text"]))
        )
        if duplicate:
            await state.clear()
            await message.answer("🔁 Bu savol shu kitobda allaqachon mavjud.", reply_markup=admin_questions_keyboard())
            return
        session.add(Question(
            book_id=int(data["book_id"]), text=data["text"], normalized_text=normalize_text(data["text"]),
            option_a=data["option_a"], option_b=data["option_b"], option_c=data["option_c"], option_d=data["option_d"],
            correct_option=value, explanation="", is_active=True,
        ))
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            await message.answer("❌ Savol saqlanmadi: duplicate yoki DB xatosi.")
            return
    await state.clear()
    await message.answer("✅ <b>Savol qo‘shildi.</b>", reply_markup=admin_questions_keyboard())


@router.message(F.text == "📋 SAVOLLAR RO‘YXATI")
async def question_list(message: Message, db: Database) -> None:
    if not can_manage_content(await require_admin(message, db)):
        return
    async with db.session() as session:
        questions = list((await session.execute(select(Question).where(Question.is_active.is_(True)).order_by(Question.id.desc()).limit(40))).scalars().all())
    await message.answer("📋 <b>SAVOLLAR</b>", reply_markup=question_list_keyboard(questions))


@router.message(F.text == "📥 TXT IMPORT")
async def txt_import_start(message: Message, state: FSMContext, db: Database) -> None:
    if not can_manage_content(await require_admin(message, db)):
        return
    async with db.session() as session:
        books = list((await session.execute(select(Book).where(Book.is_active.is_(True)).order_by(Book.title).limit(100))).scalars().all())
    if not books:
        await message.answer("📭 <b>Avval kitob qo‘shing.</b>")
        return
    await state.set_state(AdminImportStates.book)
    await message.answer(
        "📥 <b>TXT IMPORT</b>\n\nKitobni tanlang, keyin TXT fayl yuboring. Maksimum 100 ta savol.\n\n"
        "<code>1. Savol?\nA: Variant A\nB: Variant B\nC: Variant C\nD: Variant D\nANSWER: B</code>",
        reply_markup=import_book_picker_keyboard(books),
    )


@router.callback_query(AdminImportStates.book, F.data.startswith("admimportbook:"))
async def import_book(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    book_id = int(callback.data.split(":", 1)[1])
    async with db.session() as session:
        book = await session.get(Book, book_id)
    if not book or not book.is_active:
        await callback.answer("Kitob topilmadi.", show_alert=True)
        return
    await state.update_data(book_id=book.id)
    await state.set_state(AdminImportStates.file)
    await callback.answer()
    await callback.message.answer(
        f"📖 <b>{h(book.title)}</b>\n\n📄 TXT faylni yuboring. Maksimum 100 ta savol.\n\n"
        "<code>1. Savol?\nA: Variant A\nB: Variant B\nC: Variant C\nD: Variant D\nANSWER: B</code>"
    )


@router.message(AdminImportStates.file, F.document)
async def import_file(message: Message, state: FSMContext, db: Database, bot, settings: Settings) -> None:
    file_name = message.document.file_name or ""
    if not file_name.lower().endswith(".txt"):
        await message.answer("⚠️ Faqat .txt fayl yuboring.")
        return
    if (message.document.file_size or 0) > settings.max_txt_bytes:
        await message.answer(f"⚠️ Fayl hajmi juda katta. Maksimum {settings.max_txt_bytes // 1000} KB.")
        return
    data = await state.get_data()
    file_info = await bot.get_file(message.document.file_id)
    buffer = await bot.download_file(file_info.file_path)
    raw = buffer.read()
    content = None
    for encoding in ("utf-8-sig", "utf-8", "cp1251", "latin-1"):
        try:
            content = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if content is None:
        await message.answer("❌ TXT fayl kodlanishini o‘qib bo‘lmadi.")
        return

    parsed, errors, duplicates = parse_txt(content, settings.max_questions_per_import)
    if not parsed and errors:
        await message.answer("❌ <b>Import amalga oshmadi.</b>\n\n" + "\n".join(errors[:20]))
        return

    added = 0
    skipped_existing = 0
    async with db.session() as session:
        book = await session.get(Book, int(data["book_id"]))
        if not book:
            await state.clear()
            await message.answer("📭 Kitob topilmadi.", reply_markup=admin_content_keyboard())
            return
        existing_texts = set(
            (await session.execute(select(Question.normalized_text).where(Question.book_id == book.id))).scalars().all()
        )
        for item in parsed:
            normalized = normalize_text(item.text)
            if normalized in existing_texts:
                skipped_existing += 1
                continue
            session.add(
                Question(
                    book_id=book.id,
                    text=item.text,
                    normalized_text=normalized,
                    option_a=item.option_a,
                    option_b=item.option_b,
                    option_c=item.option_c,
                    option_d=item.option_d,
                    correct_option=item.correct_option,
                    explanation="",
                    is_active=True,
                )
            )
            existing_texts.add(normalized)
            added += 1
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            await state.clear()
            await message.answer("❌ Import paytida DB duplicate xatosi yuz berdi. Faylni qayta yuborishdan oldin import natijasini tekshiring.")
            return

    await state.clear()
    lines = [
        "📥 <b>IMPORT YAKUNLANDI</b>",
        "",
        f"📖 Kitob: <b>{h(book.title)}</b>",
        f"✅ Yangi: <b>{added}</b>",
        f"🔁 Bazadagi duplicate: <b>{skipped_existing}</b>",
        f"⚠️ Format xatolari: <b>{len(errors)}</b>",
        f"📄 Fayl duplicate: <b>{duplicates}</b>",
    ]
    if errors:
        lines += ["", "<b>Birinchi xatolar:</b>"] + [f"• {h(error)}" for error in errors[:12]]
    await message.answer("\n".join(lines), reply_markup=admin_content_keyboard())


@router.callback_query(F.data.startswith("admquestion:"))
async def admin_question_details(callback: CallbackQuery, db: Database) -> None:
    if not can_manage_content(await require_admin(callback, db)):
        await callback.answer()
        return
    qid = int(callback.data.split(":", 1)[1])
    async with db.session() as session:
        q = await session.get(Question, qid)
    if not q:
        await callback.answer("Savol topilmadi.", show_alert=True)
        return
    await callback.answer()
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🗑 O‘CHIRISH", callback_data=f"deletequestion:{qid}")]])
    await callback.message.answer(
        f"❓ <b>{h(q.text)}</b>\n\n"
        f"🅰️ {h(q.option_a)}\n"
        f"🅱️ {h(q.option_b)}\n"
        f"©️ {h(q.option_c)}\n"
        f"🆎 {h(q.option_d)}\n\n"
        f"✅ To‘g‘ri javob: <b>{h(q.correct_option)}</b>",
        reply_markup=kb,
    )


@router.callback_query(F.data.startswith("deletequestion:"))
async def delete_question(callback: CallbackQuery, db: Database) -> None:
    if not can_manage_content(await require_admin(callback, db)):
        await callback.answer()
        return
    qid = int(callback.data.split(":", 1)[1])
    async with db.session() as session:
        q = await session.get(Question, qid)
        if not q:
            await callback.answer("Savol topilmadi.", show_alert=True)
            return
        q.is_active = False
        await session.commit()
    await callback.answer("Savol o‘chirildi ✅")
