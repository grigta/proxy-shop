#!/usr/bin/env python3
"""
Скрипт для тестирования подключения к Heleket Payment API.

Использование:
    # Из корня проекта
    docker-compose exec backend python /app/scripts/test_heleket_api.py
    
    # Или внутри контейнера
    python /app/scripts/test_heleket_api.py

Что проверяется:
    1. Наличие всех необходимых переменных окружения
    2. Валидность формата HELEKET_MERCHANT_UUID
    3. Валидность формата HELEKET_API_KEY
    4. Подключение к API Heleket (создание тестового платежа)
    5. Правильность генерации подписи
"""

import asyncio
import sys
import os

# Добавляем путь к приложению для импорта
sys.path.insert(0, '/app')

from backend.core.heleket_client import HeleketAPIClient
from backend.core.config import settings
from decimal import Decimal
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_header(text: str):
    """Красивый заголовок"""
    line = "=" * 70
    print(f"\n{line}")
    print(f"  {text}")
    print(f"{line}\n")


def print_success(text: str):
    """Успешное сообщение"""
    print(f"✅ {text}")


def print_error(text: str):
    """Сообщение об ошибке"""
    print(f"❌ {text}")


def print_warning(text: str):
    """Предупреждение"""
    print(f"⚠️  {text}")


def print_info(text: str):
    """Информационное сообщение"""
    print(f"ℹ️  {text}")


async def test_heleket_connection():
    """Основная функция тестирования"""
    
    print_header("ТЕСТ ПОДКЛЮЧЕНИЯ К HELEKET PAYMENT API")
    
    # ========================================
    # 1. Проверка переменных окружения
    # ========================================
    print_info("Шаг 1: Проверка переменных окружения\n")
    
    required_vars = {
        'HELEKET_MERCHANT_UUID': settings.HELEKET_MERCHANT_UUID,
        'HELEKET_API_KEY': settings.HELEKET_API_KEY,
        'HELEKET_WEBHOOK_URL': settings.HELEKET_WEBHOOK_URL,
        'MIN_DEPOSIT_USD': str(settings.MIN_DEPOSIT_USD)
    }
    
    all_vars_present = True
    for var_name, var_value in required_vars.items():
        if not var_value or (isinstance(var_value, str) and var_value == ''):
            print_error(f"{var_name} не установлена!")
            all_vars_present = False
        else:
            # Маскируем чувствительные данные
            if var_name == 'HELEKET_API_KEY':
                display_value = f"{var_value[:20]}...{var_value[-10:]}" if len(var_value) > 30 else "***"
            elif var_name == 'HELEKET_MERCHANT_UUID':
                display_value = var_value
            else:
                display_value = var_value
            print_success(f"{var_name}: {display_value}")
    
    if not all_vars_present:
        print_error("\nНе все обязательные переменные установлены!")
        print_info("Проверьте файл .env и убедитесь, что все переменные HELEKET_* установлены.")
        return False
    
    # ========================================
    # 2. Валидация формата
    # ========================================
    print_info("\nШаг 2: Валидация формата credentials\n")
    
    # Проверка UUID
    uuid = settings.HELEKET_MERCHANT_UUID
    if len(uuid) == 36 and uuid.count('-') == 4:
        print_success(f"HELEKET_MERCHANT_UUID имеет правильный формат UUID")
    else:
        print_warning(f"HELEKET_MERCHANT_UUID может иметь неправильный формат (ожидается UUID)")
    
    # Проверка API Key
    api_key = settings.HELEKET_API_KEY
    if len(api_key) >= 32:
        print_success(f"HELEKET_API_KEY имеет достаточную длину ({len(api_key)} символов)")
    else:
        print_error(f"HELEKET_API_KEY слишком короткий ({len(api_key)} символов, ожидается минимум 32)")
        return False
    
    # ========================================
    # 3. Тест подключения к API
    # ========================================
    print_info("\nШаг 3: Тестирование подключения к Heleket API\n")
    print_info("Создаем тестовый платеж на сумму $10.00...\n")
    
    client = HeleketAPIClient()
    
    try:
        # Попытка создать тестовый платеж
        test_amount = Decimal("10.00")
        test_order_id = "TEST-ORDER-12345678"
        
        result = await client.create_payment(
            amount_usd=test_amount,
            order_id=test_order_id
        )
        
        print_success("Подключение к API Heleket успешно!")
        print_success(f"Создан тестовый платеж:\n")
        print(f"   Payment URL: {result['payment_url']}")
        print(f"   Payment UUID: {result['payment_uuid']}")
        print(f"   Order ID: {test_order_id}")
        if result.get('expired_at'):
            print(f"   Expires At: {result['expired_at']}")
        
        print_header("РЕЗУЛЬТАТ: ✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print_info("Ваша платежная система настроена правильно.")
        print_info("Пользователи могут пополнять баланс через бота.\n")
        
        return True
        
    except Exception as e:
        error_message = str(e)
        
        # Получаем детали из HTTPException если есть
        error_detail = ""
        if hasattr(e, 'detail'):
            error_detail = str(e.detail)
        
        print_error(f"Ошибка при подключении к API Heleket:\n")
        if error_message:
            print(f"   {error_message}\n")
        if error_detail and error_detail != error_message:
            print(f"   Детали: {error_detail}\n")
        
        # Детальный анализ ошибки
        full_error = f"{error_message} {error_detail}".lower()
        
        if "401" in full_error or "merchant unknown" in full_error or "конфигурации платежной системы" in full_error:
            print_header("ДИАГНОСТИКА ОШИБКИ 401: MERCHANT UNKNOWN")
            print_error("API Heleket не распознает ваш Merchant UUID\n")
            
            print_info("Возможные причины:")
            print("   1. HELEKET_MERCHANT_UUID неверный или скопирован с ошибкой")
            print("   2. HELEKET_API_KEY неверный или скопирован с ошибкой")
            print("   3. Ваш аккаунт Heleket не активирован")
            print("   4. Вы используете TEST credentials вместо PRODUCTION")
            print("   5. IP-адрес сервера заблокирован\n")
            
            print_info("Что делать:")
            print("   1. Зайдите в личный кабинет Heleket")
            print("   2. Найдите раздел API или Integration")
            print("   3. Скопируйте АКТУАЛЬНЫЕ credentials:")
            print("      - Merchant UUID (формат: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)")
            print("      - API Key (длинная строка символов)")
            print("   4. Обновите .env файл с новыми значениями")
            print("   5. Перезапустите сервисы: docker-compose restart backend bot")
            print("   6. Запустите этот скрипт снова для проверки\n")
            
        elif "403" in full_error:
            print_header("ДИАГНОСТИКА ОШИБКИ 403: FORBIDDEN")
            print_error("Доступ к API запрещен\n")
            print_info("Возможные причины:")
            print("   1. API Key неверный")
            print("   2. Аккаунт не верифицирован")
            print("   3. IP-адрес не в белом списке (если настроено)")
            print("   4. Превышены лимиты API\n")
            
        elif "timeout" in full_error or "connect" in full_error:
            print_header("ДИАГНОСТИКА ОШИБКИ: TIMEOUT/CONNECTION")
            print_error("Не удается подключиться к серверам Heleket\n")
            print_info("Возможные причины:")
            print("   1. Проблемы с интернет-соединением")
            print("   2. Firewall блокирует исходящие соединения")
            print("   3. Серверы Heleket временно недоступны\n")
        
        print_header("РЕЗУЛЬТАТ: ❌ ТЕСТЫ НЕ ПРОЙДЕНЫ")
        print_error("Платежная система не настроена корректно.")
        print_info("Следуйте инструкциям выше для исправления проблемы.\n")
        
        return False
        
    finally:
        await client.close()


def main():
    """Точка входа"""
    try:
        result = asyncio.run(test_heleket_connection())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Тестирование прервано пользователем\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Неожиданная ошибка: {str(e)}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

