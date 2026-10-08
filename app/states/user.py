from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    search_book = State()
    select_quiz_book = State()
    select_quiz_count = State()
    answering_quiz = State()
    contact_admin = State()
