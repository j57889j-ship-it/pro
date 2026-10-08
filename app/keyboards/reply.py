from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from app.constants import ADMIN_MENU_BUTTONS, MAIN_MENU_BUTTONS


def _kb(rows, *, placeholder: str | None = None) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=text) for text in row] for row in rows],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder=placeholder,
    )


def main_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    rows = [
        [MAIN_MENU_BUTTONS["books"], MAIN_MENU_BUTTONS["quiz"]],
        [MAIN_MENU_BUTTONS["top"], MAIN_MENU_BUTTONS["profile"]],
        [MAIN_MENU_BUTTONS["help"]],
    ]
    if is_admin:
        rows.append([MAIN_MENU_BUTTONS["admin"]])
    return _kb(rows, placeholder="Bo‘limni tanlang…")


def books_keyboard() -> ReplyKeyboardMarkup:
    return _kb([["🔎 KITOB QIDIRISH"], ["📖 BARCHA KITOBLAR"], ["⬅️ ASOSIY MENYU"]], placeholder="Kitobni tanlang…")


def quiz_keyboard() -> ReplyKeyboardMarkup:
    return _kb(
        [["📖 KITOB BO‘YICHA"], ["🎲 TASODIFIY TEST"], ["🔥 BUGUNGI SAVOL"], ["❌ XATO SAVOLLARIM"], ["⬅️ ASOSIY MENYU"]],
        placeholder="Test turini tanlang…",
    )


def profile_keyboard() -> ReplyKeyboardMarkup:
    return _kb([["📊 STATISTIKA", "❌ XATOLARIM"], ["🔥 STREAK"], ["⬅️ ASOSIY MENYU"]], placeholder="Profil bo‘limi…")


def help_keyboard() -> ReplyKeyboardMarkup:
    return _kb([["📖 BOT HAQIDA"], ["❓ QANDAY ISHLAYDI"], ["💬 ADMIN BILAN BOG‘LANISH"], ["⬅️ ASOSIY MENYU"]], placeholder="Yordam bo‘limi…")


def admin_keyboard() -> ReplyKeyboardMarkup:
    return _kb(
        [
            [ADMIN_MENU_BUTTONS["dashboard"], ADMIN_MENU_BUTTONS["content"]],
            [ADMIN_MENU_BUTTONS["users"], ADMIN_MENU_BUTTONS["channels"]],
            [ADMIN_MENU_BUTTONS["leaderboard"], ADMIN_MENU_BUTTONS["quiz"]],
            [ADMIN_MENU_BUTTONS["settings"], ADMIN_MENU_BUTTONS["back"]],
        ],
        placeholder="Admin bo‘limini tanlang…",
    )


def admin_content_keyboard() -> ReplyKeyboardMarkup:
    return _kb([["📖 KITOBLARNI BOSHQARISH"], ["❓ SAVOLLARNI BOSHQARISH"], ["📥 TXT IMPORT"], ["⬅️ ADMIN PANEL"]], placeholder="Kontent bo‘limi…")


def admin_books_keyboard() -> ReplyKeyboardMarkup:
    return _kb([["➕ KITOB QO‘SHISH"], ["🔎 KITOB TOPISH", "🗑 KITOB O‘CHIRISH"], ["⬅️ KONTENT"]], placeholder="Kitob boshqaruvi…")


def admin_questions_keyboard() -> ReplyKeyboardMarkup:
    return _kb([["➕ SAVOL QO‘SHISH"], ["📋 SAVOLLAR RO‘YXATI"], ["⬅️ KONTENT"]], placeholder="Savol boshqaruvi…")


def admin_users_keyboard() -> ReplyKeyboardMarkup:
    return _kb(
        [["🔎 USER QIDIRISH"], ["📊 USER STATISTIKASI"], ["🚫 BLOK / UNBLOK"], ["🧹 USER STATISTIKASINI TOZALASH"], ["📣 XABAR YUBORISH"], ["⬅️ ADMIN PANEL"]],
        placeholder="User boshqaruvi…",
    )


def admin_channels_keyboard() -> ReplyKeyboardMarkup:
    return _kb([["📡 MAJBURIY KANALLAR"], ["➕ KANAL QO‘SHISH"], ["🗑 KANALNI O‘CHIRISH"], ["❤️ REACTION"], ["⬅️ ADMIN PANEL"]], placeholder="Kanal sozlamasi…")


def admin_leaderboard_keyboard() -> ReplyKeyboardMarkup:
    return _kb([["👑 TOP KITOBXONLAR"], ["⚙️ TOP SOZLAMALARI"], ["🧹 TOP RESET"], ["⬅️ ADMIN PANEL"]], placeholder="Reyting sozlamasi…")


def admin_quiz_keyboard() -> ReplyKeyboardMarkup:
    return _kb([["⚙️ TEST SOZLAMALARI"], ["📊 TEST STATISTIKASI"], ["🧹 NATIJALARNI TOZALASH"], ["⬅️ ADMIN PANEL"]], placeholder="Test boshqaruvi…")


def admin_settings_keyboard() -> ReplyKeyboardMarkup:
    return _kb([["👑 ADMINLAR"], ["⬅️ ADMIN PANEL"]], placeholder="Tizim sozlamasi…")
