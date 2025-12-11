"""FSM states for SOCKS5 proxy purchase flow."""
from aiogram.fsm.state import State, StatesGroup


class Socks5States(StatesGroup):
    """States for SOCKS5 proxy purchase dialog."""

    waiting_country = State()  # Waiting for country selection
    waiting_filter_choice = State()  # Waiting for filter type (state/city/zip/random)
    waiting_state_selection = State()  # Waiting for state selection from buttons
    waiting_state_input = State()  # Waiting for state/region name input
    waiting_city_input = State()  # Waiting for city name input
    waiting_zip_input = State()  # Waiting for ZIP code input
    browsing_proxies = State()  # Browsing proxy list with pagination
    confirming_purchase = State()  # Confirming proxy purchase
