"""Payment and deposit handlers."""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot.keyboards.callback_data import PaymentCallback, AccountCallback
from bot.core.logging_config import get_logger

logger = get_logger(__name__)

router = Router(name="payment")

# Note: Payment flow has been moved to bot/routers/account.py
# This router is kept for potential future payment-specific handlers
# such as webhook callbacks or additional payment-related actions.

