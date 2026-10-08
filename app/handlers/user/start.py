from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from app.database.session import Database
from app.keyboards.inline import subscription_keyboard
from app.keyboards.reply import main_keyboard
from app.services.admins import is_admin
from app.services.subscriptions import active_channels, is_subscribed_to_all
from app.utils.ui import menu_text

router = Router(name="user_start")


@router.message(CommandStart())
async def start(message: Message, db: Database, bot) -> None:
    async with db.session() as session:
        admin = await is_admin(session, message.from_user.id)
        if not admin and not await is_subscribed_to_all(session, bot, message.from_user.id):
            channels = await active_channels(session)
            await message.answer(
                "📚 <b>SAHIFA QUIZ</b>\n\nBotdan foydalanish uchun quyidagi kanallarga obuna bo‘ling.",
                reply_markup=subscription_keyboard(channels),
            )
            return
    await message.answer(menu_text(), reply_markup=main_keyboard(admin))


@router.callback_query(lambda c: c.data == "sub:check")
async def check_subscription(callback: CallbackQuery, db: Database, bot) -> None:
    async with db.session() as session:
        admin = await is_admin(session, callback.from_user.id)
        ok = admin or await is_subscribed_to_all(session, bot, callback.from_user.id)
        channels = await active_channels(session)
    if not ok:
        await callback.answer("Hali barcha kanallarga obuna bo‘lmagansiz.", show_alert=True)
        if callback.message:
            await callback.message.edit_reply_markup(reply_markup=subscription_keyboard(channels))
        return
    await callback.answer("Obuna tasdiqlandi ✅")
    if callback.message:
        await callback.message.answer(menu_text(), reply_markup=main_keyboard(admin))
