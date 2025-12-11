# Интеграция внешнего SOCKS API

## Обзор

Интеграция позволяет автоматически синхронизировать прокси с внешнего API (http://91.142.73.7:8080) и продавать их пользователям по фиксированной цене $2.00.

## Основные возможности

✅ **Автоматическая синхронизация** - каждые 5 минут
✅ **Фиксированная цена** - $2.00 за любой прокси
✅ **Фильтрация** - по стране, городу, типу (residential/mobile/hosting)
✅ **Возвраты** - в течение 1 часа, если прокси оффлайн
✅ **Мультиплатформенность** - веб, API, Telegram бот

---

## Конфигурация

### 1. Переменные окружения (.env)

```bash
# API ключ для авторизации
EXTERNAL_SOCKS_API_TOKEN=telegram-bot-nik

# URL внешнего API
EXTERNAL_SOCKS_API_URL=http://91.142.73.7:8080/api/v1/authorized

# Таймаут запросов (секунды)
EXTERNAL_SOCKS_API_TIMEOUT=30

# Фиксированная цена (USD)
EXTERNAL_SOCKS_PRICE=2.00

# Интервал автоматической синхронизации (минуты)
EXTERNAL_SOCKS_SYNC_INTERVAL_MINUTES=5
```

### 2. Установка зависимостей

```bash
cd /root/proxy-shop/backend
pip install apscheduler==3.10.4
```

---

## Архитектура

### Backend компоненты

```
backend/
├── core/
│   ├── external_socks_client.py    # HTTP клиент для внешнего API
│   ├── scheduler.py                # Планировщик автосинхронизации
│   └── config.py                   # Настройки (обновлено)
├── services/
│   └── external_proxy_service.py   # Бизнес-логика
├── schemas/
│   └── external_proxy.py           # Pydantic модели
└── api/routes/
    └── external_proxy.py           # REST API эндпоинты
```

### Frontend компоненты

```
frontend/src/
└── lib/
    └── api-client.ts              # Методы для вызова API
```

### Telegram bot компоненты

```
bot/services/
└── api_client.py                  # Методы для бота (обновлено)
```

---

## API Эндпоинты

### Пользовательские

#### `GET /api/external-proxy/list`
Получить список доступных внешних прокси.

**Query параметры:**
- `country_code` (optional) - Код страны (US, UK, etc.)
- `city` (optional) - Город
- `page` (optional) - Номер страницы (default: 0)
- `page_size` (optional) - Записей на страницу (default: 50)

**Ответ:**
```json
{
  "proxies": [
    {
      "product_id": 123,
      "proxy_id": 456,
      "country": "United States",
      "country_code": "US",
      "city": "New York",
      "ISP": "AT&T",
      "price": 2.00,
      "status": 1
    }
  ],
  "total": 150,
  "page": 0,
  "page_size": 50
}
```

#### `POST /api/external-proxy/purchase`
Купить внешний прокси.

**Body:**
```json
{
  "product_id": 123
}
```

**Ответ:**
```json
{
  "order_id": "ORD-12345",
  "proxy_id": 456,
  "credentials": {
    "ip": "192.168.1.100",
    "port": "1080",
    "login": "user123",
    "password": "pass456",
    "country": "United States",
    "ISP": "AT&T"
  },
  "price": 2.00,
  "expires_at": "2025-11-19T12:00:00Z",
  "refundable": true
}
```

#### `POST /api/external-proxy/refund`
Вернуть прокси (в течение 1 часа, если оффлайн).

**Body:**
```json
{
  "order_id": "ORD-12345"
}
```

**Ответ:**
```json
{
  "status": "success",
  "message": "Proxy refunded successfully",
  "refund_amount": 2.00
}
```

### Административные (требуется admin права)

#### `POST /api/external-proxy/sync`
Ручная синхронизация прокси.

**Body:**
```json
{
  "country_code": "US",
  "page_size": 100
}
```

**Ответ:**
```json
{
  "total_fetched": 100,
  "total_available_external": 500,
  "added": 85,
  "updated": 0,
  "skipped": 15,
  "sync_time": "2025-11-18T10:30:00Z"
}
```

#### `POST /api/external-proxy/cleanup`
Удалить оффлайн прокси из инвентаря.

**Ответ:**
```json
{
  "status": "success",
  "removed_count": 12,
  "message": "Removed 12 expired proxies from inventory"
}
```

#### `GET /api/external-proxy/stats`
Получить статистику.

**Ответ:**
```json
{
  "total_inventory": 150,
  "total_sold": 45,
  "total_refunded": 3,
  "revenue": 84.00,
  "countries_available": 25,
  "last_sync": "2025-11-18T10:30:00Z"
}
```

---

## Использование

### Frontend (JavaScript)

```javascript
import { apiClient } from '@/lib/api-client';

// Получить список прокси
const proxies = await apiClient.getExternalProxies({
  country_code: 'US',
  page: 0,
  page_size: 50
});

// Купить прокси
const purchase = await apiClient.purchaseExternalProxy({
  product_id: 123
});

// Вернуть прокси
const refund = await apiClient.refundExternalProxy({
  order_id: 'ORD-12345'
});
```

### Telegram Bot (Python)

```python
from bot.services.api_client import BackendAPIClient

client = BackendAPIClient()
await client.login_telegram(telegram_id=123456789)

# Получить список прокси
proxies = await client.get_external_proxies(
    country_code='US',
    page=0,
    page_size=50
)

# Купить прокси
purchase = await client.purchase_external_proxy(product_id=123)

# Вернуть прокси
refund = await client.refund_external_proxy(order_id='ORD-12345')
```

### Backend (Python)

```python
from backend.services.external_proxy_service import ExternalProxyService
from backend.core.database import get_async_session

async with get_async_session() as session:
    # Синхронизация
    stats = await ExternalProxyService.sync_proxies_to_inventory(
        session=session,
        country_code='US'
    )

    # Покупка
    history, credentials = await ExternalProxyService.purchase_external_proxy(
        session=session,
        user_id=1,
        product_id=123
    )

    # Возврат
    result = await ExternalProxyService.refund_external_proxy(
        session=session,
        user_id=1,
        order_id='ORD-12345'
    )
```

---

## Автоматическая синхронизация

Планировщик запускается автоматически при старте backend и выполняет:

1. **Каждые 5 минут:**
   - Получает список онлайн прокси с внешнего API
   - Добавляет новые прокси в таблицу `products`
   - Пропускает уже существующие прокси
   - Удаляет оффлайн/недоступные прокси

2. **Logging:**
   - Все операции логируются в stdout
   - Уровень: `INFO` для успешных операций, `ERROR` для ошибок

3. **Мониторинг:**
   - Проверяйте логи: `docker logs proxy-shop-backend-1 | grep "external proxy"`
   - Статистика через админ API: `GET /api/external-proxy/stats`

---

## База данных

### Таблица Products

Внешние прокси хранятся в существующей таблице `products`:

- `line_name = "EXTERNAL_API"` - маркер внешних прокси
- `pre_lines_name = "SOCKS5"`
- `catalog_id` - FK к каталогу "SOCKS5_EXTERNAL"
- `product` (JSONB) - содержит все данные прокси:
  ```json
  {
    "proxy_id": 456,
    "ip": "192.168.1.100",
    "country": "United States",
    "country_code": "US",
    "city": "New York",
    "ISP": "AT&T",
    "speed": "388",
    "mobile": false,
    "hosting": false,
    "status": 1,
    "price": 2.00,
    "source": "external_api"
  }
  ```

### Таблица ProxyHistory

Покупки внешних прокси сохраняются в `proxy_history`:

- `proxies` (TEXT) - JSON с credentials:
  ```json
  [{
    "ip": "192.168.1.100",
    "port": "1080",
    "login": "user123",
    "password": "pass456",
    "external_credentials_id": 789,
    "external_proxy_id": 456,
    "refundable": true
  }]
  ```

---

## Troubleshooting

### Ошибка: "ExternalSocksAPIClient not initialized"

**Причина:** Клиент не был инициализирован при старте приложения.

**Решение:**
```python
from backend.core.external_socks_client import initialize_external_socks_client
await initialize_external_socks_client()
```

### Ошибка: "Insufficient balance on external API"

**Причина:** На балансе внешнего API недостаточно средств.

**Решение:** Пополните баланс на http://91.142.73.7:8080

### Прокси не синхронизируются

**Проверьте:**
1. Переменные окружения в `.env`
2. Доступность внешнего API: `curl http://91.142.73.7:8080/health`
3. Логи планировщика: `docker logs proxy-shop-backend-1 | grep scheduler`

### Возврат не работает

**Требования для возврата:**
- Покупка менее 1 часа назад
- Прокси оффлайн (status != 1)
- Еще не был возвращен ранее

---

## Тестирование

### 1. Проверка синтаксиса

```bash
cd /root/proxy-shop/backend
python3 -m py_compile core/external_socks_client.py
python3 -m py_compile services/external_proxy_service.py
python3 -m py_compile schemas/external_proxy.py
python3 -m py_compile api/routes/external_proxy.py
python3 -m py_compile core/scheduler.py
```

### 2. Ручная синхронизация

```bash
curl -X POST http://localhost:8000/api/external-proxy/sync \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{"country_code": "US", "page_size": 50}'
```

### 3. Получение списка

```bash
curl -X GET "http://localhost:8000/api/external-proxy/list?country_code=US" \
  -H "Authorization: Bearer <user_token>"
```

### 4. Покупка

```bash
curl -X POST http://localhost:8000/api/external-proxy/purchase \
  -H "Authorization: Bearer <user_token>" \
  -H "Content-Type: application/json" \
  -d '{"product_id": 123}'
```

---

## Мониторинг

### Логи

```bash
# Backend логи
docker logs -f proxy-shop-backend-1 | grep "external"

# Планировщик
docker logs -f proxy-shop-backend-1 | grep "scheduler"

# Синхронизация
docker logs -f proxy-shop-backend-1 | grep "sync"
```

### Метрики

```bash
# Статистика (admin)
curl -X GET http://localhost:8000/api/external-proxy/stats \
  -H "Authorization: Bearer <admin_token>"

# Статус планировщика
# Добавить эндпоинт: GET /api/external-proxy/scheduler-status
```

---

## Roadmap

### Будущие улучшения

- [ ] Dashboard для мониторинга синхронизации
- [ ] Уведомления в Telegram при ошибках синхронизации
- [ ] Кэширование списка прокси (Redis)
- [ ] Batch покупка (несколько прокси за раз)
- [ ] Фильтр по ISP и скорости
- [ ] Экспорт credentials (CSV, TXT)
- [ ] Интеграция с другими провайдерами прокси

---

## Контакты и поддержка

- **API провайдер:** http://91.142.73.7:8080
- **Swagger:** http://91.142.73.7:8080/secret/swagger/index.html
- **API Key:** telegram-bot-nik

Для вопросов и поддержки обращайтесь к разработчику.
