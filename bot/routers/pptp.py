"""PPTP proxy purchase flow handlers."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _
from typing import Dict, Any

from bot.keyboards.callback_data import (
    MenuCallback, PPTPRegionCallback, FilterCallback,
    ProxyCallback, StateSelectionCallback, HistoryCallback,
    CatalogSelectionCallback, PPTPListCallback
)
from bot.keyboards import (
    build_pptp_region_keyboard,
    build_filter_selection_keyboard,
    build_states_list_keyboard,
    build_back_to_main_menu_keyboard,
    build_proxy_history_actions_keyboard
)
from bot.services.api_client import BackendAPIClient, APITimeoutError, APINetworkError
from bot.states import PPTPStates
from bot.utils.formatters import (
    format_pptp_info,
    format_purchase_success,
    format_no_results_message,
    format_zip_list
)
from bot.utils.validators import validate_city_name, validate_zip_code
from bot.core.logging_config import get_logger

logger = get_logger(__name__)

router = Router(name="pptp")


@router.callback_query(MenuCallback.filter(F.action == "pptp"))
async def callback_pptp_menu(callback: CallbackQuery, state: FSMContext, api_client: BackendAPIClient):
    """Show PPTP catalogs selection.

    Args:
        callback: Callback query
        state: FSM context
        api_client: API client
    """
    from bot.keyboards.proxies import build_catalogs_list_keyboard

    try:
        # Get available catalogs
        catalogs_response = await api_client.get_catalogs(proxy_type="PPTP")
        catalogs = catalogs_response.get("catalogs", [])

        if not catalogs:
            # No catalogs available
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = [[InlineKeyboardButton(
                text=_("◀️ НАЗАД"),
                callback_data=MenuCallback(action="back").pack()
            )]]
            await callback.message.edit_text(
                _("❌ Нет доступных каталогов PPTP"),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
            await callback.answer()
            return

        # Build catalog selection keyboard
        keyboard = build_catalogs_list_keyboard(catalogs)

        # Show catalog selection
        await callback.message.edit_text(
            _("📚 <b>Выберите каталог PPTP</b>\n\n"
              "Доступные каталоги:"),
            reply_markup=keyboard
        )

        await state.set_state(PPTPStates.waiting_catalog_choice)
        await callback.answer()

    except Exception as e:
        logger.error(f"Error loading PPTP catalogs: {e}")
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = [[InlineKeyboardButton(
            text=_("◀️ НАЗАД"),
            callback_data=MenuCallback(action="back").pack()
        )]]
        await callback.message.edit_text(
            _("❌ Ошибка при загрузке каталогов"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        await callback.answer()


@router.callback_query(CatalogSelectionCallback.filter())
async def callback_catalog_select(
    callback: CallbackQuery,
    callback_data: CatalogSelectionCallback,
    state: FSMContext
):
    """Handle catalog selection - show filter menu or PPTP list.

    Args:
        callback: Callback query
        callback_data: Catalog selection data
        state: FSM context
    """
    from bot.keyboards.proxies import build_filter_selection_keyboard

    catalog_id = callback_data.catalog_id
    catalog_name = callback_data.catalog_name
    price = callback_data.price

    # Save catalog info to FSM
    await state.update_data(
        catalog_id=catalog_id,
        catalog_name=catalog_name,
        catalog_price=price,
        region="USA"  # Default region for PPTP
    )

    # Show filter selection menu
    keyboard = build_filter_selection_keyboard("pptp", "US")

    # Add validation button before the back button
    from aiogram.types import InlineKeyboardButton
    from bot.keyboards.callback_data import PPTPListCallback

    validate_button = [InlineKeyboardButton(
        text=_("✅ ПРОВЕРКА НА ВАЛИД"),
        callback_data=PPTPListCallback(
            catalog_id=catalog_id,
            action="validate_all",
            page=0,
            proxy_id=0
        ).pack()
    )]
    # Insert before last row (back button)
    keyboard.inline_keyboard.insert(-1, validate_button)

    await callback.message.edit_text(
        _(f"📦 <b>{catalog_name}</b>\n"
          f"Цена: ${price} за прокси\n\n"
          f"Выберите фильтр для поиска или пропустите фильтры:"),
        reply_markup=keyboard
    )

    await state.set_state(PPTPStates.waiting_filter_choice)
    await callback.answer()


@router.callback_query(PPTPRegionCallback.filter())
async def callback_pptp_region(
    callback: CallbackQuery,
    callback_data: PPTPRegionCallback,
    state: FSMContext
):
    """Handle PPTP region selection.
    
    Args:
        callback: Callback query
        callback_data: Parsed callback data
        state: FSM context
    """
    region = callback_data.region
    
    await state.update_data(region=region)
    await state.set_state(PPTPStates.waiting_filter_choice)
    
    # For PPTP, show filter selection directly (state/city/zip/random)
    await callback.message.edit_text(
        _(f"🔍 <b>PPTP {region}</b>\n\nВыберите способ фильтрации:"),
        reply_markup=build_filter_selection_keyboard("pptp", region)
    )
    
    await callback.answer()


@router.callback_query(FilterCallback.filter(F.proxy_type == "pptp"))
async def callback_pptp_filter(
    callback: CallbackQuery,
    callback_data: FilterCallback,
    state: FSMContext,
    api_client: BackendAPIClient
):
    """Handle filter type selection for PPTP.
    
    Args:
        callback: Callback query
        callback_data: Parsed callback data
        state: FSM context
        api_client: API client
    """
    filter_type = callback_data.filter_type
    state_data = await state.get_data()
    region = state_data.get("region", "USA")
    
    if filter_type == "back":
        await state.clear()
        await callback_pptp_menu(callback, state, api_client)

    elif filter_type == "skip":
        # Skip filters - show PPTP list for catalog
        from bot.keyboards.proxies import build_pptp_list_keyboard

        try:
            catalog_id = state_data.get("catalog_id")
            catalog_name = state_data.get("catalog_name", "PPTP")

            if not catalog_id:
                await callback.answer(_("Ошибка: каталог не выбран"), show_alert=True)
                return

            # Fetch PPTP proxies from catalog
            result = await api_client.get_pptp_products(
                region=region,
                catalog_id=catalog_id,
                page=1,
                page_size=10
            )

            proxies = result.get("products", [])
            total = result.get("total", 0)

            if not proxies:
                await callback.message.edit_text(
                    _("❌ В этом каталоге нет доступных PPTP прокси"),
                    reply_markup=build_filter_selection_keyboard("pptp", region)
                )
                await callback.answer()
                return

            # Build PPTP list keyboard
            keyboard = build_pptp_list_keyboard(proxies, catalog_id, 1, total, 10)

            await callback.message.edit_text(
                _(f"📦 <b>{catalog_name}</b>\n"
                  f"Регион: {region}\n"
                  f"Всего прокси: {total}\n\n"
                  f"Выберите прокси для покупки:"),
                reply_markup=keyboard
            )

            await state.set_state(PPTPStates.browsing_pptp_list)
            await callback.answer()

        except Exception as e:
            logger.error(f"Error loading PPTP list: {e}")
            await callback.message.edit_text(
                _("❌ Ошибка при загрузке списка прокси"),
                reply_markup=build_filter_selection_keyboard("pptp", region)
            )
            await callback.answer()

    elif filter_type == "state":
        # Show state selection buttons with counts
        from bot.utils.us_states import get_states_with_counts

        try:
            catalog_id = state_data.get("catalog_id")

            # Get states with proxy counts from API
            api_states = await api_client.get_available_states(
                proxy_type="PPTP",
                country="US",
                catalog_id=catalog_id
            )

            # Merge with full US states list (all 50 states)
            states = get_states_with_counts(api_states)

            keyboard = build_states_list_keyboard("pptp", "US", states)

            await callback.message.edit_text(
                _("🔍 <b>Название фильтра: STATE</b>\n\n"
                  "ℹ️ Выберите штат:"),
                reply_markup=keyboard
            )

            await state.set_state(PPTPStates.browsing_states)

        except Exception as e:
            logger.error(f"Error loading states: {e}")
            await callback.message.edit_text(
                _("❌ Ошибка при загрузке списка штатов"),
                reply_markup=build_filter_selection_keyboard("pptp", region)
            )
    
    elif filter_type == "city":
        try:
            catalog_name = state_data.get("catalog_name", "")

            await callback.message.edit_text(
                _(f"📝 <b>Введите город</b>\n\n"
                  f"Регион: {region}\n"
                  f"Каталог: {catalog_name}\n\n"
                  f"Пример: San Francisco"),
                reply_markup=build_filter_selection_keyboard("pptp", region)
            )
        except Exception:
            # Message is already the same, just ignore
            pass

        await state.set_state(PPTPStates.waiting_city_input)

    elif filter_type == "zip":
        try:
            await callback.message.edit_text(
                _("📮 <b>Введите ZIP код</b>\n\n"
                  "Пример: 90210"),
                reply_markup=build_filter_selection_keyboard("pptp", region)
            )
        except Exception:
            # Message is already the same, just ignore
            pass

        await state.set_state(PPTPStates.waiting_zip_input)
    
    elif filter_type == "random":
        # Purchase random PPTP
        try:
            await callback.message.edit_text(_("⏳ Обработка покупки..."))
            
            purchase_result = await api_client.purchase_pptp(region=region)

            # Get price from purchase result
            price = purchase_result.get("price", 5.0)

            # Extract credentials from proxies list
            proxies_list = purchase_result.get("proxies", [])
            proxy_credentials = None
            if proxies_list:
                p = proxies_list[0]
                # Format: IP:Login:Pass:State:City:Zip
                proxy_credentials = f"{p.get('ip', '')}:{p.get('login', '')}:{p.get('password', '')}:{p.get('state', '')}:{p.get('city', '')}:{p.get('zip', '')}"

            success_text = format_purchase_success(
                purchase_id=purchase_result.get("product_id"),
                price=price,
                country=region,
                state=proxies_list[0].get('state') if proxies_list else "RANDOM",
                city=proxies_list[0].get('city') if proxies_list else None,
                zip_code=proxies_list[0].get('zip') if proxies_list else None,
                proxy_credentials=proxy_credentials
            )

            # Delete old message and send new success message
            await callback.message.delete()
            await callback.message.answer(
                success_text,
                reply_markup=build_back_to_main_menu_keyboard()
            )

            await state.clear()
            await callback.answer(_("✅ Покупка успешна!"))
        
        except Exception as e:
            logger.error(f"Error purchasing random PPTP: {e}")
            error_msg = str(e)
            if "Insufficient balance" in error_msg:
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

    await callback.answer()


@router.callback_query(StateSelectionCallback.filter(F.proxy_type == "pptp"))
async def callback_pptp_state_select(
    callback: CallbackQuery,
    callback_data: StateSelectionCallback,
    api_client: BackendAPIClient,
    state: FSMContext
):
    """Handle PPTP state selection - show proxies in that state.

    Args:
        callback: Callback query
        callback_data: Parsed callback data
        api_client: API client
        state: FSM context
    """
    from bot.keyboards.proxies import build_pptp_list_keyboard

    state_name = callback_data.state_name
    region = callback_data.country_code

    state_data = await state.get_data()
    catalog_id = state_data.get("catalog_id")
    catalog_name = state_data.get("catalog_name", "PPTP")

    try:
        # Get PPTP proxies filtered by state
        result = await api_client.get_pptp_products(
            region=region,
            catalog_id=catalog_id,
            state=state_name,
            page=1,
            page_size=10
        )

        proxies = result.get("products", [])
        total = result.get("total", 0)

        if not proxies:
            # No proxies in this state
            await callback.answer(
                _("❌ Нет доступных прокси в этом штате"),
                show_alert=True
            )
            return

        # Save selected state for reference
        await state.update_data(selected_state=state_name)

        # Build PPTP list keyboard
        keyboard = build_pptp_list_keyboard(proxies, catalog_id, 1, total, 10)

        await callback.message.edit_text(
            _(f"📦 <b>{catalog_name}</b>\n"
              f"Штат: {state_name}\n"
              f"Всего прокси: {total}\n\n"
              f"Выберите прокси для покупки:"),
            reply_markup=keyboard
        )

        await state.set_state(PPTPStates.browsing_pptp_list)
        await callback.answer()

    except Exception as e:
        logger.error(f"Error selecting PPTP state {state_name}: {e}")
        await callback.answer(_("Ошибка при загрузке прокси"), show_alert=True)


@router.callback_query(ProxyCallback.filter(F.action == "buy_pptp"))
async def callback_buy_pptp(
    callback: CallbackQuery,
    api_client: BackendAPIClient,
    state: FSMContext
):
    """Handle PPTP purchase without filters.

    Args:
        callback: Callback query
        api_client: API client
        state: FSM context
    """
    try:
        await callback.message.edit_text(_("⏳ Обработка покупки..."))

        # Purchase random PPTP from USA region
        purchase_result = await api_client.purchase_pptp(region="USA")

        # Get price from purchase result
        price = purchase_result.get("price", 5.0)

        # Extract credentials from proxies list
        proxies_list = purchase_result.get("proxies", [])
        proxy_credentials = None
        if proxies_list:
            p = proxies_list[0]
            # Format: IP:Login:Pass:State:City:Zip
            proxy_credentials = f"{p.get('ip', '')}:{p.get('login', '')}:{p.get('password', '')}:{p.get('state', '')}:{p.get('city', '')}:{p.get('zip', '')}"

        success_text = format_purchase_success(
            purchase_id=purchase_result.get("product_id"),
            price=price,
            country="USA",
            state=proxies_list[0].get('state') if proxies_list else None,
            city=proxies_list[0].get('city') if proxies_list else None,
            zip_code=proxies_list[0].get('zip') if proxies_list else None,
            proxy_credentials=proxy_credentials
        )

        # Delete old message with proxy details and send new success message
        await callback.message.delete()
        await callback.message.answer(
            success_text,
            reply_markup=build_back_to_main_menu_keyboard()
        )

        await state.clear()
        await callback.answer(_("✅ Покупка успешна!"))

    except Exception as e:
        logger.error(f"Error purchasing PPTP: {e}")
        error_msg = str(e)
        if "Insufficient balance" in error_msg:
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


@router.callback_query(PPTPListCallback.filter())
async def callback_pptp_list_handler(
    callback: CallbackQuery,
    callback_data: PPTPListCallback,
    state: FSMContext,
    api_client: BackendAPIClient
):
    """Handle PPTP list actions (pagination and proxy selection).

    Args:
        callback: Callback query
        callback_data: PPTP list callback data
        state: FSM context
        api_client: API client
    """
    from bot.keyboards.proxies import build_pptp_list_keyboard

    action = callback_data.action
    catalog_id = callback_data.catalog_id
    page = callback_data.page
    proxy_id = callback_data.proxy_id

    state_data = await state.get_data()
    region = state_data.get("region", "USA")
    catalog_name = state_data.get("catalog_name", "PPTP")
    catalog_price = state_data.get("catalog_price", "5.0")

    if action in ["show_list", "next_page", "prev_page"]:
        # Show/refresh PPTP list
        try:
            result = await api_client.get_pptp_products(
                region=region,
                catalog_id=catalog_id,
                page=page,
                page_size=10
            )

            proxies = result.get("products", [])
            total = result.get("total", 0)

            if not proxies:
                await callback.answer(_("На этой странице нет прокси"), show_alert=True)
                return

            keyboard = build_pptp_list_keyboard(proxies, catalog_id, page, total, 10)

            await callback.message.edit_text(
                _(f"📦 <b>{catalog_name}</b>\n"
                  f"Регион: {region}\n"
                  f"Всего прокси: {total}\n"
                  f"Страница: {page}\n\n"
                  f"Выберите прокси для покупки:"),
                reply_markup=keyboard
            )

            await callback.answer()

        except Exception as e:
            logger.error(f"Error loading PPTP list page {page}: {e}")
            await callback.answer(_("Ошибка при загрузке списка"), show_alert=True)

    elif action == "select_proxy":
        # Purchase selected proxy
        try:
            await callback.message.edit_text(_("⏳ Обработка покупки..."))

            # Purchase specific proxy by product_id
            purchase_result = await api_client.purchase_pptp(
                product_id=proxy_id
            )

            price = purchase_result.get("price", catalog_price)

            # Extract credentials from proxies list
            proxies_list = purchase_result.get("proxies", [])
            proxy_credentials = None
            if proxies_list:
                p = proxies_list[0]
                # Format: IP:Login:Pass:State:City:Zip
                proxy_credentials = f"{p.get('ip', '')}:{p.get('login', '')}:{p.get('password', '')}:{p.get('state', '')}:{p.get('city', '')}:{p.get('zip', '')}"

            success_text = format_purchase_success(
                purchase_id=purchase_result.get("product_id"),
                price=price,
                country=region,
                state=proxies_list[0].get('state') if proxies_list else None,
                city=proxies_list[0].get('city') if proxies_list else None,
                zip_code=proxies_list[0].get('zip') if proxies_list else None,
                proxy_credentials=proxy_credentials
            )

            # Delete old message and send new success message
            await callback.message.delete()
            await callback.message.answer(
                success_text,
                reply_markup=build_back_to_main_menu_keyboard()
            )

            await state.clear()
            await callback.answer(_("✅ Покупка успешна!"))

        except Exception as e:
            logger.error(f"Error purchasing PPTP proxy {proxy_id}: {e}")
            error_msg = str(e)
            if "Insufficient balance" in error_msg:
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

    elif action == "validate_all":
        # Validate all user's PPTP proxies from last 24 hours
        try:
            await callback.message.edit_text(_("⏳ Проверяем ваши PPTP прокси..."))

            result = await api_client.validate_all_pptp()

            validated_count = result.get("validated_count", 0)
            valid_count = result.get("valid_count", 0)
            invalid_count = result.get("invalid_count", 0)
            refunded_amount = result.get("refunded_amount", 0)

            if validated_count == 0:
                text = _("ℹ️ У вас нет PPTP прокси, купленных за последние 24 часа.")
            else:
                text = _(
                    f"✅ <b>Проверка завершена</b>\n\n"
                    f"📊 Проверено: {validated_count}\n"
                    f"✅ Работают: {valid_count}\n"
                    f"❌ Не работают (ушли в оффлайн): {invalid_count}\n"
                )
                if float(refunded_amount) > 0:
                    text += _(f"\n💰 Возвращено на баланс: ${float(refunded_amount):.2f}")

            await callback.message.edit_text(
                text,
                reply_markup=build_back_to_main_menu_keyboard()
            )
            await callback.answer()

        except Exception as e:
            logger.error(f"Error validating PPTP proxies: {e}")
            await callback.message.edit_text(
                _("❌ Ошибка при проверке прокси. Попробуйте позже."),
                reply_markup=build_back_to_main_menu_keyboard()
            )
            await callback.answer()


@router.message(PPTPStates.waiting_state_input)
async def process_pptp_state_input(
    message: Message,
    state: FSMContext,
    api_client: BackendAPIClient
):
    """Process PPTP state name input (text).

    Args:
        message: User message
        state: FSM context
        api_client: API client
    """
    from bot.utils.validators import validate_state_name
    from bot.keyboards.proxies import build_pptp_list_keyboard

    is_valid, state_name, error = validate_state_name(message.text)

    if not is_valid:
        await message.answer(_(f"❌ {error}\n\nПопробуйте еще раз:"))
        return

    state_data = await state.get_data()
    region = state_data.get("region", "USA")
    catalog_id = state_data.get("catalog_id")
    catalog_name = state_data.get("catalog_name", "PPTP")

    try:
        # Get PPTP proxies filtered by state
        result = await api_client.get_pptp_products(
            region=region,
            catalog_id=catalog_id,
            state=state_name,
            page=1,
            page_size=10
        )

        proxies = result.get("products", [])
        total = result.get("total", 0)

        if not proxies:
            await message.answer(
                _(f"❌ Не найдено PPTP прокси в штате {state_name}\n\n"
                  f"Попробуйте другой штат или вернитесь к выбору фильтров"),
                reply_markup=build_filter_selection_keyboard("pptp", region)
            )
            return

        # Show PPTP list
        keyboard = build_pptp_list_keyboard(proxies, catalog_id, 1, total, 10)

        await message.answer(
            _(f"📦 <b>{catalog_name}</b>\n"
              f"Штат: {state_name}\n"
              f"Всего прокси: {total}\n\n"
              f"Выберите прокси для покупки:"),
            reply_markup=keyboard
        )

        await state.set_state(PPTPStates.browsing_pptp_list)

    except APITimeoutError:
        await message.answer(_("⏱ Сервер не отвечает. Попробуйте позже."))
    except APINetworkError:
        await message.answer(_("🌐 Ошибка сети. Проверьте подключение."))
    except Exception as e:
        logger.error(f"Error loading PPTP with state {state_name}: {e}")
        await message.answer(_("❌ Ошибка при загрузке PPTP. Попробуйте еще раз."))


@router.message(PPTPStates.waiting_city_input)
async def process_pptp_city_input(
    message: Message,
    state: FSMContext,
    api_client: BackendAPIClient
):
    """Process PPTP city name input.
    
    Args:
        message: User message
        state: FSM context
        api_client: API client
    """
    is_valid, city_name, error = validate_city_name(message.text)
    
    if not is_valid:
        await message.answer(_(f"❌ {error}\n\nПопробуйте еще раз:"))
        return
    
    state_data = await state.get_data()
    region = state_data.get("region")
    
    try:
        result = await api_client.get_pptp_products(region=region, city=city_name, page=1, page_size=1)
        pptp_list = result.get("products", [])
        
        if not pptp_list:
            await message.answer(
                format_no_results_message("city"),
                reply_markup=build_filter_selection_keyboard("pptp", region)
            )
        else:
            # Show first PPTP for purchase
            pptp = pptp_list[0]
            price = float(pptp.get("price", 5.0))
            pptp_text = format_pptp_info(pptp, city_name, price)

            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = [
                [InlineKeyboardButton(
                    text=f"💳 КУПИТЬ - {price:.2f}$",
                    callback_data=ProxyCallback(action="buy_pptp", proxy_id=pptp.get("product_id")).pack()
                )],
            ]

            # Save city_name in FSM state for purchase
            await state.update_data(selected_city=city_name)

            await message.answer(
                pptp_text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
            await state.set_state(PPTPStates.confirming_purchase)

    except APITimeoutError as e:
        logger.error(f"Timeout fetching PPTP by city: {e}")
        await message.answer(
            _("⏱ Сервер не отвечает. Попробуйте позже."),
            reply_markup=build_filter_selection_keyboard("pptp", region)
        )

    except APINetworkError as e:
        logger.error(f"Network error fetching PPTP by city: {e}")
        await message.answer(
            _("🌐 Ошибка сети. Проверьте подключение."),
            reply_markup=build_filter_selection_keyboard("pptp", region)
        )

    except Exception as e:
        logger.error(f"Error fetching PPTP by city: {e}")
        await message.answer(
            _("❌ Ошибка при загрузке PPTP. Попробуйте еще раз."),
            reply_markup=build_filter_selection_keyboard("pptp", region)
        )
        # Keep state for retry, don't clear


@router.message(PPTPStates.waiting_zip_input)
async def process_pptp_zip_input(
    message: Message,
    state: FSMContext,
    api_client: BackendAPIClient
):
    """Process PPTP ZIP code input.
    
    Args:
        message: User message
        state: FSM context
        api_client: API client
    """
    is_valid, zip_code, error = validate_zip_code(message.text)
    
    if not is_valid:
        await message.answer(_(f"❌ {error}\n\nПопробуйте еще раз:"))
        return
    
    state_data = await state.get_data()
    region = state_data.get("region")

    try:
        # Calculate ZIP range for user information
        try:
            zip_int = int(zip_code)
            zip_min = zip_int - 100
            zip_max = zip_int + 100
            logger.debug(f"Fetching PPTP by zip range: region={region}, zip={zip_code} (range: {zip_min}-{zip_max})")

            # Show range info to user
            await message.answer(_(f"🔍 Поиск прокси с ZIP {zip_min} - {zip_max}..."))
        except (ValueError, TypeError):
            logger.debug(f"Fetching PPTP by zip (exact): region={region}, zip={zip_code}")
            await message.answer(_(f"🔍 Поиск прокси с ZIP {zip_code}..."))

        result = await api_client.get_pptp_products(region=region, zip_code=zip_code, page=1, page_size=1)
        pptp_list = result.get("products", [])

        if not pptp_list:
            # Show all available ZIPs
            # TODO: Get all ZIPs from API
            await message.answer(
                _("К сожалению в списке прокси текущего ZIP нет.\n"
                  "Посмотрите список всех ZIP или попробуйте другие настройки."),
                reply_markup=build_filter_selection_keyboard("pptp", region)
            )
        else:
            pptp = pptp_list[0]
            price = float(pptp.get("price", 5.0))
            pptp_text = format_pptp_info(pptp, zip_code, price)

            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = [
                [InlineKeyboardButton(
                    text=f"💳 КУПИТЬ - {price:.2f}$",
                    callback_data=ProxyCallback(action="buy_pptp", proxy_id=pptp.get("product_id")).pack()
                )],
            ]

            # Save zip_code in FSM state for purchase
            await state.update_data(selected_zip=zip_code)

            await message.answer(
                pptp_text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
            )
            await state.set_state(PPTPStates.confirming_purchase)

    except APITimeoutError as e:
        logger.error(f"Timeout fetching PPTP by ZIP: {e}")
        await message.answer(
            _("⏱ Сервер не отвечает. Попробуйте позже."),
            reply_markup=build_filter_selection_keyboard("pptp", region)
        )

    except APINetworkError as e:
        logger.error(f"Network error fetching PPTP by ZIP: {e}")
        await message.answer(
            _("🌐 Ошибка сети. Проверьте подключение."),
            reply_markup=build_filter_selection_keyboard("pptp", region)
        )

    except Exception as e:
        logger.error(f"Error fetching PPTP by ZIP: {e}")
        await message.answer(
            _("❌ Ошибка при загрузке PPTP. Попробуйте еще раз."),
            reply_markup=build_filter_selection_keyboard("pptp", region)
        )
        # Keep state for retry, don't clear


@router.callback_query(HistoryCallback.filter(F.history_type == "pptp"))
async def callback_pptp_history(
    callback: CallbackQuery,
    api_client: BackendAPIClient
):
    """Show PPTP purchase history.
    
    Args:
        callback: Callback query
        api_client: API client
    """
    try:
        history = await api_client.get_purchase_history(proxy_type="pptp", limit=20)
        purchases = history.get("purchases", [])
        
        if not purchases:
            await callback.message.edit_text(
                _("📜 <b>История PPTP</b>\n\nИстория покупок пуста."),
                reply_markup=build_proxy_history_actions_keyboard()
            )
        else:
            history_lines = []
            for purchase in purchases:
                pptp = purchase.get("pptp", "N/A")
                timestamp = purchase.get("timestamp", "N/A")
                hours_left = purchase.get("hours_left", 0)
                
                history_lines.append(
                    f"<code>{pptp}</code> {timestamp} ({hours_left}h left)"
                )
            
            history_text = (
                _("📜 <b>История PPTP</b>\n\n") +
                "\n".join(history_lines)
            )
            
            await callback.message.edit_text(
                history_text,
                reply_markup=build_proxy_history_actions_keyboard()
            )
        
        await callback.answer()
    
    except Exception as e:
        logger.error(f"Error loading PPTP history: {e}")
        await callback.answer(_("Ошибка при загрузке истории"), show_alert=True)
