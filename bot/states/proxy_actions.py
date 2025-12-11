"""FSM states for proxy actions (validation and extension)."""
from aiogram.fsm.state import State, StatesGroup


class ProxyActionStates(StatesGroup):
    """States for proxy validation and extension actions."""
    
    waiting_proxy_id_for_validation = State()  # Waiting for proxy ID to validate (both socks5 and pptp)
    waiting_proxy_id_for_extension = State()  # Waiting for proxy ID to extend
