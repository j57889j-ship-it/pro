from aiogram import Router

from . import channels, content, dashboard, leaderboard, navigation, quiz, settings, users


def build_router() -> Router:
    router = Router(name="admin")
    # Navigation first; AdminOnlyMiddleware is applied at runtime in main.py.
    for module in (navigation, dashboard, content, users, channels, leaderboard, quiz, settings):
        router.include_router(module.router)
    return router
