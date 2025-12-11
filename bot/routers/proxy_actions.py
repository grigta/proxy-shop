"""Proxy validation and extension handlers."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _
from datetime import datetime

from bot.keyboards.callback_data import ProxyCallback
from bot.keyboards import build_back_to_main_menu_keyboard
from bot.services.api_client import BackendAPIClient
from bot.states import ProxyActionStates
from bot.utils.formatters import format_proxy_validation_result
from bot.utils.validators import validate_proxy_id, validate_ip_address
from bot.core.config import bot_settings
from bot.core.logging_config import get_logger

logger = get_logger(__name__)

router = Router(name="proxy_actions")


@router.callback_query(ProxyCallback.filter(F.action == "validate"))
async def callback_start_validation(callback: CallbackQuery, state: FSMContext):
    """Start proxy validation flow.
    
    Args:
        callback: Callback query
        state: FSM context
    """
    await state.set_state(ProxyActionStates.waiting_proxy_id_for_validation)
    # Save proxy_type context - defaulting to socks5, will be updated from input
    await state.update_data(validation_proxy_type="socks5")
    
    await callback.message.answer(
        _("✅ <b>Проверка прокси на валидность</b>\n\n"
          "Отправьте ID прокси для проверки:")
    )
    
    await callback.answer()


@router.message(ProxyActionStates.waiting_proxy_id_for_validation)
async def process_validation_id(
    message: Message,
    state: FSMContext,
    api_client: BackendAPIClient
):
    """Process proxy ID for validation.
    
    Args:
        message: User message
        state: FSM context
        api_client: API client
    """
    is_valid, proxy_id, error = validate_proxy_id(message.text)
    
    if not is_valid:
        await message.answer(_(f"❌ {error}\n\nПопробуйте еще раз:"))
        return
    
    try:
        # Get proxy_type from state or default to socks5
        state_data = await state.get_data()
        proxy_type = state_data.get("validation_proxy_type", "socks5")
        
        # Validate proxy
        result = await api_client.validate_proxy(proxy_id, proxy_type)
        
        is_online = result.get("online", False)
        purchase_time = result.get("purchase_time")
        refund_eligible = result.get("refund_eligible", False)
        minutes_since_purchase = result.get("minutes_since_purchase", 0)
        
        # Calculate time since purchase
        time_since_purchase = None
        if minutes_since_purchase is not None:
            hours = minutes_since_purchase // 60
            minutes = minutes_since_purchase % 60
            time_since_purchase = f"{hours}ч {minutes}м"
        
        validation_text = format_proxy_validation_result(
            is_online=is_online,
            time_since_purchase=time_since_purchase,
            can_refund=refund_eligible
        )
        
        await message.answer(
            validation_text,
            reply_markup=build_back_to_main_menu_keyboard()
        )
        
        await state.clear()
    
    except Exception as e:
        logger.error(f"Error validating proxy: {e}")
        await message.answer(
            _("❌ Ошибка при проверке прокси"),
            reply_markup=build_back_to_main_menu_keyboard()
        )
        await state.clear()


@router.callback_query(ProxyCallback.filter(F.action == "extend"))
async def callback_start_extension(
    callback: CallbackQuery,
    state: FSMContext,
    user_profile: dict
):
    """Start proxy extension flow.
    
    Args:
        callback: Callback query
        state: FSM context
        user_profile: User profile data
    """
    await state.set_state(ProxyActionStates.waiting_proxy_id_for_extension)
    # Save proxy_type context - defaulting to socks5
    await state.update_data(extension_proxy_type="socks5")
    
    # Assuming extension costs the same as original purchase (e.g., $2)
    extension_cost = 2.0
    
    await callback.message.answer(
        _(f"🔄 <b>Продление прокси</b>\n\n"
          f"Стоимость продления прокси: {extension_cost}$\n"
          f"Для продления отправьте proxy_id")
    )
    
    await callback.answer()


@router.message(ProxyActionStates.waiting_proxy_id_for_extension)
async def process_extension_id(
    message: Message,
    state: FSMContext,
    api_client: BackendAPIClient,
    user_profile: dict
):
    """Process proxy ID for extension.
    
    Args:
        message: User message
        state: FSM context
        api_client: API client
        user_profile: User profile data
    """
    is_valid, proxy_id, error = validate_proxy_id(message.text)
    
    if not is_valid:
        await message.answer(_(f"❌ {error}\n\nПопробуйте еще раз:"))
        return
    
    try:
        # Get proxy_type from state or default to socks5
        state_data = await state.get_data()
        proxy_type = state_data.get("extension_proxy_type", "socks5")
        
        # First validate if proxy is online
        validation = await api_client.validate_proxy(proxy_id, proxy_type)
        is_online = validation.get("online", False)
        proxy_string = validation.get("proxy", "N/A")
        
        if not is_online:
            await message.answer(
                _(f"❌ Прокси {proxy_string} ушел в офлайн, продление невозможно"),
                reply_markup=build_back_to_main_menu_keyboard()
            )
            await state.clear()
            return
        
        # Extend proxy
        result = await api_client.extend_proxy(proxy_id, proxy_type)
        
        new_balance = result.get("new_balance", user_profile.get("balance", 0))
        # Convert to float for formatting (handles string/Decimal from API)
        try:
            new_balance = float(new_balance)
        except (ValueError, TypeError):
            new_balance = 0.0
        
        await message.answer(
            _(f"✅ Прокси {proxy_string} успешно продлен.\n\n"
              f"💸 Баланс: {new_balance:.2f}$"),
            reply_markup=build_back_to_main_menu_keyboard()
        )
        
        await state.clear()
    
    except Exception as e:
        logger.error(f"Error extending proxy: {e}")
        await message.answer(
            _("❌ Ошибка при продлении прокси. Возможно недостаточно средств."),
            reply_markup=build_back_to_main_menu_keyboard()
        )
        await state.clear()


# PPTP validation handlers

@router.callback_query(ProxyCallback.filter(F.action == "validate_pptp"))
async def callback_start_pptp_validation(callback: CallbackQuery, state: FSMContext):
    """Start PPTP validation flow.
    
    Args:
        callback: Callback query
        state: FSM context
    """
    await state.set_state(ProxyActionStates.waiting_proxy_id_for_validation)
    # Save proxy_type context as pptp
    await state.update_data(validation_proxy_type="pptp")
    
    await callback.message.answer(
        _("✅ <b>Проверка PPTP на валидность</b>\n\n"
          "Отправьте ID PPTP прокси для проверки:")
    )
    
    await callback.answer()

# Note: PPTP validation now uses the same handler as SOCKS5 (process_validation_id)
# with proxy_type="pptp" stored in state
