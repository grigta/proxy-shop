"""FSM states for PPTP proxy purchase flow."""
from aiogram.fsm.state import State, StatesGroup


class PPTPStates(StatesGroup):
    """States for PPTP proxy purchase dialog."""

    waiting_catalog_choice = State()  # Waiting for catalog selection
    waiting_region = State()  # Waiting for region selection (USA/EUROPE)
    waiting_filter_choice = State()  # Waiting for filter type (state/city/zip/skip)
    waiting_state_input = State()  # Waiting for state name input (text)
    waiting_city_input = State()  # Waiting for city name input (text)
    waiting_zip_input = State()  # Waiting for ZIP code input (text)
    browsing_states = State()  # Browsing available states (buttons)
    browsing_pptp_list = State()  # Browsing PPTP proxy list with pagination
    confirming_purchase = State()  # Confirming PPTP purchase
