from aiogram.fsm.state import State, StatesGroup

class ParserStates(StatesGroup):
    waiting_seller_url = State()
    waiting_seller_urls_for_inn = State() 
    waiting_product_urls_for_inn = State()  