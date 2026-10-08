from __future__ import annotations

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand, ErrorEvent, Update
from fastapi import FastAPI, Header, HTTPException, Request, Response
from redis.asyncio import Redis
from sqlalchemy import text

from app.config import Settings, get_settings
from app.constants import WEBHOOK_UPDATE_TYPES
from app.database.session import Database
from app.handlers.admin import build_router as build_admin_router
from app.handlers.channel_reactions import router as channel_reactions_router
from app.handlers.user import build_router as build_user_router
from app.middlewares.admin_only import AdminOnlyMiddleware
from app.middlewares.resources import ResourcesMiddleware
from app.middlewares.user_context import UserContextMiddleware
from app.services.admins import ensure_super_admins
from app.services.settings import ensure_default_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("sahifa_quiz")

settings: Settings = get_settings()
db = Database(settings.database_url)
redis = Redis.from_url(settings.redis_url, decode_responses=False)
storage = RedisStorage(redis=redis, state_ttl=60 * 60 * 8, data_ttl=60 * 60 * 8)
bot = Bot(
    token=settings.bot_token,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML,
        link_preview_is_disabled=True,
    ),
)
dp = Dispatcher(storage=storage)

resources = ResourcesMiddleware(db, settings, redis)
user_context = UserContextMiddleware(db, settings, redis)
admin_only = AdminOnlyMiddleware(db)

user_router = build_user_router()
admin_router = build_admin_router()

# Resource injection is attached to every incoming event type we use.
user_router.message.outer_middleware(resources)
user_router.callback_query.outer_middleware(resources)
user_router.message.outer_middleware(user_context)
user_router.callback_query.outer_middleware(user_context)

admin_router.message.outer_middleware(resources)
admin_router.callback_query.outer_middleware(resources)
admin_router.message.outer_middleware(user_context)
admin_router.callback_query.outer_middleware(user_context)
admin_router.message.outer_middleware(admin_only)
admin_router.callback_query.outer_middleware(admin_only)

channel_reactions_router.channel_post.outer_middleware(resources)

# Admin callbacks have their own namespaces; registering admin first also prevents accidental shadowing.
dp.include_router(admin_router)
dp.include_router(user_router)
dp.include_router(channel_reactions_router)


@dp.errors()
async def global_error_handler(event: ErrorEvent):
    logger.error("Unhandled Telegram update error: %s", event.exception, exc_info=event.exception)
    return False


async def prepare() -> None:
    async with db.session() as session:
        await ensure_super_admins(session, settings)
        await ensure_default_settings(session)

    commands = [
        BotCommand(command="start", description="Sahifa Quizni boshlash"),
        BotCommand(command="help", description="Yordam"),
        BotCommand(command="cancel", description="Joriy amalni bekor qilish"),
    ]
    try:
        await bot.set_my_commands(commands)
        await bot.set_my_short_description("📚 Kitoblar • 🧠 Testlar • 🏆 TOP")
        await bot.set_my_description(
            "📚 Kitobxonlar uchun maxsus quiz bot.\n\n"
            "📖 Kitoblarni toping\n"
            "🧠 Asarlar bo‘yicha test ishlang\n"
            "🏆 TOP kitobxonlar safidan joy oling\n"
            "👤 Shaxsiy natijalaringizni kuzating"
        )
    except Exception as exc:
        logger.warning("Bot profil sozlamalari bajarilmadi: %s", exc)


def public_base_url() -> str:
    value = (settings.webhook_url or os.getenv("RENDER_EXTERNAL_HOSTNAME", "")).strip()
    if not value:
        return ""
    if not value.startswith("http"):
        value = f"https://{value}"
    value = value.rstrip("/")
    if value.endswith("/telegram/webhook"):
        value = value[: -len("/telegram/webhook")]
    return value


async def configure_webhook() -> None:
    base = public_base_url()
    if not base:
        return
    webhook = f"{base}/telegram/webhook"
    # Always send allowed_updates. Telegram preserves the previous list when this field is omitted,
    # which was the source of the old channel_post/reaction failure.
    await bot.set_webhook(
        url=webhook,
        secret_token=settings.webhook_secret,
        drop_pending_updates=False,
        max_connections=settings.webhook_max_connections,
        allowed_updates=WEBHOOK_UPDATE_TYPES,
    )
    info = await bot.get_webhook_info()
    logger.info(
        "Webhook configured url=%s allowed=%s pending=%s last_error=%s",
        info.url,
        info.allowed_updates,
        info.pending_update_count,
        info.last_error_message,
    )


async def polling_runner() -> None:
    await bot.delete_webhook(drop_pending_updates=False)
    await dp.start_polling(bot, allowed_updates=WEBHOOK_UPDATE_TYPES)


from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    await prepare()
    polling_task: asyncio.Task | None = None
    if public_base_url():
        try:
            await configure_webhook()
        except Exception:
            logger.exception("Webhook setup failed")
    else:
        polling_task = asyncio.create_task(polling_runner())
        logger.info("WEBHOOK_URL/RENDER_EXTERNAL_HOSTNAME yo‘q — polling ishlayapti")
    try:
        yield
    finally:
        if polling_task:
            polling_task.cancel()
            await asyncio.gather(polling_task, return_exceptions=True)
        await storage.close()
        await redis.aclose()
        await bot.session.close()
        await db.dispose()


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.get("/")
async def root():
    return {"ok": True, "service": settings.app_name, "live": "/live", "health": "/health"}


@app.get("/live")
async def live():
    return {"status": "alive"}


@app.head("/live")
async def live_head():
    return Response(status_code=200)


async def _check_dependencies() -> None:
    async with db.session() as session:
        await session.execute(text("SELECT 1"))
    await redis.ping()


@app.get("/health")
async def health():
    await _check_dependencies()
    return {"status": "ok", "database": "ok", "redis": "ok"}


@app.head("/health")
async def health_head():
    try:
        await _check_dependencies()
    except Exception:
        return Response(status_code=503)
    return Response(status_code=200)


@app.post("/telegram/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    if settings.webhook_secret and x_telegram_bot_api_secret_token != settings.webhook_secret:
        raise HTTPException(status_code=403, detail="Forbidden")

    declared_length = int(request.headers.get("content-length", "0") or 0)
    if declared_length > 2_000_000:
        raise HTTPException(status_code=413, detail="Payload too large")
    try:
        raw_body = await request.body()
        if len(raw_body) > 2_000_000:
            raise HTTPException(status_code=413, detail="Payload too large")
        import json
        payload = json.loads(raw_body)
        update = Update.model_validate(payload, context={"bot": bot})
    except Exception as exc:
        logger.warning("Invalid Telegram update: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid update") from exc

    update_id = update.update_id
    try:
        await dp.feed_update(bot, update)
        if update_id is not None:
            await redis.set(f"telegram:update:{update_id}", b"1", ex=86400, nx=True)
    except Exception as exc:
        logger.exception("Telegram update %s failed", update_id)
        # Non-2xx tells Telegram to retry the webhook delivery.
        raise HTTPException(status_code=500, detail="Update processing failed") from exc
    return {"ok": True}
