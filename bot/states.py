from aiogram.fsm.state import State, StatesGroup

class ParserStates(StatesGroup):
    waiting_seller_url = State()