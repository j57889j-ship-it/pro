from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def subscription_keyboard(channels) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for channel in channels:
        builder.row(InlineKeyboardButton(text=f"📢 {channel.title}", url=channel.invite_url))
    builder.row(InlineKeyboardButton(text="✅ OBUNANI TEKSHIRISH", callback_data="sub:check"))
    return builder.as_markup()


def book_list_keyboard(books, *, page: int = 0, has_next: bool = False, back_callback: str = "books:home", item_callback_prefix: str = "book") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for book in books:
        title = book.title if len(book.title) <= 44 else book.title[:41].rstrip() + "…"
        builder.row(InlineKeyboardButton(text=f"📖 {title}", callback_data=f"{item_callback_prefix}:{book.id}"))
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"books:page:{page-1}"))
    if has_next:
        nav.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"books:page:{page+1}"))
    if nav:
        builder.row(*nav)
    builder.row(InlineKeyboardButton(text="⬅️ ORQAGA", callback_data=back_callback))
    return builder.as_markup()


def book_detail_keyboard(book, *, back_callback: str = "books:list:0") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if book.channel_url:
        builder.row(InlineKeyboardButton(text="📖 KITOB POSTI", url=book.channel_url))
    if book.detail_url:
        builder.row(InlineKeyboardButton(text="📚 BATAFSIL MA’LUMOT", url=book.detail_url))
    builder.row(InlineKeyboardButton(text="🧠 TESTNI BOSHLASH", callback_data=f"quizbook:{book.id}"))
    builder.row(InlineKeyboardButton(text="⬅️ KITOBLAR", callback_data=back_callback))
    return builder.as_markup()


def admin_book_detail_keyboard(book) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if book.channel_url:
        builder.row(InlineKeyboardButton(text="📖 KITOB POSTI", url=book.channel_url))
    if book.detail_url:
        builder.row(InlineKeyboardButton(text="📚 BATAFSIL MA’LUMOT", url=book.detail_url))
    builder.row(InlineKeyboardButton(text="⬅️ KITOBLAR", callback_data="adm:books"))
    return builder.as_markup()


def question_book_picker_keyboard(books) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for book in books:
        title = book.title if len(book.title) <= 46 else book.title[:43].rstrip() + "…"
        builder.row(InlineKeyboardButton(text=f"📖 {title}", callback_data=f"admqbook:{book.id}"))
    builder.row(InlineKeyboardButton(text="⬅️ SAVOLLAR BOSHQARUVI", callback_data="adm:questions"))
    return builder.as_markup()


def import_book_picker_keyboard(books) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for book in books:
        title = book.title if len(book.title) <= 46 else book.title[:43].rstrip() + "…"
        builder.row(InlineKeyboardButton(text=f"📖 {title}", callback_data=f"admimportbook:{book.id}"))
    builder.row(InlineKeyboardButton(text="⬅️ KONTENT", callback_data="adm:content"))
    return builder.as_markup()


def admin_books_list_keyboard(books, prefix: str = "admbook") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for book in books:
        title = book.title if len(book.title) <= 46 else book.title[:43].rstrip() + "…"
        builder.row(InlineKeyboardButton(text=f"📖 {title}", callback_data=f"{prefix}:{book.id}"))
    builder.row(InlineKeyboardButton(text="⬅️ KITOBLAR BOSHQARUVI", callback_data="adm:books"))
    return builder.as_markup()


def question_list_keyboard(questions, prefix: str = "admquestion") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for q in questions:
        title = q.text.replace("\n", " ")[:45]
        builder.row(InlineKeyboardButton(text=f"❓ {title}", callback_data=f"{prefix}:{q.id}"))
    builder.row(InlineKeyboardButton(text="⬅️ SAVOLLAR BOSHQARUVI", callback_data="adm:questions"))
    return builder.as_markup()


def channels_list_keyboard(channels, prefix: str = "admchannel") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for channel in channels:
        status = "🟢" if channel.is_active else "🔴"
        builder.row(InlineKeyboardButton(text=f"{status} {channel.title}", callback_data=f"{prefix}:{channel.id}"))
    builder.row(InlineKeyboardButton(text="⬅️ KANALLAR", callback_data="adm:channels"))
    return builder.as_markup()


def reaction_keyboard(enabled: bool, emoji: str) -> InlineKeyboardMarkup:
    status = "🟢 YONIQ" if enabled else "🔴 O‘CHIQ"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{status}", callback_data="reaction:toggle")],
            [InlineKeyboardButton(text=f"❤️ Emoji: {emoji}", callback_data="reaction:presets")],
            [InlineKeyboardButton(text="🧪 TEST REACTION", callback_data="reaction:test")],
            [InlineKeyboardButton(text="⬅️ KANALLAR", callback_data="adm:channels")],
        ]
    )


def reaction_presets_keyboard() -> InlineKeyboardMarkup:
    rows = [["🔥", "❤", "👏", "🎉"], ["🤩", "💯", "🏆", "😍"], ["📚", "⚡", "👀", "🤝"]]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=e, callback_data=f"reaction:preset:{e}") for e in row] for row in rows
        ] + [[InlineKeyboardButton(text="⬅️ REACTION", callback_data="reaction:home")]]
    )


def answers_keyboard(attempt_id: int, index: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🅰️ A", callback_data=f"quiz_answer:{attempt_id}:{index}:A"),
                InlineKeyboardButton(text="🅱️ B", callback_data=f"quiz_answer:{attempt_id}:{index}:B"),
            ],
            [
                InlineKeyboardButton(text="🅲️ C", callback_data=f"quiz_answer:{attempt_id}:{index}:C"),
                InlineKeyboardButton(text="🅳️ D", callback_data=f"quiz_answer:{attempt_id}:{index}:D"),
            ],
            [InlineKeyboardButton(text="⏹️ TESTNI TO‘XTATISH", callback_data=f"quiz_stop:{attempt_id}")],
        ]
    )


def quiz_count_keyboard(book_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="5️⃣ 5 TA", callback_data=f"quiz_count:{book_id}:5"), InlineKeyboardButton(text="🔟 10 TA", callback_data=f"quiz_count:{book_id}:10")],
            [InlineKeyboardButton(text="2️⃣0️⃣ 20 TA", callback_data=f"quiz_count:{book_id}:20"), InlineKeyboardButton(text="3️⃣0️⃣ 30 TA", callback_data=f"quiz_count:{book_id}:30")],
            [InlineKeyboardButton(text="⬅️ TESTLAR", callback_data="quiz:home")],
        ]
    )


def quiz_finish_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🧠 YANA TEST", callback_data="quiz:home")],
            [InlineKeyboardButton(text="📚 KITOBLAR", callback_data="books:home"), InlineKeyboardButton(text="🏠 BOSH MENYU", callback_data="main:home")],
        ]
    )
