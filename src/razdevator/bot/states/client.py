from aiogram.fsm.state import State, StatesGroup


class GenerationState(StatesGroup):
    waiting_photo = State()

