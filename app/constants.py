MAIN_MENU_BUTTONS = {
    "books": "📚 KITOBLAR",
    "quiz": "🧠 TEST",
    "top": "🏆 TOP",
    "profile": "👤 PROFIL",
    "help": "ℹ️ YORDAM",
    "admin": "🛠 ADMIN",
}

ADMIN_MENU_BUTTONS = {
    "dashboard": "📊 DASHBOARD",
    "content": "📚 KONTENT",
    "users": "👥 FOYDALANUVCHILAR",
    "channels": "📢 KANALLAR",
    "leaderboard": "🏆 REYTING",
    "quiz": "🧠 TEST BOSHQARUVI",
    "settings": "⚙️ SOZLAMALAR",
    "back": "⬅️ ASOSIY MENYU",
}

# Reply-navigation labels. These are intentionally unique so FSM handlers never swallow them.
NAV_MAIN = "⬅️ ASOSIY MENYU"
NAV_BOOKS = "⬅️ KITOBLAR"
NAV_TESTS = "⬅️ TESTLAR"
NAV_PROFILE = "⬅️ PROFIL"
NAV_HELP = "⬅️ YORDAM"
NAV_ADMIN = "⬅️ ADMIN PANEL"
NAV_CONTENT = "⬅️ KONTENT"
NAV_BOOK_MANAGEMENT = "⬅️ KITOBLAR BOSHQARUVI"
NAV_QUESTION_MANAGEMENT = "⬅️ SAVOLLAR BOSHQARUVI"
NAV_USERS = "⬅️ FOYDALANUVCHILAR"
NAV_CHANNELS = "⬅️ KANALLAR"
NAV_LEADERBOARD = "⬅️ REYTING"
NAV_TEST_MANAGEMENT = "⬅️ TEST BOSHQARUVI"
NAV_SETTINGS = "⬅️ SOZLAMALAR"
CANCEL = "❌ BEKOR"

ROLE_SUPERADMIN = "superadmin"
ROLE_ADMIN = "admin"
ROLE_MODERATOR = "moderator"

# Telegram accepts these as ReactionTypeEmoji values. The bot can set at most one emoji reaction per message.
SUPPORTED_REACTION_EMOJIS = {
    "❤", "👍", "👎", "🔥", "🥰", "👏", "😁", "🤔", "🤯", "😱", "🤬", "😢", "🎉", "🤩",
    "🤮", "💩", "🙏", "👌", "🕊", "🤡", "🥱", "🥴", "😍", "🐳", "❤‍🔥", "🌚", "🌭", "💯",
    "🤣", "⚡", "🍌", "🏆", "💔", "🤨", "😐", "🍓", "🍾", "💋", "😈", "😴", "😭", "🤓",
    "👻", "👨‍💻", "👀", "🎃", "🙈", "😇", "😨", "🤝", "✍", "🤗", "🫡", "🎅", "🎄", "☃",
    "💅", "🤪", "🗿", "🆒", "💘", "🙉", "😘", "💊", "🙊", "😎", "👾", "🤷‍♂", "🤷", "🤷‍♀", "😡",
}

WEBHOOK_UPDATE_TYPES = [
    "message",
    "callback_query",
    "channel_post",
    "edited_channel_post",
    "my_chat_member",
]
