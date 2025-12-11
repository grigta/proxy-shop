"""SOCKS5 proxy purchase flow handlers."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _
from typing import Dict, Any

from bot.keyboards.callback_data import (
    MenuCallback, CountryCallback, FilterCallback,
    ProxyCallback, PaginationCallback, HistoryCallback,
    StateSelectionCallback, CitySelectionCallback
)
from bot.keyboards import (
    build_countries_keyboard,
    build_filter_selection_keyboard,
    build_proxy_purchase_keyboard,
    build_proxy_pagination_keyboard,
    build_proxy_history_actions_keyboard,
    get_country_name,
    build_back_to_main_menu_keyboard,
    build_purchase_success_keyboard,
    build_states_list_keyboard,
    build_cities_list_keyboard
)
from bot.services.api_client import BackendAPIClient, APITimeoutError, APINetworkError
from bot.states import Socks5States
from bot.utils.formatters import (
    format_proxy_details,
    format_purchase_success,
    format_no_results_message
)
from bot.utils.validators import (
    validate_state_name,
    validate_city_name,
    validate_zip_code
)
from bot.utils.country_mapper import get_country_name_from_code
from bot.core.config import bot_settings
from bot.core.logging_config import get_logger

logger = get_logger(__name__)

router = Router(name="socks5")


@router.callback_query(MenuCallback.filter(F.action == "socks5"))
async def callback_socks5_menu(callback: CallbackQuery, state: FSMContext):
    """Show SOCKS5 main menu with countries or history.
    
    Args:
        callback: Callback query
        state: FSM context
    """
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = [
        [InlineKeyboardButton(
            text=_("🌍 ВЫБРАТЬ СТРАНУ"),
            callback_data=CountryCallback(proxy_type="socks5", country_code="list", page=1).pack()
        )],
        [InlineKeyboardButton(
            text=_("📜 ИСТОРИЯ SOCKS5"),
            callback_data=HistoryCallback(history_type="socks5", page=1).pack()
        )],
        [InlineKeyboardButton(
            text=_("◀️ НАЗАД"),
            callback_data=MenuCallback(action="back").pack()
        )],
    ]
    
    socks5_description = _(
        "🧦 <b>SOCKS5 прокси</b>\n\n"
        "• Все адреса — с реальных домашних ПК, без роутеров и IoT\n"
        "• Более 350 000 чистейших IP из 100 стран\n"
        "• Протокол SOCKS5\n"
        "• Возврат средств в течение 1 часа, если прокси ушли в оффлайн\n"
        "• Чистейшие IP на рынке. Подходят под максимально требовательные задачи\n\n"
        "Выберите действие:"
    )
    await callback.message.edit_text(
        socks5_description,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    
    await callback.answer()


@router.callback_query(CountryCallback.filter(F.proxy_type == "socks5"))
async def callback_select_country(
    callback: CallbackQuery,
    callback_data: CountryCallback,
    state: FSMContext,
    api_client: BackendAPIClient
):
    """Handle country selection for SOCKS5.

    Args:
        callback: Callback query
        callback_data: Parsed callback data
        state: FSM context
        api_client: API client
    """
    country_code = callback_data.country_code
    page = callback_data.page

    if country_code == "list":
        # Show country list
        await callback.message.edit_text(
            _("🌍 <b>Выберите страну</b>\n\nВыберите страну для покупки SOCKS5 прокси:"),
            reply_markup=build_countries_keyboard("socks5", page)
        )
    else:
        # Country selected, save to state and show filter menu
        country_name = get_country_name(country_code)
        await state.update_data(
            country_code=country_code,
            country_name=country_name,
            # Clear any previous filters
            filter_type=None,
            filter_value=None
        )

        # Show filter selection menu
        await state.set_state(Socks5States.waiting_filter_choice)
        await callback.message.edit_text(
            _("🔍 <b>Найти прокси по:</b>\n\nВыберите способ фильтрации прокси:"),
            reply_markup=build_filter_selection_keyboard("socks5", country_code)
        )

    await callback.answer()


@router.callback_query(PaginationCallback.filter(F.page_type == "countries"))
async def callback_countries_pagination(
    callback: CallbackQuery,
    callback_data: PaginationCallback
):
    """Handle country list pagination.

    Args:
        callback: Callback query
        callback_data: Parsed callback data
    """
    proxy_type = callback_data.extra or "socks5"
    page = callback_data.page

    await callback.message.edit_reply_markup(
        reply_markup=build_countries_keyboard(proxy_type, page)
    )

    await callback.answer()


@router.callback_query(StateSelectionCallback.filter(F.proxy_type == "socks5"))
async def callback_socks5_state_select(
    callback: CallbackQuery,
    callback_data: StateSelectionCallback,
    api_client: BackendAPIClient,
    state: FSMContext
):
    """Handle SOCKS5 state selection from buttons - show proxies in that state.

    Args:
        callback: Callback query
        callback_data: Parsed callback data
        api_client: API client
        state: FSM context
    """
    state_name = callback_data.state_name
    country_code = callback_data.country_code

    try:
        # Always use English country name for API calls (not Russian display name from state)
        country_name = get_country_name_from_code(country_code)

        logger.info(f"SOCKS5 state selection: country_code={country_code}, country_name={country_name}, state_name={state_name}")

        # Fetch proxies for selected state
        result = await api_client.get_socks5_products(
            country=country_name,
            state=state_name,
            page=1,
            page_size=bot_settings.PROXIES_PER_PAGE
        )

        logger.info(f"SOCKS5 state selection result: {len(result.get('products', []))} products")

        proxies = result.get("products", [])
        has_more = result.get("has_more", False)

        if not proxies:
            # No proxies in this state
            await callback.answer(
                _("❌ Нет доступных прокси в этом штате/регионе"),
                show_alert=True
            )
            return

        # Save state to FSM
        await state.update_data(
            state_name=state_name,
            filter_type="state",
            filter_value=state_name,
            current_page=1,
            has_more=has_more
        )
        await state.set_state(Socks5States.browsing_proxies)

        # Delete the current message and send proxy list
        await callback.message.delete()
        await _send_proxy_list(callback.message, proxies, state)

        await callback.answer()

    except Exception as e:
        logger.error(f"Error selecting SOCKS5 state {state_name}: {e}")
        await callback.answer(_("Ошибка при загрузке прокси"), show_alert=True)


@router.callback_query(CitySelectionCallback.filter(F.proxy_type == "socks5"))
async def callback_socks5_city_select(
    callback: CallbackQuery,
    callback_data: CitySelectionCallback,
    api_client: BackendAPIClient,
    state: FSMContext
):
    """Handle SOCKS5 city selection from buttons."""
    # NOTE: This handler is currently unused as filter system is disabled
    try:
        state_data = await state.get_data()
        country_name = state_data.get("country_name")
        if not country_name:
            country_name = get_country_name_from_code(callback_data.country_code)

        await callback.message.edit_text(_("⏳ Загрузка прокси..."))

        result = await api_client.get_socks5_products(
            country=country_name,
            state=callback_data.state_name,
            city=callback_data.city_name,
            page=1,
            page_size=bot_settings.PROXIES_PER_PAGE
        )
        proxies = result.get("products", [])
        has_more = result.get("has_more", False)

        if proxies:
            await state.update_data(
                filter_type="city",
                filter_value=callback_data.city_name,
                state_name=callback_data.state_name,
                current_page=1,
                has_more=has_more
            )
            await state.set_state(Socks5States.browsing_proxies)
            await _send_proxy_list(callback.message, proxies, state)
        else:
            await callback.message.edit_text(
                format_no_results_message("city"),
                reply_markup=build_cities_list_keyboard("socks5", callback_data.country_code, callback_data.state_name, [])
            )

        await callback.answer()
    except Exception as e:
        logger.error(f"Error selecting city: {e}")
        await callback.answer(_("Ошибка при загрузке"), show_alert=True)


@router.callback_query(FilterCallback.filter((F.proxy_type == "socks5") & (F.filter_type == "back_to_states")))
async def callback_back_to_states(
    callback: CallbackQuery,
    callback_data: FilterCallback,
    state: FSMContext,
    api_client: BackendAPIClient
):
    """Handle back to states navigation from cities.

    Args:
        callback: Callback query
        callback_data: Parsed callback data
        state: FSM context
        api_client: API client
    """
    # NOTE: This handler is currently unused as filter system is disabled
    country_code = callback_data.country_code

    try:
        country_name_for_api = get_country_name_from_code(country_code)
        states = await api_client.get_available_states("socks5", country_name_for_api)
        label = _("штат") if country_code == "US" else _("регион")
        await callback.message.edit_text(
            _("📍 <b>Выберите {label}</b>\n\nВыберите {label} для покупки SOCKS5 прокси:").format(label=label),
            reply_markup=build_states_list_keyboard("socks5", country_code, states)
        )
        await state.set_state(Socks5States.waiting_state_selection)
    except Exception as e:
        logger.error(f"Error loading states: {e}")
        await callback.message.edit_text(
            _("🔍 <b>Найти прокси по:</b>\n\nВыберите способ фильтрации прокси:"),
            reply_markup=build_filter_selection_keyboard("socks5", country_code)
        )
        await state.set_state(Socks5States.waiting_filter_choice)
    await callback.answer()


@router.callback_query(FilterCallback.filter((F.proxy_type == "socks5") & (F.filter_type == "back_to_filter")))
async def callback_back_to_filter(
    callback: CallbackQuery,
    callback_data: FilterCallback,
    state: FSMContext,
    api_client: BackendAPIClient
):
    """Handle back navigation from purchase success to filter selection.

    Keeps the purchased proxy message visible and sends a new message with filter options.

    Args:
        callback: Callback query
        callback_data: Parsed callback data
        state: FSM context
        api_client: API client
    """
    country_code = callback_data.country_code or "US"

    try:
        # Remove buttons from the purchase message (keep the proxy info visible)
        await callback.message.edit_reply_markup(reply_markup=None)

        # Get stored filter info from state
        state_data = await state.get_data()
        prev_filter_type = state_data.get("filter_type")
        country_name_for_api = get_country_name_from_code(country_code)

        if prev_filter_type == "state":
            # Return to state selection - send NEW message
            from bot.utils.us_states import get_states_with_counts

            # Fetch states with proper proxy_type (UPPERCASE)
            api_states = await api_client.get_available_states(
                proxy_type="SOCKS5",
                country=country_name_for_api
            )

            # For US - merge with full states list, for others - format properly
            if country_code == "US":
                states = get_states_with_counts(api_states)
            else:
                states = []
                for s in api_states:
                    state_name = s.get("state", "")
                    states.append({
                        "state": state_name,
                        "abbr": state_name[:2].upper() if state_name else "??",
                        "count": s.get("count", 0)
                    })

            await callback.message.answer(
                _("🔍 <b>Название фильтра: STATE</b>\n\nℹ️ Выберите штат/регион:"),
                reply_markup=build_states_list_keyboard("socks5", country_code, states)
            )
            await state.set_state(Socks5States.waiting_state_selection)
        elif prev_filter_type == "city":
            # Return to city input - send NEW message
            await callback.message.answer(
                _("🏙 <b>Введите название города</b>\n\n"
                  "Напишите название города для поиска SOCKS5 прокси:")
            )
            await state.set_state(Socks5States.waiting_city_input)
        elif prev_filter_type == "zip":
            # Return to zip input - send NEW message
            await callback.message.answer(
                _("📮 <b>Введите ZIP код</b>\n\n"
                  "Напишите ZIP код для поиска SOCKS5 прокси:")
            )
            await state.set_state(Socks5States.waiting_zip_input)
        else:
            # Default: return to filter selection menu - send NEW message
            await callback.message.answer(
                _("🔍 <b>Найти прокси по:</b>\n\nВыберите способ фильтрации прокси:"),
                reply_markup=build_filter_selection_keyboard("socks5", country_code)
            )
            await state.set_state(Socks5States.waiting_filter_choice)

    except Exception as e:
        logger.error(f"Error in back_to_filter: {e}")
        # Fallback to filter selection menu - send NEW message
        await callback.message.answer(
            _("🔍 <b>Найти прокси по:</b>\n\nВыберите способ фильтрации прокси:"),
            reply_markup=build_filter_selection_keyboard("socks5", country_code)
        )
        await state.set_state(Socks5States.waiting_filter_choice)

    await callback.answer()


@router.callback_query(FilterCallback.filter(F.proxy_type == "socks5"))
async def callback_socks5_filter(
    callback: CallbackQuery,
    callback_data: FilterCallback,
    state: FSMContext,
    api_client: BackendAPIClient
):
    """Handle filter type selection for SOCKS5.

    Args:
        callback: Callback query
        callback_data: Parsed callback data
        state: FSM context
        api_client: API client
    """
    # NOTE: This handler is currently unused as filter system is disabled
    filter_type = callback_data.filter_type
    country_code = callback_data.country_code

    if filter_type == "back":
        # Back to country selection
        await state.clear()
        await callback.message.edit_text(
            _("🌍 <b>Выберите страну</b>\n\nВыберите страну для покупки SOCKS5 прокси:"),
            reply_markup=build_countries_keyboard("socks5", 1)
        )

    elif filter_type == "skip":
        # Skip filter - show all proxies for selected country
        try:
            await state.update_data(filter_type="skip")
            await state.set_state(Socks5States.browsing_proxies)

            await callback.message.edit_text(_("⏳ Загрузка прокси..."))

            # Convert country code to full name for API
            country_name = get_country_name_from_code(country_code)
            logger.debug(f"Skipping filters - fetching all SOCKS5 proxies: country_code={country_code}, country_name={country_name}")

            result = await api_client.get_socks5_products(
                country=country_name,
                page=1,
                page_size=bot_settings.PROXIES_PER_PAGE
            )

            proxies = result.get("products", [])
            has_more = result.get("has_more", False)

            if not proxies:
                await callback.message.edit_text(
                    _("❌ Прокси не найдены для выбранной страны."),
                    reply_markup=build_filter_selection_keyboard("socks5", country_code)
                )
            else:
                await state.update_data(current_page=1, has_more=has_more)
                # Delete "Loading..." message to avoid clutter
                await callback.message.delete()
                await _send_proxy_list(callback.message, proxies, state)

        except APITimeoutError as e:
            logger.error(f"Timeout fetching proxies: {e}")
            await callback.message.edit_text(
                _("⏱ Сервер не отвечает. Попробуйте позже."),
                reply_markup=build_filter_selection_keyboard("socks5", country_code)
            )
            await callback.answer()
        except APINetworkError as e:
            logger.error(f"Network error fetching proxies: {e}")
            await callback.message.edit_text(
                _("🌐 Ошибка сети. Проверьте подключение."),
                reply_markup=build_filter_selection_keyboard("socks5", country_code)
            )
            await callback.answer()
        except Exception as e:
            logger.error(f"Error fetching proxies: {e}")
            await callback.answer(_("Ошибка при загрузке прокси"), show_alert=True)

    elif filter_type == "random":
        # Random proxy - fetch and display
        try:
            await state.update_data(filter_type="random")
            await state.set_state(Socks5States.browsing_proxies)

            # Fetch random proxies
            # Convert country code to full name for API
            country_name = get_country_name_from_code(country_code)
            logger.debug(f"Fetching SOCKS5 proxies: country_code={country_code}, country_name={country_name}")

            result = await api_client.get_socks5_products(
                country=country_name,
                page=1,
                page_size=bot_settings.PROXIES_PER_PAGE
            )
            
            proxies = result.get("products", [])
            has_more = result.get("has_more", False)
            
            if not proxies:
                await callback.message.edit_text(
                    _("❌ Прокси не найдены для выбранной страны."),
                    reply_markup=build_filter_selection_keyboard("socks5", country_code)
                )
            else:
                await state.update_data(current_page=1, has_more=has_more)
                await _send_proxy_list(callback.message, proxies, state)

        except APITimeoutError as e:
            logger.error(f"Timeout fetching random proxies: {e}")
            await callback.message.edit_text(
                _("⏱ Сервер не отвечает. Попробуйте позже."),
                reply_markup=build_filter_selection_keyboard("socks5", country_code)
            )
            await callback.answer()
        except APINetworkError as e:
            logger.error(f"Network error fetching random proxies: {e}")
            await callback.message.edit_text(
                _("🌐 Ошибка сети. Проверьте подключение."),
                reply_markup=build_filter_selection_keyboard("socks5", country_code)
            )
            await callback.answer()
        except Exception as e:
            logger.error(f"Error fetching random proxies: {e}")
            await callback.answer(_("Ошибка при загрузке прокси"), show_alert=True)
    
    elif filter_type == "state":
        # Show state selection buttons with counts
        from bot.utils.us_states import get_states_with_counts

        try:
            # Get states with proxy counts from API
            country_name = get_country_name_from_code(country_code)
            api_states = await api_client.get_available_states(
                proxy_type="SOCKS5",
                country=country_name
            )

            # For US - merge with full states list, for others - use API response as-is
            if country_code == "US":
                states = get_states_with_counts(api_states)
            else:
                # For non-US countries, add abbr from state name (first 2 letters)
                states = []
                for s in api_states:
                    state_name = s.get("state", "")
                    states.append({
                        "state": state_name,
                        "abbr": state_name[:2].upper() if state_name else "??",
                        "count": s.get("count", 0)
                    })

            keyboard = build_states_list_keyboard("socks5", country_code, states)

            await callback.message.edit_text(
                _("🔍 <b>Название фильтра: STATE</b>\n\n"
                  "ℹ️ Выберите штат/регион:"),
                reply_markup=keyboard
            )

            await state.set_state(Socks5States.waiting_state_selection)

        except Exception as e:
            logger.error(f"Error loading states: {e}")
            await callback.message.edit_text(
                _("❌ Ошибка при загрузке списка штатов"),
                reply_markup=build_filter_selection_keyboard("socks5", country_code)
            )

    elif filter_type == "city":
        try:
            await callback.message.edit_text(
                _("📝 <b>Введите город</b>\n\n"
                  "Отправьте название города для поиска прокси:"),
                reply_markup=build_filter_selection_keyboard("socks5", country_code)
            )
        except Exception:
            # Message is already the same, just ignore
            pass

        await state.set_state(Socks5States.waiting_city_input)

    elif filter_type == "zip":
        try:
            await callback.message.edit_text(
                _("📝 <b>Введите ZIP код</b>\n\n"
                  "Отправьте ZIP код для поиска прокси:"),
                reply_markup=build_filter_selection_keyboard("socks5", country_code)
            )
        except Exception:
            # Message is already the same, just ignore
            pass

        await state.set_state(Socks5States.waiting_zip_input)
    
    await callback.answer()


@router.message(Socks5States.waiting_state_input)
async def process_state_input(
    message: Message,
    state: FSMContext,
    api_client: BackendAPIClient
):
    """Process state/region name input.
    
    Args:
        message: User message
        state: FSM context
        api_client: API client
    """
    # NOTE: This handler is currently unused as filter system is disabled
    is_valid, state_name, error = validate_state_name(message.text)
    
    if not is_valid:
        await message.answer(_(f"❌ {error}\n\nПопробуйте еще раз:"))
        return
    
    # Fetch proxies by state
    state_data = await state.get_data()
    country_code = state_data.get("country_code")

    try:
        # Convert country code to full name for API
        country_name = get_country_name_from_code(country_code)
        logger.debug(f"Fetching SOCKS5 by state: country_code={country_code}, country_name={country_name}, state={state_name}")

        result = await api_client.get_socks5_products(
            country=country_name,
            state=state_name,
            page=1,
            page_size=bot_settings.PROXIES_PER_PAGE
        )
        
        proxies = result.get("products", [])
        has_more = result.get("has_more", False)
        
        if not proxies:
            await message.answer(
                format_no_results_message("state"),
                reply_markup=build_filter_selection_keyboard("socks5", country_code)
            )
        else:
            await state.update_data(
                filter_type="state",
                filter_value=state_name,
                current_page=1,
                has_more=has_more
            )
            await state.set_state(Socks5States.browsing_proxies)
            await _send_proxy_list(message, proxies, state)

    except APITimeoutError as e:
        logger.error(f"Timeout fetching proxies by state: {e}")
        await message.answer(
            _("⏱ Сервер не отвечает. Попробуйте позже."),
            reply_markup=build_filter_selection_keyboard("socks5", country_code)
        )

    except APINetworkError as e:
        logger.error(f"Network error fetching proxies by state: {e}")
        await message.answer(
            _("🌐 Ошибка сети. Проверьте подключение."),
            reply_markup=build_filter_selection_keyboard("socks5", country_code)
        )

    except Exception as e:
        logger.error(f"Error fetching proxies by state: {e}")
        await message.answer(
            _("❌ Ошибка при загрузке прокси. Попробуйте еще раз."),
            reply_markup=build_filter_selection_keyboard("socks5", country_code)
        )
        # Keep state for retry, don't clear


@router.message(Socks5States.waiting_city_input)
async def process_city_input(
    message: Message,
    state: FSMContext,
    api_client: BackendAPIClient
):
    """Process city name input.
    
    Args:
        message: User message
        state: FSM context
        api_client: API client
    """
    # NOTE: This handler is currently unused as filter system is disabled
    is_valid, city_name, error = validate_city_name(message.text)
    
    if not is_valid:
        await message.answer(_(f"❌ {error}\n\nПопробуйте еще раз:"))
        return
    
    state_data = await state.get_data()
    country_code = state_data.get("country_code")

    try:
        # Convert country code to full name for API
        country_name = get_country_name_from_code(country_code)
        logger.debug(f"Fetching SOCKS5 by city: country_code={country_code}, country_name={country_name}, city={city_name}")

        result = await api_client.get_socks5_products(
            country=country_name,
            city=city_name,
            page=1,
            page_size=bot_settings.PROXIES_PER_PAGE
        )
        
        proxies = result.get("products", [])
        has_more = result.get("has_more", False)
        
        if not proxies:
            await message.answer(
                format_no_results_message("city"),
                reply_markup=build_filter_selection_keyboard("socks5", country_code)
            )
        else:
            await state.update_data(
                filter_type="city",
                filter_value=city_name,
                current_page=1,
                has_more=has_more
            )
            await state.set_state(Socks5States.browsing_proxies)
            await _send_proxy_list(message, proxies, state)

    except APITimeoutError as e:
        logger.error(f"Timeout fetching proxies by city: {e}")
        await message.answer(
            _("⏱ Сервер не отвечает. Попробуйте позже."),
            reply_markup=build_filter_selection_keyboard("socks5", country_code)
        )

    except APINetworkError as e:
        logger.error(f"Network error fetching proxies by city: {e}")
        await message.answer(
            _("🌐 Ошибка сети. Проверьте подключение."),
            reply_markup=build_filter_selection_keyboard("socks5", country_code)
        )

    except Exception as e:
        logger.error(f"Error fetching proxies by city: {e}")
        await message.answer(
            _("❌ Ошибка при загрузке прокси. Попробуйте еще раз."),
            reply_markup=build_filter_selection_keyboard("socks5", country_code)
        )
        # Keep state for retry, don't clear


@router.message(Socks5States.waiting_zip_input)
async def process_zip_input(
    message: Message,
    state: FSMContext,
    api_client: BackendAPIClient
):
    """Process ZIP code input.
    
    Args:
        message: User message
        state: FSM context
        api_client: API client
    """
    # NOTE: This handler is currently unused as filter system is disabled
    is_valid, zip_code, error = validate_zip_code(message.text)
    
    if not is_valid:
        await message.answer(_(f"❌ {error}\n\nПопробуйте еще раз:"))
        return
    
    state_data = await state.get_data()
    country_code = state_data.get("country_code")

    try:
        # Convert country code to full name for API
        country_name = get_country_name_from_code(country_code)

        # Calculate ZIP range for user information
        try:
            zip_int = int(zip_code)
            zip_min = zip_int - 100
            zip_max = zip_int + 100
            logger.debug(f"Fetching SOCKS5 by zip range: country_code={country_code}, country_name={country_name}, zip={zip_code} (range: {zip_min}-{zip_max})")

            # Show range info to user
            await message.answer(_(f"🔍 Поиск прокси с ZIP {zip_min} - {zip_max}..."))
        except (ValueError, TypeError):
            logger.debug(f"Fetching SOCKS5 by zip (exact): country_code={country_code}, country_name={country_name}, zip={zip_code}")
            await message.answer(_(f"🔍 Поиск прокси с ZIP {zip_code}..."))

        result = await api_client.get_socks5_products(
            country=country_name,
            zip_code=zip_code,
            page=1,
            page_size=bot_settings.PROXIES_PER_PAGE
        )

        proxies = result.get("products", [])
        has_more = result.get("has_more", False)

        if not proxies:
            await message.answer(
                format_no_results_message("zip"),
                reply_markup=build_filter_selection_keyboard("socks5", country_code)
            )
        else:
            await state.update_data(
                filter_type="zip",
                filter_value=zip_code,
                current_page=1,
                has_more=has_more
            )
            await state.set_state(Socks5States.browsing_proxies)
            await _send_proxy_list(message, proxies, state)

    except APITimeoutError as e:
        logger.error(f"Timeout fetching proxies by zip: {e}")
        await message.answer(
            _("⏱ Сервер не отвечает. Попробуйте позже."),
            reply_markup=build_filter_selection_keyboard("socks5", country_code)
        )

    except APINetworkError as e:
        logger.error(f"Network error fetching proxies by zip: {e}")
        await message.answer(
            _("🌐 Ошибка сети. Проверьте подключение."),
            reply_markup=build_filter_selection_keyboard("socks5", country_code)
        )

    except Exception as e:
        logger.error(f"Error fetching proxies by zip: {e}")
        await message.answer(
            _("❌ Ошибка при загрузке прокси. Попробуйте еще раз."),
            reply_markup=build_filter_selection_keyboard("socks5", country_code)
        )
        # Keep state for retry, don't clear


async def _send_proxy_list(target, proxies: list, state: FSMContext):
    """Send list of proxies to user.

    Args:
        target: Message object to send replies to
        proxies: List of proxy products
        state: FSM context
    """
    try:
        # Track all message IDs for cleanup after purchase
        message_ids = []

        for idx, proxy in enumerate(proxies):
            proxy_text = format_proxy_details(proxy)
            price = proxy.get("price", 2.0)
            keyboard = build_proxy_purchase_keyboard(proxy.get("product_id"), price)

            # Send each proxy as a new message and track ID
            msg = await target.answer(proxy_text, reply_markup=keyboard)
            message_ids.append(msg.message_id)

        # Send pagination message after all proxies
        state_data = await state.get_data()
        current_page = state_data.get("current_page", 1)
        has_more = state_data.get("has_more", False)

        pagination_msg = await target.answer(
            _("Посмотреть другие варианты"),
            reply_markup=build_proxy_pagination_keyboard(current_page, has_more)
        )
        message_ids.append(pagination_msg.message_id)

        # Save message IDs to state for cleanup
        await state.update_data(proxy_list_message_ids=message_ids)
    except Exception as e:
        logger.error(f"Error sending proxy list: {e}", exc_info=True)
        raise


@router.callback_query(ProxyCallback.filter(F.action == "buy"))
async def callback_buy_proxy(
    callback: CallbackQuery,
    callback_data: ProxyCallback,
    api_client: BackendAPIClient,
    state: FSMContext
):
    """Handle proxy purchase.

    Args:
        callback: Callback query
        callback_data: Parsed callback data
        api_client: API client
        state: FSM context
    """
    proxy_id = callback_data.proxy_id

    try:
        # Get state data before purchase (for cleanup and back button)
        state_data = await state.get_data()
        message_ids = state_data.get("proxy_list_message_ids", [])
        country_code = state_data.get("country_code", "US")

        # Delete all other proxy messages (except current one)
        current_message_id = callback.message.message_id
        for msg_id in message_ids:
            if msg_id != current_message_id:
                try:
                    await callback.bot.delete_message(callback.message.chat.id, msg_id)
                except Exception:
                    pass  # Ignore errors (message may already be deleted)

        # Purchase proxy
        await callback.message.edit_text(_("⏳ Обработка покупки..."))

        purchase_result = await api_client.purchase_socks5(proxy_id)

        # Format credentials from proxies list
        proxies_list = purchase_result.get("proxies", [])
        proxy_credentials = None
        if proxies_list:
            p = proxies_list[0]
            proxy_credentials = f"{p.get('ip')}:{p.get('port')}@{p.get('login')}:{p.get('password')}"

        # Format success message
        success_text = format_purchase_success(
            purchase_id=purchase_result.get("order_id"),  # API returns order_id, not purchase_id
            price=purchase_result.get("price"),
            country=purchase_result.get("country"),
            state=purchase_result.get("state"),
            city=purchase_result.get("city"),
            zip_code=purchase_result.get("zip"),
            proxy_credentials=proxy_credentials
        )

        # Use keyboard with Main Menu and Back buttons
        await callback.message.edit_text(
            success_text,
            reply_markup=build_purchase_success_keyboard(country_code)
        )

        # Clear message IDs from state but keep filter data for Back button
        await state.update_data(proxy_list_message_ids=[])

        await callback.answer(_("✅ Покупка успешна!"))
    
    except Exception as e:
        logger.error(f"Error purchasing proxy: {e}")
        error_msg = str(e)

        # Check for specific error types
        if "503" in error_msg or "Service Unavailable" in error_msg:
            await callback.message.edit_text(
                _("❌ Этот прокси временно недоступен. Попробуйте выбрать другой."),
                reply_markup=build_back_to_main_menu_keyboard()
            )
        elif "Insufficient balance" in error_msg:
            from bot.keyboards.payment import build_insufficient_balance_keyboard
            await callback.message.edit_text(
                _("❌ Недостаточно средств на балансе.\n\n"
                  "Пополните баланс для продолжения покупки."),
                reply_markup=build_insufficient_balance_keyboard()
            )
        else:
            await callback.message.edit_text(
                _("❌ Попробуйте еще раз, или напишите в поддержку"),
                reply_markup=build_back_to_main_menu_keyboard()
            )
        await callback.answer()


@router.callback_query(ProxyCallback.filter(F.action == "show_more"))
async def callback_show_more_proxies(
    callback: CallbackQuery,
    callback_data: ProxyCallback,
    api_client: BackendAPIClient,
    state: FSMContext
):
    """Load and show more proxies.
    
    Args:
        callback: Callback query
        callback_data: Parsed callback data
        api_client: API client
        state: FSM context
    """
    page = callback_data.page
    state_data = await state.get_data()
    
    country_code = state_data.get("country_code")
    filter_type = state_data.get("filter_type")
    filter_value = state_data.get("filter_value")
    
    try:
        # Convert country code to full name for API
        country_name = get_country_name_from_code(country_code)
        logger.debug(f"Loading more SOCKS5 proxies: country_code={country_code}, country_name={country_name}, page={page}")

        # Build filter params
        kwargs = {
            "country": country_name,
            "page": page,
            "page_size": bot_settings.PROXIES_PER_PAGE
        }

        if filter_type == "state":
            kwargs["state"] = filter_value
        elif filter_type == "city":
            kwargs["city"] = filter_value
        elif filter_type == "zip":
            kwargs["zip_code"] = filter_value

        result = await api_client.get_socks5_products(**kwargs)
        proxies = result.get("products", [])
        has_more = result.get("has_more", False)
        
        if proxies:
            await state.update_data(current_page=page, has_more=has_more)
            await _send_proxy_list(callback.message, proxies, state)
        else:
            await callback.answer(_("Больше прокси не найдено"), show_alert=True)
    
    except Exception as e:
        logger.error(f"Error loading more proxies: {e}")
        await callback.answer(_("Ошибка при загрузке"), show_alert=True)


@router.callback_query(ProxyCallback.filter(F.action == "back"))
async def callback_proxy_back(callback: CallbackQuery, state: FSMContext):
    """Handle back button from proxy browsing.
    
    Args:
        callback: Callback query
        state: FSM context
    """
    await state.clear()
    
    from bot.keyboards import build_main_menu_keyboard
    await callback.message.answer(
        _("🏠 <b>Главное меню</b>"),
        reply_markup=build_main_menu_keyboard()
    )
    
    await callback.answer()


@router.callback_query(HistoryCallback.filter(F.history_type == "socks5"))
async def callback_socks5_history(
    callback: CallbackQuery,
    api_client: BackendAPIClient
):
    """Show SOCKS5 purchase history.
    
    Args:
        callback: Callback query
        api_client: API client
    """
    try:
        history = await api_client.get_purchase_history(proxy_type="socks5", limit=20)
        purchases = history.get("purchases", [])
        
        if not purchases:
            await callback.message.edit_text(
                _("📜 <b>История SOCKS5</b>\n\nИстория покупок пуста."),
                reply_markup=build_proxy_history_actions_keyboard()
            )
        else:
            history_lines = []
            for purchase in purchases:
                proxy = purchase.get("proxy", "N/A")
                purchase_id = purchase.get("id", "N/A")
                timestamp = purchase.get("timestamp", "N/A")
                hours_left = purchase.get("hours_left", 0)
                
                history_lines.append(
                    f"<code>{proxy}</code> [<code>{purchase_id}</code>] {timestamp} ({hours_left}h left)"
                )
            
            history_text = (
                _("📜 <b>История SOCKS5</b>\n\n") +
                "\n".join(history_lines)
            )
            
            await callback.message.edit_text(
                history_text,
                reply_markup=build_proxy_history_actions_keyboard()
            )
        
        await callback.answer()
    
    except Exception as e:
        logger.error(f"Error loading SOCKS5 history: {e}")
        await callback.answer(_("Ошибка при загрузке истории"), show_alert=True)
