from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import select

from app.constants import ROLE_ADMIN, ROLE_MODERATOR
from app.database.models import Admin
from app.database.session import Database
from app.keyboards.reply import admin_settings_keyboard
from app.services.admins import add_admin, remove_admin
from app.states.admin import AdminAddAdminStates, AdminRemoveAdminStates
from app.utils.auth import is_super, require_admin
from app.utils.ui import h

router = Router(name="admin_settings")


@router.message(F.text == "⚙️ SOZLAMALAR")
async def home(message: Message, db: Database) -> None:
    if not await require_admin(message, db):
        return
    await message.answer("⚙️ <b>SOZLAMALAR</b>", reply_markup=admin_settings_keyboard())


@router.message(F.text == "👑 ADMINLAR")
async def admins_list(message: Message, db: Database) -> None:
    if not is_super(await require_admin(message, db)):
        return
    async with db.session() as session:
        admins = list((await session.execute(select(Admin).where(Admin.is_active.is_(True)).order_by(Admin.role, Admin.telegram_id))).scalars().all())
    lines = ["👑 <b>ADMINLAR</b>", "", "<i>Faqat Super Admin qo‘sha yoki o‘chira oladi.</i>", ""]
    for admin in admins:
        role_icon = "👑" if admin.role == "superadmin" else ("🛠" if admin.role == "admin" else "📚")
        lines.append(f"{role_icon} <code>{admin.telegram_id}</code> — <b>{h(admin.role)}</b>")
    lines.append("\n➕ Yangi admin qo‘shish yoki 🗑 mavjud adminni o‘chirish uchun tugmadan foydalaning.")
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ ADMIN QO‘SHISH", callback_data="admins:add")],
        [InlineKeyboardButton(text="🗑 ADMIN O‘CHIRISH", callback_data="admins:remove")],
        [InlineKeyboardButton(text="⬅️ SOZLAMALAR", callback_data="adm:settings")],
    ])
    await message.answer("\n".join(lines), reply_markup=markup)


@router.callback_query(F.data == "admins:add")
async def admins_add_callback(callback, state: FSMContext, db: Database) -> None:
    if not is_super(await require_admin(callback, db)):
        await callback.answer()
        return
    await callback.answer()
    await state.set_state(AdminAddAdminStates.telegram_id)
    await callback.message.answer("🆔 Yangi adminning Telegram ID sini yuboring.\n/cancel bilan bekor qiling.")


@router.callback_query(F.data == "admins:remove")
async def admins_remove_callback(callback, state: FSMContext, db: Database) -> None:
    if not is_super(await require_admin(callback, db)):
        await callback.answer()
        return
    await callback.answer()
    await state.set_state(AdminRemoveAdminStates.telegram_id)
    await callback.message.answer("🗑 O‘chiriladigan admin Telegram ID sini yuboring.\n/cancel bilan bekor qiling.")


@router.message(F.text == "➕ ADMIN QO‘SHISH")
async def add_admin_start(message: Message, state: FSMContext, db: Database) -> None:
    if not is_super(await require_admin(message, db)):
        return
    await state.set_state(AdminAddAdminStates.telegram_id)
    await message.answer("🆔 Yangi adminning Telegram ID sini yuboring.\n/cancel bilan bekor qiling.")


@router.message(AdminAddAdminStates.telegram_id)
async def add_admin_id(message: Message, state: FSMContext) -> None:
    if not (message.text or "").isdigit():
        await message.answer("⚠️ Telegram ID raqam bo‘lishi kerak.")
        return
    await state.update_data(telegram_id=int(message.text))
    await state.set_state(AdminAddAdminStates.role)
    await message.answer("Rolni yuboring: <b>admin</b> yoki <b>moderator</b>")


@router.message(AdminAddAdminStates.role)
async def add_admin_role(message: Message, state: FSMContext, db: Database) -> None:
    if not is_super(await require_admin(message, db)):
        return
    value = (message.text or "").strip().lower()
    if value not in {ROLE_ADMIN, ROLE_MODERATOR}:
        await message.answer("⚠️ Faqat admin yoki moderator.")
        return
    data = await state.get_data()
    async with db.session() as session:
        await add_admin(session, int(data["telegram_id"]), value)
    await state.clear()
    await message.answer("✅ Admin qo‘shildi.", reply_markup=admin_settings_keyboard())


@router.message(F.text == "🗑 ADMIN O‘CHIRISH")
async def remove_admin_start(message: Message, state: FSMContext, db: Database) -> None:
    if not is_super(await require_admin(message, db)):
        return
    await state.set_state(AdminRemoveAdminStates.telegram_id)
    await message.answer("🗑 O‘chiriladigan admin Telegram ID sini yuboring.\n/cancel bilan bekor qiling.")


@router.message(AdminRemoveAdminStates.telegram_id)
async def remove_admin_value(message: Message, state: FSMContext, db: Database) -> None:
    if not is_super(await require_admin(message, db)):
        return
    if not (message.text or "").isdigit():
        await message.answer("⚠️ Telegram ID raqam bo‘lishi kerak.")
        return
    telegram_id = int(message.text)
    async with db.session() as session:
        await remove_admin(session, telegram_id)
    await state.clear()
    await message.answer("✅ Admin o‘chirildi.", reply_markup=admin_settings_keyboard())
