from __future__ import annotations

from aiogram import F, Router
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from app.config import Settings
from app.constants import SUPPORTED_REACTION_EMOJIS
from app.database.models import MandatoryChannel
from app.database.session import Database
from app.keyboards.inline import channels_list_keyboard, reaction_keyboard, reaction_presets_keyboard
from app.keyboards.reply import admin_channels_keyboard
from app.services.settings import get_setting, set_setting
from app.services.subscriptions import active_channels
from app.states.admin import AdminChannelStates, AdminReactionStates
from app.utils.auth import is_super, require_admin
from app.utils.ui import h

router = Router(name="admin_channels")


def normalize_reaction(value: str) -> str:
    return {"❤️": "❤", "♥️": "❤"}.get(value.strip(), value.strip())


@router.message(F.text == "📢 KANALLAR")
async def channels_home(message: Message, db: Database) -> None:
    if not await require_admin(message, db):
        return
    await message.answer("📢 <b>KANALLAR</b>", reply_markup=admin_channels_keyboard())


@router.message(F.text == "📡 MAJBURIY KANALLAR")
async def mandatory_list(message: Message, db: Database) -> None:
    if not await require_admin(message, db):
        return
    async with db.session() as session:
        channels = await active_channels(session)
    if not channels:
        await message.answer("📭 Majburiy kanal qo‘shilmagan.", reply_markup=admin_channels_keyboard())
        return
    await message.answer("📡 <b>MAJBURIY KANALLAR</b>", reply_markup=channels_list_keyboard(channels))


@router.message(F.text == "➕ KANAL QO‘SHISH")
async def add_channel_start(message: Message, state: FSMContext, db: Database) -> None:
    if not await require_admin(message, db):
        return
    await state.set_state(AdminChannelStates.title)
    await message.answer("1/3 📢 Kanal nomini yuboring.")


@router.message(AdminChannelStates.title)
async def add_channel_title(message: Message, state: FSMContext) -> None:
    await state.update_data(title=(message.text or "").strip())
    await state.set_state(AdminChannelStates.chat_id)
    await message.answer("2/3 🆔 Kanal Chat ID sini yuboring. Masalan: -1001234567890")


@router.message(AdminChannelStates.chat_id)
async def add_channel_chat_id(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    try:
        chat_id = int(value)
    except ValueError:
        await message.answer("⚠️ Chat ID raqam bo‘lishi kerak.")
        return
    await state.update_data(chat_id=chat_id)
    await state.set_state(AdminChannelStates.invite_url)
    await message.answer("3/3 🔗 Kanal havolasini yuboring.")


@router.message(AdminChannelStates.invite_url)
async def add_channel_url(message: Message, state: FSMContext, db: Database, bot) -> None:
    data = await state.get_data()
    invite_url = (message.text or "").strip()
    chat_id = int(data["chat_id"])
    try:
        chat = await bot.get_chat(chat_id)
        me = await bot.get_me()
        member = await bot.get_chat_member(chat_id, me.id)
        if member.status not in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR}:
            await message.answer("⚠️ Bot bu kanalda administrator bo‘lishi kerak.")
            return
        if chat.type != ChatType.CHANNEL:
            await message.answer("⚠️ Faqat Telegram kanalini qo‘shing.")
            return
    except Exception as exc:
        await message.answer("⚠️ Kanalni tekshirib bo‘lmadi. Chat ID va bot admin huquqlarini tekshiring.")
        return
    async with db.session() as session:
        existing = await session.scalar(select(MandatoryChannel).where(MandatoryChannel.chat_id == chat_id))
        if existing:
            existing.title = data["title"]
            existing.invite_url = invite_url
            existing.is_active = True
        else:
            session.add(MandatoryChannel(title=data["title"], chat_id=int(data["chat_id"]), invite_url=invite_url, is_active=True))
        await session.commit()
    await state.clear()
    await message.answer("✅ Majburiy kanal qo‘shildi.", reply_markup=admin_channels_keyboard())


@router.callback_query(F.data.startswith("admchannel:"))
async def channel_details(callback: CallbackQuery, db: Database) -> None:
    if not await require_admin(callback, db):
        await callback.answer()
        return
    channel_id = int(callback.data.split(":", 1)[1])
    async with db.session() as session:
        channel = await session.get(MandatoryChannel, channel_id)
    if not channel:
        await callback.answer("Kanal topilmadi.", show_alert=True)
        return
    await callback.answer()
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑 O‘CHIRISH", callback_data=f"deletechannel:{channel.id}")],
            [InlineKeyboardButton(text="⬅️ KANALLAR", callback_data="adm:channels")],
        ]
    )
    await callback.message.answer(
        f"📢 <b>{h(channel.title)}</b>\n\n🆔 <code>{channel.chat_id}</code>\n🔗 {h(channel.invite_url)}",
        reply_markup=kb,
    )


@router.callback_query(F.data.startswith("deletechannel:"))
async def delete_channel(callback: CallbackQuery, db: Database) -> None:
    if not await require_admin(callback, db):
        await callback.answer()
        return
    channel_id = int(callback.data.split(":", 1)[1])
    async with db.session() as session:
        channel = await session.get(MandatoryChannel, channel_id)
        if not channel:
            await callback.answer("Kanal topilmadi.", show_alert=True)
            return
        channel.is_active = False
        await session.commit()
    await callback.answer("Kanal o‘chirildi ✅")


@router.message(F.text == "🗑 KANALNI O‘CHIRISH")
async def delete_channel_start(message: Message, state: FSMContext, db: Database) -> None:
    if not is_super(await require_admin(message, db)):
        return
    await state.set_state(AdminChannelStates.delete)
    await message.answer("🗑 O‘chiriladigan kanal Chat ID sini yuboring.")


@router.message(AdminChannelStates.delete)
async def delete_channel_value(message: Message, state: FSMContext, db: Database) -> None:
    try:
        chat_id = int((message.text or "").strip())
    except ValueError:
        await message.answer("⚠️ Chat ID raqam bo‘lishi kerak.")
        return
    async with db.session() as session:
        channel = await session.scalar(select(MandatoryChannel).where(MandatoryChannel.chat_id == chat_id))
        if not channel:
            await message.answer("📭 Kanal topilmadi.")
            return
        channel.is_active = False
        await session.commit()
    await state.clear()
    await message.answer("✅ Kanal o‘chirildi.", reply_markup=admin_channels_keyboard())


@router.message(F.text == "❤️ REACTION")
async def reaction_home(message: Message, db: Database) -> None:
    if not await require_admin(message, db):
        return
    async with db.session() as session:
        enabled = await get_setting(session, "reaction_enabled", "1") == "1"
        emoji = await get_setting(session, "reaction_emoji", "🔥")
        last_post = await get_setting(session, "last_channel_post_id", "")
        last_error = await get_setting(session, "reaction_last_error", "")
    await message.answer(
        "❤️ <b>KANAL REACTION</b>\n\n"
        f"Holat: <b>{'🟢 ON' if enabled else '🔴 OFF'}</b>\n"
        f"Emoji: <b>{h(emoji)}</b>\n"
        f"Oxirgi post: <code>{h(last_post or 'yo‘q')}</code>\n"
        f"Holat: {'✅ Muammo yo‘q' if not last_error else '⚠️ Xato mavjud'}\n"
        f"{('<i>' + h(last_error) + '</i>') if last_error else ''}",
        reply_markup=reaction_keyboard(enabled, emoji),
    )


@router.callback_query(F.data == "reaction:home")
async def reaction_home_callback(callback: CallbackQuery, db: Database) -> None:
    if not await require_admin(callback, db):
        await callback.answer()
        return
    await callback.answer()
    async with db.session() as session:
        enabled = await get_setting(session, "reaction_enabled", "1") == "1"
        emoji = await get_setting(session, "reaction_emoji", "🔥")
    await callback.message.edit_text("❤️ <b>KANAL REACTION</b>\n\nEmoji va avtomatik reaction holatini boshqaring.", reply_markup=reaction_keyboard(enabled, emoji))


@router.callback_query(F.data == "reaction:toggle")
async def reaction_toggle(callback: CallbackQuery, db: Database) -> None:
    if not await require_admin(callback, db):
        await callback.answer()
        return
    async with db.session() as session:
        current = await get_setting(session, "reaction_enabled", "1")
        await set_setting(session, "reaction_enabled", "0" if current == "1" else "1")
        enabled = current != "1"
        emoji = await get_setting(session, "reaction_emoji", "🔥")
    await callback.answer("ON" if enabled else "OFF")
    await callback.message.edit_reply_markup(reply_markup=reaction_keyboard(enabled, emoji))


@router.callback_query(F.data == "reaction:presets")
async def reaction_presets(callback: CallbackQuery, db: Database) -> None:
    if not await require_admin(callback, db):
        await callback.answer()
        return
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=reaction_presets_keyboard())


@router.callback_query(F.data.startswith("reaction:preset:"))
async def reaction_preset(callback: CallbackQuery, db: Database) -> None:
    if not await require_admin(callback, db):
        await callback.answer()
        return
    emoji = normalize_reaction(callback.data.split(":", 2)[2])
    if emoji not in SUPPORTED_REACTION_EMOJIS:
        await callback.answer("Bu emoji reaction sifatida qo‘llab-quvvatlanmaydi.", show_alert=True)
        return
    async with db.session() as session:
        await set_setting(session, "reaction_emoji", emoji)
        enabled = await get_setting(session, "reaction_enabled", "1") == "1"
    await callback.answer(f"Reaction: {emoji}")
    await callback.message.edit_reply_markup(reply_markup=reaction_keyboard(enabled, emoji))


@router.callback_query(F.data == "reaction:test")
async def reaction_test(callback: CallbackQuery, db: Database, bot, settings: Settings) -> None:
    if not await require_admin(callback, db):
        await callback.answer()
        return
    if not settings.target_channel_id:
        await callback.answer("TARGET_CHANNEL_ID sozlanmagan.", show_alert=True)
        return
    async with db.session() as session:
        enabled = await get_setting(session, "reaction_enabled", "1") == "1"
        emoji = normalize_reaction(await get_setting(session, "reaction_emoji", "🔥"))
        raw_post = await get_setting(session, "last_channel_post_id", "")
    if not enabled:
        await callback.answer("Reaction OFF.", show_alert=True)
        return
    if not raw_post.isdigit():
        await callback.answer("Hali channel post olinmagan. Kanalga yangi post yuboring.", show_alert=True)
        return
    if emoji not in SUPPORTED_REACTION_EMOJIS:
        await callback.answer("Emoji qo‘llab-quvvatlanmaydi.", show_alert=True)
        return
    try:
        chat = await bot.get_chat(settings.target_channel_id)
        if chat.available_reactions:
            allowed = {getattr(item, "emoji", None) for item in chat.available_reactions}
            if emoji not in allowed:
                await callback.answer("Bu emoji target kanalda ruxsat etilmagan.", show_alert=True)
                return
        member = me = await bot.get_me()
        member = await bot.get_chat_member(settings.target_channel_id, me.id)
        if member.status not in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR}:
            await callback.answer("Bot target kanalda admin bo‘lishi kerak.", show_alert=True)
            return
        from aiogram.types import ReactionTypeEmoji
        await bot.set_message_reaction(chat_id=settings.target_channel_id, message_id=int(raw_post), reaction=[ReactionTypeEmoji(type="emoji", emoji=emoji)], is_big=True)
    except Exception as exc:
        await callback.answer("Reaction yuborilmadi. Render logini tekshiring.", show_alert=True)
        return
    await callback.answer("✅ Test reaction yuborildi!")
