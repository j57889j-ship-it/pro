from aiogram.fsm.state import State, StatesGroup


class AdminBookStates(StatesGroup):
    title = State()
    author = State()
    description = State()
    channel_url = State()
    detail_url = State()
    cover = State()
    find = State()
    delete = State()


class AdminQuestionStates(StatesGroup):
    book = State()
    text = State()
    option_a = State()
    option_b = State()
    option_c = State()
    option_d = State()
    correct = State()


class AdminImportStates(StatesGroup):
    book = State()
    file = State()


class AdminChannelStates(StatesGroup):
    title = State()
    chat_id = State()
    invite_url = State()
    delete = State()


class AdminAddAdminStates(StatesGroup):
    telegram_id = State()
    role = State()


class AdminBroadcastStates(StatesGroup):
    text = State()


class AdminUserStates(StatesGroup):
    search = State()
    manage = State()
    clean = State()
    block = State()


class AdminReactionStates(StatesGroup):
    emoji = State()


class AdminSettingStates(StatesGroup):
    top_limit = State()
    points = State()
    daily_question = State()


class AdminRemoveAdminStates(StatesGroup):
    telegram_id = State()
