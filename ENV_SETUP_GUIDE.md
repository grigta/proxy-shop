# Инструкция по настройке переменных окружения

## 📝 Обязательные настройки перед запуском в production

Файл `docker-compose.yml` содержит все необходимые переменные окружения. Ниже указаны значения, которые **ОБЯЗАТЕЛЬНО** нужно заменить на реальные.

## 🔴 КРИТИЧЕСКИ ВАЖНО

### 1. Telegram Bot Token

**Где найти:** Получите у @BotFather в Telegram

1. Откройте Telegram и найдите @BotFather
2. Отправьте команду `/newbot` (или используйте существующего)
3. Следуйте инструкциям и получите токен формата: `1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ1234567890`

**Где изменить в docker-compose.yml:**
```yaml
services:
  backend:
    environment:
      TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN:-ВАШ_РЕАЛЬНЫЙ_ТОКЕН_СЮДА}
      TELEGRAM_BOT_USERNAME: ${TELEGRAM_BOT_USERNAME:-имя_вашего_бота}
```

### 2. CryptoCurrency API (для приема платежей)

**Где получить:** https://cryptocurrencyapi.net/

1. Зарегистрируйтесь на сайте
2. Получите API Key
3. Получите IPN Secret для webhook'ов

**Где изменить в docker-compose.yml:**
```yaml
services:
  backend:
    environment:
      CRYPTO_API_KEY: ${CRYPTO_API_KEY:-ваш_api_ключ_минимум_16_символов}
      CRYPTO_API_IPN_SECRET: ${CRYPTO_API_IPN_SECRET:-ваш_ipn_secret_минимум_16_символов}
```

### 3. USDT TRC20 Wallet Address

**Где получить:** Используйте любой кошелек поддерживающий TRON (TRC20)
- Trust Wallet
- TronLink
- Или любой другой

**Где изменить в docker-compose.yml:**
```yaml
services:
  backend:
    environment:
      USDT_TRC20_MAIN_WALLET: ${USDT_TRC20_MAIN_WALLET:-ваш_реальный_TRC20_адрес}
```

### 4. JWT Secret Key (для production)

**Как сгенерировать:**
```bash
openssl rand -hex 32
```

Это даст вам случайную строку, например: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6`

**Где изменить в docker-compose.yml:**
```yaml
services:
  backend:
    environment:
      JWT_SECRET_KEY: ${JWT_SECRET_KEY:-ваша_случайная_строка_32_символа}
```

## 🟡 РЕКОМЕНДУЕТСЯ ИЗМЕНИТЬ

### 5. Пароли PostgreSQL и pgAdmin

**Где изменить:**
```yaml
services:
  postgres:
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-ваш_сложный_пароль}
      
  pgadmin:
    environment:
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_DEFAULT_PASSWORD:-ваш_admin_пароль}
```

Также обновите в backend:
```yaml
services:
  backend:
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-тот_же_пароль_что_для_postgres}
      DATABASE_URL: ${DATABASE_URL:-postgresql+asyncpg://postgres:ваш_пароль@postgres:5432/proxy_shop}
```

## 🔧 Как применить изменения

### Вариант 1: Редактирование docker-compose.yml напрямую

1. Откройте файл:
   ```bash
   nano /root/proxy-shop/docker-compose.yml
   ```

2. Найдите и замените значения после `:-` на ваши реальные

3. Сохраните (Ctrl+X, Y, Enter)

4. Перезапустите сервисы:
   ```bash
   cd /root/proxy-shop
   docker-compose down
   docker-compose up -d
   ```

### Вариант 2: Использование .env файла (рекомендуется)

1. Создайте файл `.env` в корне проекта:
   ```bash
   nano /root/proxy-shop/.env
   ```

2. Добавьте ваши значения:
   ```bash
   # Telegram
   TELEGRAM_BOT_TOKEN=ваш_реальный_токен
   TELEGRAM_BOT_USERNAME=ваш_бот_username
   
   # Crypto API
   CRYPTO_API_KEY=ваш_api_ключ
   CRYPTO_API_IPN_SECRET=ваш_ipn_secret
   USDT_TRC20_MAIN_WALLET=ваш_trc20_адрес
   
   # JWT
   JWT_SECRET_KEY=ваш_jwt_secret_минимум_32_символа
   
   # Database
   POSTGRES_PASSWORD=ваш_db_пароль
   DATABASE_URL=postgresql+asyncpg://postgres:ваш_db_пароль@postgres:5432/proxy_shop
   
   # pgAdmin
   PGADMIN_DEFAULT_PASSWORD=ваш_admin_пароль
   ```

3. Сохраните файл

4. Перезапустите:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

## ✅ Проверка конфигурации

После изменения переменных и перезапуска:

1. **Проверьте логи backend:**
   ```bash
   docker-compose logs backend | tail -20
   ```
   Должно быть: `Application startup complete.`

2. **Проверьте логи бота:**
   ```bash
   docker-compose logs bot | tail -20
   ```
   Должно быть: `Bot started successfully`

3. **Проверьте API:**
   ```bash
   curl http://23.95.132.61:8000/api/docs
   ```

4. **Проверьте frontend:**
   ```bash
   curl http://23.95.132.61:3000
   ```

## 🚨 Troubleshooting

### Ошибка: "TELEGRAM_BOT_TOKEN must be a valid bot token"
- Убедитесь, что токен содержит `:` и имеет правильный формат
- Проверьте, что токен получен от @BotFather

### Ошибка: "CRYPTO_API_IPN_SECRET must be at least 16 characters long"
- Убедитесь, что значение содержит минимум 16 символов

### Ошибка: "JWT_SECRET_KEY must be at least 32 characters long"
- Используйте `openssl rand -hex 32` для генерации

### База данных не подключается
- Проверьте, что пароль одинаковый в `postgres` и `backend` секциях
- Проверьте, что DATABASE_URL содержит правильный пароль

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте логи: `docker-compose logs [service_name]`
2. Убедитесь, что все сервисы запущены: `docker-compose ps`
3. Telegram: 8171638354

---

**Последнее обновление:** November 14, 2025

