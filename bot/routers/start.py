"""Start command and main menu navigation handlers."""
from typing import Dict, Any, Optional

from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot.keyboards import build_main_menu_keyboard
from bot.keyboards.callback_data import MenuCallback
from bot.core.logging_config import get_logger

logger = get_logger(__name__)

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, user_profile: Optional[Dict[str, Any]] = None):
    """Handle /start command and display main menu.
    
    Args:
        message: Incoming message
        state: FSM context
        user_profile: User profile data (injected by AuthMiddleware)
    """
    # Note: referral_code and access_code extraction is now handled in AuthMiddleware
    # Clear any active FSM state (but keep auth data)
    state_data = await state.get_data()
    auth_data = {
        "access_token": state_data.get("access_token"),
        "refresh_token": state_data.get("refresh_token"),
        "access_code": state_data.get("access_code"),
        "referral_code": state_data.get("referral_code")
    }
    await state.clear()
    await state.update_data(**{k: v for k, v in auth_data.items() if v is not None})
    
    # Get access_code from user_profile or FSM state
    access_code = None
    if user_profile:
        access_code = user_profile.get("access_code")
    if not access_code:
        state_data = await state.get_data()
        access_code = state_data.get("access_code")
    
    welcome_text = _(
        "👋 <b>Добро пожаловать в USE.NET Proxy Shop!</b>\n\n"
    )
    
    if access_code:
        welcome_text += _(
            "🔑 <b>Ваш код доступа:</b> <code>{access_code}</code>\n"
            "💡 Сохраните этот код - он работает на всех платформах!\n\n"
        ).format(access_code=access_code)
    
    welcome_text += _("Выберите нужный раздел из меню ниже:")
    
    await message.answer(
        welcome_text,
        reply_markup=build_main_menu_keyboard()
    )


@router.callback_query(MenuCallback.filter(F.action == "back"))
async def callback_back_to_menu(callback: CallbackQuery, state: FSMContext):
    """Handle 'Back to Main Menu' button.
    
    Args:
        callback: Callback query
        state: FSM context
    """
    # Clear FSM state
    await state.clear()
    
    await callback.message.edit_text(
        _("🏠 <b>Главное меню</b>\n\nВыберите нужный раздел:"),
        reply_markup=build_main_menu_keyboard()
    )
    
    await callback.answer()


@router.callback_query(MenuCallback.filter(F.action == "support"))
async def callback_support(callback: CallbackQuery):
    """Handle support button - redirect to support user.
    
    Args:
        callback: Callback query
    """
    from bot.core.config import bot_settings
    
    support_url = f"tg://user?id={bot_settings.SUPPORT_USER_ID}"
    
    await callback.message.answer(
        _("💬 <b>Техническая поддержка</b>\n\n"
          "Нажмите на ссылку ниже, чтобы связаться с поддержкой:\n"
          f'<a href="{support_url}">Написать в поддержку</a>')
    )
    
    await callback.answer()


@router.callback_query(MenuCallback.filter(F.action == "rules"))
async def callback_rules(callback: CallbackQuery):
    """Handle rules button - show rules link.
    
    Args:
        callback: Callback query
    """
    from bot.core.config import bot_settings
    from bot.keyboards import build_back_to_main_menu_keyboard
    
    await callback.message.edit_text(
        _("📜 <b>Правила использования сервиса</b>\n\n"
          f"Ознакомьтесь с правилами: {bot_settings.RULES_URL}"),
        reply_markup=build_back_to_main_menu_keyboard()
    )
    
    await callback.answer()
