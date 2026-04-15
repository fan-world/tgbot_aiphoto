from aiogram.fsm.state import State, StatesGroup


class CreateBotState(StatesGroup):
    waiting_token = State()


class EditBotTextState(StatesGroup):
    waiting_welcome = State()
    waiting_farewell = State()


class BotBroadcastState(StatesGroup):
    waiting_text = State()


class OwnerRateState(StatesGroup):
    waiting_staff_ref = State()
    waiting_rate = State()


class OwnerReferralStatsState(StatesGroup):
    waiting_staff_ref = State()


class OwnerBroadcastState(StatesGroup):
    waiting_text = State()


class OwnerMainLinkState(StatesGroup):
    waiting_link = State()
