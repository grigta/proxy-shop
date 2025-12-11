"""Common handlers: cancel, help, language, unknown messages."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from bot.keyboards import build_main_menu_keyboard

router = Router(name="common")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Handle /cancel command to reset FSM state.
    
    Args:
        message: Incoming message
        state: FSM context
    """
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(
            _("Нет активных операций для отмены."),
            reply_markup=build_main_menu_keyboard()
        )
        return
    
    await state.clear()
    await message.answer(
        _("Операция отменена."),
        reply_markup=build_main_menu_keyboard()
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command.
    
    Args:
        message: Incoming message
    """
    help_text = _(
        "🤖 <b>Помощь по использованию бота</b>\n\n"
        "<b>Основные команды:</b>\n"
        "/start - Главное меню\n"
        "/cancel - Отменить текущую операцию\n"
        "/help - Показать эту справку\n\n"
        "<b>Разделы:</b>\n"
        "👤 АККАУНТ - Просмотр профиля, пополнение баланса, история\n"
        "🧦 SOCKS5 - Покупка SOCKS5 прокси\n"
        "🔐 PPTP - Покупка PPTP прокси\n"
        "💬 ПОДДЕРЖКА - Связь с технической поддержкой\n"
        "📜 ПРАВИЛА - Правила использования сервиса\n\n"
        "Для навигации используйте кнопки меню."
    )
    
    await message.answer(help_text, reply_markup=build_main_menu_keyboard())


@router.message(Command("lang"))
async def cmd_language(message: Message):
    """Handle /lang command to change language.
    
    Args:
        message: Incoming message
    """
    # TODO: Implement language selection
    await message.answer(
        _("Выбор языка будет доступен в следующей версии.\n"
          "Language selection will be available in the next version."),
        reply_markup=build_main_menu_keyboard()
    )


@router.message()
async def unknown_message(message: Message):
    """Handle unknown text messages.
    
    Args:
        message: Incoming message
    """
    await message.answer(
        _("Я не понимаю эту команду. Используйте /help для справки."),
        reply_markup=build_main_menu_keyboard()
    )
