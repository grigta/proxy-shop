from aiogram.fsm.state import State, StatesGroup


class AccountStates(StatesGroup):
    """FSM states for account management operations"""

    waiting_access_code = State()  # Waiting for access code input (XXX-XXX-XXX format)
    waiting_telegram_id_to_add = State()  # Waiting for telegram ID input to add to linked users
    waiting_for_deposit_amount = State()  # Waiting for deposit amount input (minimum $10)
