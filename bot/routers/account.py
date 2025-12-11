"""Account profile, deposit, and history handlers."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _
from typing import Dict, Any, Optional
import io

from bot.keyboards.callback_data import MenuCallback, AccountCallback, ManageUsersCallback
from bot.keyboards import (
    build_back_to_main_menu_keyboard,
    build_payment_invoice_keyboard,
    build_deposit_amount_keyboard
)
from bot.services.api_client import BackendAPIClient
from bot.utils.formatters import format_user_profile, format_payment_invoice
from bot.utils.validators import validate_access_code, validate_telegram_id
from bot.states.account import AccountStates
from bot.core.logging_config import get_logger

logger = get_logger(__name__)

router = Router(name="account")


@router.callback_query(MenuCallback.filter(F.action == "account"))
async def callback_account(
    callback: CallbackQuery,
    api_client: BackendAPIClient,
    user_profile: Optional[Dict[str, Any]] = None
):
    """Show account information.
    
    Args:
        callback: Callback query
        api_client: API client (injected by AuthMiddleware)
        user_profile: User profile data (injected by AuthMiddleware, optional)
    """
    try:
        # If no profile, fetch it
        if not user_profile:
            try:
                user_profile = await api_client.get_user_profile()
            except Exception as e:
                logger.error(f"Failed to fetch user profile: {e}")
                await callback.message.edit_text(
                    _("❌ <b>Ошибка при загрузке профиля</b>\n\n"
                      "Возможные причины:\n"
                      "• Проблема с подключением к серверу\n"
                      "• Сессия устарела\n\n"
                      "Пожалуйста, используйте /start для повторной авторизации."),
                    reply_markup=build_back_to_main_menu_keyboard()
                )
                await callback.answer()
                return
        
        # Format profile message
        profile_text = format_user_profile(user_profile)

        # Create keyboard with action buttons
        keyboard = [
            [InlineKeyboardButton(
                text=_("💰 ПОПОЛНИТЬ БАЛАНС"),
                callback_data=AccountCallback(action="deposit").pack()
            )],
            [InlineKeyboardButton(
                text=_("📊 ИСТОРИЯ АККАУНТА"),
                callback_data=AccountCallback(action="history").pack()
            )],
            [InlineKeyboardButton(
                text=_("🔑 ВХОД ПО КЛЮЧУ"),
                callback_data=AccountCallback(action="login_by_key").pack()
            )],
            [InlineKeyboardButton(
                text=_("👥 МОИ ПОЛЬЗОВАТЕЛИ"),
                callback_data=AccountCallback(action="my_users").pack()
            )],
            [InlineKeyboardButton(
                text=_("◀️ НАЗАД"),
                callback_data=MenuCallback(action="back").pack()
            )],
        ]

        await callback.message.edit_text(
            profile_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            disable_web_page_preview=True
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Error showing account: {e}")
        await callback.answer(_("Ошибка при загрузке профиля"), show_alert=True)


@router.callback_query(AccountCallback.filter(F.action == "deposit"))
async def callback_deposit(
    callback: CallbackQuery,
    state: FSMContext,
    api_client: BackendAPIClient
):
    """Request deposit amount from user.

    Args:
        callback: Callback query
        state: FSM context
        api_client: API client (injected by AuthMiddleware)
    """
    try:
        # Get minimum deposit amount from config
        from bot.core.config import bot_settings
        min_amount = bot_settings.MIN_DEPOSIT_USD

        # Show message requesting deposit amount
        await callback.message.edit_text(
            _("💵 <b>Введите сумму пополнения в долларах</b>\n\n"
              "💰 Минимальная сумма: ${min_amount:.0f}\n\n"
              "Отправьте число (например: 50)").format(min_amount=min_amount),
            reply_markup=build_deposit_amount_keyboard()
        )

        # Set FSM state to wait for amount input
        await state.set_state(AccountStates.waiting_for_deposit_amount)
        await callback.answer()

    except Exception as e:
        logger.error(f"Error requesting deposit amount: {e}")
        await callback.message.edit_text(
            _("❌ Ошибка. Попробуйте позже."),
            reply_markup=build_back_to_main_menu_keyboard()
        )
        await callback.answer()


@router.message(AccountStates.waiting_for_deposit_amount)
async def process_deposit_amount(
    message: Message,
    state: FSMContext,
    api_client: BackendAPIClient
):
    """Process user input for deposit amount and create payment invoice.

    Args:
        message: User message with amount
        state: FSM context
        api_client: API client (injected by AuthMiddleware)
    """
    try:
        # Get minimum deposit amount from config
        from bot.core.config import bot_settings
        min_amount = bot_settings.MIN_DEPOSIT_USD

        # Validate input - must be an integer
        try:
            amount = int(message.text.strip())
        except (ValueError, AttributeError):
            await message.answer(
                _("❌ <b>Неверный формат</b>\n\n"
                  "Пожалуйста, введите целое число (например: 50)"),
                reply_markup=build_deposit_amount_keyboard()
            )
            return

        # Validate amount - must be >= minimum
        if amount < min_amount:
            await message.answer(
                _("❌ <b>Сумма слишком мала</b>\n\n"
                  "Минимальная сумма пополнения: ${min_amount:.0f}\n"
                  "Попробуйте снова.").format(min_amount=min_amount),
                reply_markup=build_deposit_amount_keyboard()
            )
            return

        # Amount is valid - create payment invoice
        loading_msg = await message.answer(_("⏳ Создаём платёжную ссылку..."))

        # Create payment invoice with specified amount
        invoice_response = await api_client.create_payment_invoice(amount_usd=float(amount))

        payment_url = invoice_response.get("payment_url")
        payment_uuid = invoice_response.get("payment_uuid")
        order_id = invoice_response.get("order_id")
        expired_at = invoice_response.get("expired_at")
        amount_usd = invoice_response.get("amount_usd", amount)
        min_amount_usd = invoice_response.get("min_amount_usd", min_amount)

        if not payment_url or not order_id:
            await loading_msg.edit_text(
                _("❌ Ошибка при создании платёжной ссылки. Попробуйте позже."),
                reply_markup=build_back_to_main_menu_keyboard()
            )
            await state.clear()
            return

        # Save payment info to state for reference
        await state.update_data(
            payment_uuid=payment_uuid,
            order_id=order_id,
            payment_url=payment_url
        )

        # Format payment invoice message
        invoice_text = format_payment_invoice(
            payment_url=payment_url,
            order_id=order_id,
            amount_usd=amount_usd,
            min_amount_usd=min_amount_usd,
            expired_at=expired_at
        )

        # Send message with payment URL button
        await loading_msg.edit_text(
            invoice_text,
            reply_markup=build_payment_invoice_keyboard(payment_url)
        )

        # Clear FSM state
        await state.clear()

    except Exception as e:
        logger.error(f"Error processing deposit amount: {e}")

        # Check if it's an HTTP error with specific message
        error_message = _("❌ Ошибка при создании платёжной ссылки. Попробуйте позже.")

        # Try to extract more specific error from the response
        if hasattr(e, 'response'):
            try:
                error_data = e.response.json()
                detail = error_data.get('detail', '')
                if detail:
                    error_message = f"❌ {detail}"
            except:
                pass

        await message.answer(
            error_message,
            reply_markup=build_back_to_main_menu_keyboard()
        )
        await state.clear()


@router.callback_query(AccountCallback.filter(F.action == "cancel_deposit"))
async def callback_cancel_deposit(
    callback: CallbackQuery,
    state: FSMContext,
    api_client: BackendAPIClient,
    user_profile: Optional[Dict[str, Any]] = None
):
    """Cancel deposit flow and return to account menu.

    Args:
        callback: Callback query
        state: FSM context
        api_client: API client (injected by AuthMiddleware)
        user_profile: User profile data (injected by AuthMiddleware, optional)
    """
    try:
        # Clear FSM state
        await state.clear()

        # Fetch user profile if not provided
        if not user_profile:
            try:
                user_profile = await api_client.get_user_profile()
            except Exception as e:
                logger.error(f"Failed to fetch user profile: {e}")
                await callback.message.edit_text(
                    _("❌ Ошибка при загрузке профиля"),
                    reply_markup=build_back_to_main_menu_keyboard()
                )
                await callback.answer()
                return

        # Show account profile
        profile_text = format_user_profile(user_profile)

        # Create keyboard with action buttons
        keyboard = [
            [InlineKeyboardButton(
                text=_("💰 ПОПОЛНИТЬ БАЛАНС"),
                callback_data=AccountCallback(action="deposit").pack()
            )],
            [InlineKeyboardButton(
                text=_("📊 ИСТОРИЯ АККАУНТА"),
                callback_data=AccountCallback(action="history").pack()
            )],
            [InlineKeyboardButton(
                text=_("🔑 ВХОД ПО КЛЮЧУ"),
                callback_data=AccountCallback(action="login_by_key").pack()
            )],
            [InlineKeyboardButton(
                text=_("👥 МОИ ПОЛЬЗОВАТЕЛИ"),
                callback_data=AccountCallback(action="my_users").pack()
            )],
            [InlineKeyboardButton(
                text=_("◀️ НАЗАД"),
                callback_data=MenuCallback(action="back").pack()
            )],
        ]

        await callback.message.edit_text(
            profile_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            disable_web_page_preview=True
        )

        await callback.answer(_("❌ Пополнение отменено"))

    except Exception as e:
        logger.error(f"Error cancelling deposit: {e}")
        await callback.answer(_("Ошибка"), show_alert=True)


@router.callback_query(AccountCallback.filter(F.action == "history"))
async def callback_history(
    callback: CallbackQuery,
    api_client: BackendAPIClient
):
    """Show account transaction history.
    
    Args:
        callback: Callback query
        api_client: API client (injected by AuthMiddleware)
    """
    try:
        # Get user history from API
        history_response = await api_client.get_user_history(limit=20)
        history = history_response.get("history", [])
        
        if not history:
            await callback.message.edit_text(
                _("📊 <b>История аккаунта</b>\n\n"
                  "История транзакций пуста."),
                reply_markup=build_back_to_main_menu_keyboard()
            )
        else:
            # Format history entries
            history_lines = []
            for entry in history:
                # Use the formatted_message directly from API
                formatted_message = entry.get("formatted_message", "N/A")
                history_lines.append(formatted_message)
            
            history_text = (
                _("📊 <b>История аккаунта</b>\n\n") +
                "\n".join(history_lines)
            )
            
            await callback.message.edit_text(
                history_text,
                reply_markup=build_back_to_main_menu_keyboard()
            )
        
        await callback.answer()
    
    except Exception as e:
        logger.error(f"Error loading history: {e}")
        await callback.answer(_("Ошибка при загрузке истории"), show_alert=True)


@router.callback_query(AccountCallback.filter(F.action == "back"))
async def callback_account_back(callback: CallbackQuery):
    """Handle back button from account section.

    Args:
        callback: Callback query
    """
    from bot.keyboards import build_main_menu_keyboard

    await callback.message.edit_text(
        _("🏠 <b>Главное меню</b>\n\nВыберите нужный раздел:"),
        reply_markup=build_main_menu_keyboard()
    )

    await callback.answer()


@router.callback_query(AccountCallback.filter(F.action == "login_by_key"))
async def callback_login_by_key(
    callback: CallbackQuery,
    state: FSMContext
):
    """Prompt user to enter access code for account linking.

    Args:
        callback: Callback query
        state: FSM context
    """
    # Set FSM state
    await state.set_state(AccountStates.waiting_access_code)

    # Create cancel keyboard
    keyboard = [
        [InlineKeyboardButton(
            text=_("❌ Отмена"),
            callback_data=MenuCallback(action="account").pack()
        )]
    ]

    await callback.message.edit_text(
        _("🔑 <b>Вход по ключу доступа</b>\n\n"
          "Введите ваш ключ доступа в формате:\n"
          "<code>XXX-XXX-XXX</code>\n\n"
          "Этот ключ вы получили при регистрации на сайте."),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

    await callback.answer()


@router.message(AccountStates.waiting_access_code)
async def process_access_code_input(
    message: Message,
    state: FSMContext,
    api_client: BackendAPIClient
):
    """Process access code input and link Telegram account.

    Args:
        message: User message with access code
        state: FSM context
        api_client: API client
    """
    try:
        # Validate access code format
        is_valid, normalized_code, error_message = validate_access_code(message.text)

        if not is_valid:
            await message.answer(
                f"❌ <b>Неверный формат кода</b>\n\n{error_message}\n\n"
                "Попробуйте еще раз или нажмите /start для отмены."
            )
            return

        # Show processing message
        processing_msg = await message.answer(_("⏳ Проверяем код доступа..."))

        # Try to link account
        try:
            response = await api_client.link_telegram_by_key(
                access_code=normalized_code,
                telegram_id=message.from_user.id,
                username=message.from_user.username
            )

            # Update tokens in state
            access_token = response.get("access_token")
            refresh_token = response.get("refresh_token")

            if access_token and refresh_token:
                await state.update_data(
                    access_token=access_token,
                    refresh_token=refresh_token
                )
                api_client.set_access_token(access_token, refresh_token)

            # Clear FSM state
            await state.clear()

            # Show success message
            await processing_msg.edit_text(
                _("✅ <b>Аккаунт успешно привязан!</b>\n\n"
                  "Ваш Telegram аккаунт теперь связан с профилем.\n"
                  "Используйте /start для доступа к главному меню."),
                reply_markup=build_back_to_main_menu_keyboard()
            )

        except Exception as e:
            logger.error(f"Error linking by access code: {e}")

            # Extract error message
            error_msg = _("❌ Ошибка при привязке аккаунта")
            if hasattr(e, 'response'):
                try:
                    error_data = e.response.json()
                    detail = error_data.get('detail', '')
                    if detail:
                        error_msg = f"❌ {detail}"
                except:
                    pass

            await processing_msg.edit_text(
                f"{error_msg}\n\n"
                "Возможные причины:\n"
                "• Код доступа не найден\n"
                "• Telegram ID уже привязан к другому аккаунту\n"
                "• Код доступа истёк\n\n"
                "Попробуйте еще раз или обратитесь в поддержку.",
                reply_markup=build_back_to_main_menu_keyboard()
            )

            # Clear FSM state
            await state.clear()

    except Exception as e:
        logger.error(f"Error processing access code: {e}")
        await message.answer(
            _("❌ Произошла ошибка. Попробуйте позже."),
            reply_markup=build_back_to_main_menu_keyboard()
        )
        await state.clear()


@router.callback_query(AccountCallback.filter(F.action == "my_users"))
async def callback_my_users(
    callback: CallbackQuery,
    api_client: BackendAPIClient
):
    """Show list of linked Telegram users.

    Args:
        callback: Callback query
        api_client: API client
    """
    try:
        # Get linked users from API
        response = await api_client.get_linked_users()

        telegram_id_owner = response.get("telegram_id_owner")
        linked_telegram_ids = response.get("linked_telegram_ids", [])
        total = response.get("total", 0)

        # Build message
        if total == 0:
            message_text = _(
                "👥 <b>Мои пользователи</b>\n\n"
                "Нет подключенных пользователей.\n\n"
                "Вы можете добавить дополнительные Telegram аккаунты "
                "для совместного использования баланса."
            )
        else:
            users_list = "\n".join([f"• <code>{tid}</code>" for tid in linked_telegram_ids])
            message_text = _(
                f"👥 <b>Мои пользователи</b>\n\n"
                f"Владелец: <code>{telegram_id_owner}</code>\n\n"
                f"Связанные пользователи ({total}):\n{users_list}\n\n"
                "Все связанные пользователи используют общий баланс."
            )

        # Build keyboard
        keyboard = []

        # Add remove buttons for each linked user
        for tid in linked_telegram_ids:
            keyboard.append([InlineKeyboardButton(
                text=f"❌ {tid}",
                callback_data=ManageUsersCallback(action="remove", telegram_id=tid).pack()
            )])

        # Add "Add user" button
        keyboard.append([InlineKeyboardButton(
            text=_("➕ Добавить пользователя"),
            callback_data=ManageUsersCallback(action="add").pack()
        )])

        # Add back button
        keyboard.append([InlineKeyboardButton(
            text=_("◀️ Назад"),
            callback_data=MenuCallback(action="account").pack()
        )])

        await callback.message.edit_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )

        await callback.answer()

    except Exception as e:
        logger.error(f"Error loading linked users: {e}")
        await callback.answer(_("Ошибка при загрузке списка пользователей"), show_alert=True)


@router.callback_query(ManageUsersCallback.filter(F.action == "add"))
async def callback_add_user(
    callback: CallbackQuery,
    state: FSMContext
):
    """Prompt user to enter Telegram ID to add.

    Args:
        callback: Callback query
        state: FSM context
    """
    # Set FSM state
    await state.set_state(AccountStates.waiting_telegram_id_to_add)

    # Create cancel keyboard
    keyboard = [
        [InlineKeyboardButton(
            text=_("❌ Отмена"),
            callback_data=AccountCallback(action="my_users").pack()
        )]
    ]

    await callback.message.edit_text(
        _("➕ <b>Добавить пользователя</b>\n\n"
          "Введите Telegram ID пользователя, которого хотите добавить.\n\n"
          "Telegram ID - это уникальный числовой идентификатор пользователя.\n"
          "Пример: <code>123456789</code>"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

    await callback.answer()


@router.message(AccountStates.waiting_telegram_id_to_add)
async def process_telegram_id_input(
    message: Message,
    state: FSMContext,
    api_client: BackendAPIClient
):
    """Process Telegram ID input and add user to linked list.

    Args:
        message: User message with Telegram ID
        state: FSM context
        api_client: API client
    """
    try:
        # Validate Telegram ID
        is_valid, telegram_id, error_message = validate_telegram_id(message.text)

        if not is_valid:
            await message.answer(
                f"❌ <b>Неверный формат</b>\n\n{error_message}\n\n"
                "Попробуйте еще раз или нажмите /start для отмены."
            )
            return

        # Show processing message
        processing_msg = await message.answer(_("⏳ Добавляем пользователя..."))

        # Try to add user
        try:
            response = await api_client.add_linked_user(telegram_id)

            # Clear FSM state
            await state.clear()

            # Get updated list
            linked_telegram_ids = response.get("linked_telegram_ids", [])
            total = len(linked_telegram_ids)

            # Show success message with updated list
            users_list = "\n".join([f"• <code>{tid}</code>" for tid in linked_telegram_ids])

            await processing_msg.edit_text(
                _(f"✅ <b>Пользователь добавлен!</b>\n\n"
                  f"Telegram ID <code>{telegram_id}</code> успешно добавлен.\n\n"
                  f"Связанные пользователи ({total}):\n{users_list}"),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text=_("◀️ К списку пользователей"),
                        callback_data=AccountCallback(action="my_users").pack()
                    )]
                ])
            )

        except Exception as e:
            logger.error(f"Error adding linked user: {e}")

            # Extract error message
            error_msg = _("❌ Ошибка при добавлении пользователя")
            if hasattr(e, 'response'):
                try:
                    error_data = e.response.json()
                    detail = error_data.get('detail', '')
                    if detail:
                        error_msg = f"❌ {detail}"
                except:
                    pass

            await processing_msg.edit_text(
                f"{error_msg}\n\n"
                "Возможные причины:\n"
                "• Telegram ID уже привязан к другому аккаунту\n"
                "• Telegram ID не существует\n"
                "• У вас нет прав для этой операции\n\n"
                "Попробуйте еще раз или обратитесь в поддержку.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text=_("◀️ К списку пользователей"),
                        callback_data=AccountCallback(action="my_users").pack()
                    )]
                ])
            )

            # Clear FSM state
            await state.clear()

    except Exception as e:
        logger.error(f"Error processing telegram ID: {e}")
        await message.answer(
            _("❌ Произошла ошибка. Попробуйте позже."),
            reply_markup=build_back_to_main_menu_keyboard()
        )
        await state.clear()


@router.callback_query(ManageUsersCallback.filter(F.action == "remove"))
async def callback_remove_user(
    callback: CallbackQuery,
    callback_data: ManageUsersCallback
):
    """Show confirmation dialog for removing user.

    Args:
        callback: Callback query
        callback_data: Callback data with telegram_id
    """
    telegram_id = callback_data.telegram_id

    # Create confirmation keyboard
    keyboard = [
        [InlineKeyboardButton(
            text=_("✅ Подтвердить"),
            callback_data=ManageUsersCallback(action="confirm_remove", telegram_id=telegram_id).pack()
        )],
        [InlineKeyboardButton(
            text=_("❌ Отмена"),
            callback_data=AccountCallback(action="my_users").pack()
        )]
    ]

    await callback.message.edit_text(
        _(f"❓ <b>Удалить пользователя?</b>\n\n"
          f"Вы уверены, что хотите удалить пользователя <code>{telegram_id}</code> "
          f"из списка связанных аккаунтов?\n\n"
          f"После удаления этот пользователь больше не сможет использовать ваш баланс."),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

    await callback.answer()


@router.callback_query(ManageUsersCallback.filter(F.action == "confirm_remove"))
async def callback_confirm_remove_user(
    callback: CallbackQuery,
    callback_data: ManageUsersCallback,
    api_client: BackendAPIClient
):
    """Confirm and remove user from linked list.

    Args:
        callback: Callback query
        callback_data: Callback data with telegram_id
        api_client: API client
    """
    telegram_id = callback_data.telegram_id

    try:
        # Show processing message
        await callback.message.edit_text(_("⏳ Удаляем пользователя..."))

        # Try to remove user
        try:
            response = await api_client.remove_linked_user(telegram_id)

            # Get updated list
            linked_telegram_ids = response.get("linked_telegram_ids", [])
            total = len(linked_telegram_ids)

            # Show success message
            if total == 0:
                message_text = _(
                    f"✅ <b>Пользователь удалён!</b>\n\n"
                    f"Telegram ID <code>{telegram_id}</code> удалён из списка.\n\n"
                    "Список связанных пользователей пуст."
                )
            else:
                users_list = "\n".join([f"• <code>{tid}</code>" for tid in linked_telegram_ids])
                message_text = _(
                    f"✅ <b>Пользователь удалён!</b>\n\n"
                    f"Telegram ID <code>{telegram_id}</code> удалён из списка.\n\n"
                    f"Связанные пользователи ({total}):\n{users_list}"
                )

            await callback.message.edit_text(
                message_text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text=_("◀️ К списку пользователей"),
                        callback_data=AccountCallback(action="my_users").pack()
                    )]
                ])
            )

            await callback.answer(_("✅ Пользователь удалён"))

        except Exception as e:
            logger.error(f"Error removing linked user: {e}")

            # Extract error message
            error_msg = _("❌ Ошибка при удалении пользователя")
            if hasattr(e, 'response'):
                try:
                    error_data = e.response.json()
                    detail = error_data.get('detail', '')
                    if detail:
                        error_msg = f"❌ {detail}"
                except:
                    pass

            await callback.message.edit_text(
                f"{error_msg}\n\n"
                "Возможные причины:\n"
                "• Пользователь не найден в списке\n"
                "• У вас нет прав для этой операции\n"
                "• Попытка удалить владельца аккаунта\n\n"
                "Обратитесь в поддержку, если проблема сохраняется.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text=_("◀️ К списку пользователей"),
                        callback_data=AccountCallback(action="my_users").pack()
                    )]
                ])
            )

            await callback.answer()

    except Exception as e:
        logger.error(f"Error in confirm remove user: {e}")
        await callback.answer(_("❌ Произошла ошибка"), show_alert=True)


