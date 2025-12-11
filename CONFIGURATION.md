# Конфигурация Proxy Shop - Настройка окружения

## 🎉 Конфигурация успешно обновлена!

Все локальные адреса заменены на серверные, база данных инициализирована и готова к работе.

## 📋 Информация о сервере

- **IP сервера:** 23.95.132.61
- **Домен:** https://penobsobdiveivw.xyz
- **Backend API:** http://23.95.132.61:8000
- **Frontend:** https://penobsobdiveivw.xyz
- **Admin Panel:** http://23.95.132.61:3001
- **pgAdmin:** http://23.95.132.61:5050

## 🔑 Учетные данные

### База данных PostgreSQL
- **Хост:** postgres (внутри Docker) / 23.95.132.61:5432 (внешний доступ)
- **База данных:** proxy_shop
- **Пользователь:** postgres
- **Пароль:** `Secure_ProxyShop_Password_2024!`

### pgAdmin
- **URL:** http://23.95.132.61:5050
- **Email:** admin@proxy-shop.com
- **Пароль:** `Secure_Admin_Password_2024!`

### Admin Access Code (для входа в админ-панель)
```
8Y2-DPD-4C7
```
**⚠️ ВАЖНО:** Сохраните этот код! Он нужен для входа в админ-панель.

## 🔧 Что нужно настроить вручную

### 1. Telegram Bot Token
Получите токен от @BotFather и обновите в `docker-compose.yml`:
```yaml
TELEGRAM_BOT_TOKEN: ваш_реальный_токен_от_BotFather
TELEGRAM_BOT_USERNAME: имя_вашего_бота_без_@
```

### 2. CryptoCurrency API
Зарегистрируйтесь на https://cryptocurrencyapi.net/ и обновите:
```yaml
CRYPTO_API_KEY: ваш_api_ключ
CRYPTO_API_IPN_SECRET: ваш_ipn_secret
```

### 3. USDT TRC20 Кошелек
Укажите ваш реальный TRC20 адрес для получения платежей:
```yaml
USDT_TRC20_MAIN_WALLET: ваш_trc20_адрес
```

### 4. JWT Secret Key (для production)
Замените значение по умолчанию на случайную строку минимум 32 символа:
```bash
openssl rand -hex 32
```

## 📊 Статус сервисов

Все сервисы запущены и работают:
- ✅ PostgreSQL (порт 5432) - HEALTHY
- ✅ Redis (порт 6379) - HEALTHY  
- ✅ Backend API (порт 8000) - RUNNING
- ✅ Telegram Bot - RUNNING
- ✅ Frontend (порт 3000) - RUNNING
- ✅ Admin Panel (порт 3001) - RUNNING
- ✅ pgAdmin (порт 5050) - RUNNING

## 🗄️ База данных

База данных успешно инициализирована со следующими таблицами:
- users
- user_addresses
- user_transactions
- user_logs
- catalog
- products
- proxy_history
- pptp_history
- coupons
- user_coupon_activation
- environment_variables

## 🚀 Управление сервисами

### Просмотр логов
```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f backend
docker-compose logs -f bot
docker-compose logs -f frontend
```

### Перезапуск сервисов
```bash
# Все сервисы
docker-compose restart

# Конкретный сервис
docker-compose restart backend
```

### Остановка и запуск
```bash
# Остановить все
docker-compose down

# Запустить все
docker-compose up -d
```

### Проверка статуса
```bash
docker-compose ps
```

## 🔗 Доступ к API

### Backend API Documentation
- **Swagger UI:** http://23.95.132.61:8000/docs
- **ReDoc:** http://23.95.132.61:8000/redoc

### Проверка здоровья
```bash
curl http://23.95.132.61:8000/health
```

## 📝 Следующие шаги

1. **Настройте Telegram бота** - получите токен от @BotFather
2. **Настройте платежный API** - зарегистрируйтесь на cryptocurrencyapi.net
3. **Обновите переменные окружения** в docker-compose.yml
4. **Перезапустите сервисы** после обновления конфигурации:
   ```bash
   docker-compose down
   docker-compose up -d
   ```
5. **Войдите в админ-панель** по адресу http://23.95.132.61:3001 используя access code `8Y2-DPD-4C7`
6. **Добавьте прокси** через админ-панель для тестирования

## 🌐 Настройка домена

Основной фронтенд настроен на домен **https://penobsobdiveivw.xyz**

### DNS настройки
Убедитесь, что DNS запись для домена указывает на IP сервера:
```
A запись: penobsobdiveivw.xyz -> 23.95.132.61
```

### Настройка reverse proxy (Nginx/Caddy)
Для работы домена необходимо настроить reverse proxy на сервере, который будет перенаправлять запросы с домена на порт 3000.

#### Пример конфигурации Nginx:
```nginx
server {
    listen 80;
    listen 443 ssl http2;
    server_name penobsobdiveivw.xyz;

    # SSL сертификаты (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/penobsobdiveivw.xyz/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/penobsobdiveivw.xyz/privkey.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Пример конфигурации Caddy (рекомендуется):
```
penobsobdiveivw.xyz {
    reverse_proxy localhost:3000
    reverse_proxy /api/* localhost:8000
}
```

### Получение SSL сертификата (Let's Encrypt)
```bash
# Установка Certbot
apt install certbot python3-certbot-nginx

# Получение сертификата
certbot --nginx -d penobsobdiveivw.xyz
```

## 🔐 Безопасность

⚠️ **ВАЖНО для продакшна:**

1. Смените все пароли по умолчанию
2. Настройте SSL/TLS сертификаты (Let's Encrypt)
3. Настройте firewall
4. Ограничьте доступ к pgAdmin (порт 5050)
5. Используйте сильный JWT_SECRET_KEY
6. Настройте регулярные backup базы данных

## 📞 Поддержка

- Telegram ID поддержки: 8171638354
- Backend логи: `docker-compose logs backend`
- Bot логи: `docker-compose logs bot`

---

**Дата настройки:** November 14, 2025
**IP сервера:** 23.95.132.61

