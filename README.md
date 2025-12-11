# Proxy Shop - Cross-Platform Proxy Marketplace

Полнофункциональный магазин прокси с синхронизацией между Telegram ботом и веб-интерфейсом.

## 🎯 Основные возможности

**Cross-Platform Authentication:**
- Единая система входа через access_code (формат: XXX-XXX-XXX)
- Регистрация возможна как в боте, так и на сайте
- Автоматическая синхронизация между платформами
- JWT токены для безопасной аутентификации

**Современный веб-интерфейс:**
- Новый фронтенд на Vite + React 19 с улучшенной производительностью
- Мгновенная горячая перезагрузка при разработке
- Оптимизированные сборки для production
- Полная поддержка темной темы

**Платежная система:**
- Прием криптовалютных платежей через Heleket API (Mode B)
- Универсальные платежные ссылки - пользователь выбирает криптовалюту на странице Heleket
- Поддержка 20+ криптовалют: BTC, ETH, USDT, SOL, TON, DOGE, LTC, BNB и другие
- Автоматическая конвертация в USD
- Автоматическое обновление баланса через webhooks
- Безопасная верификация платежей с MD5 подписью
- Минимальная сумма пополнения: 10 USD

**Каталог прокси:**
- SOCKS5 прокси (цена: 2 USD, длительность: 24 часа)
- PPTP прокси (цена: 5 USD, длительность: 24 часа)
- Фильтрация по стране, штату, городу, ZIP коду
- 50 стран в каталоге
- Детальная информация о каждом прокси (ISP, ORG, скорость)

**Гарантии и возвраты:**
- SOCKS5: возврат если прокси офлайн в течение 30 минут
- PPTP: возврат если прокси офлайн в течение 24 часов
- Автоматическая проверка статуса прокси
- Возможность продления прокси

**Реферальная система:**
- Бонус 10% от покупок рефералов
- Реферальные ссылки для бота и веба
- Статистика по рефералам

**Система купонов:**
- Скидки на покупки
- Лимиты использования
- Срок действия купонов

## 📁 Структура проекта

```
proxy-shop/
├── backend/           # FastAPI REST API
│   ├── api/          # Endpoints (auth, user, payment, products, purchase)
│   ├── core/         # Config, security, database, payment clients
│   ├── models/       # SQLAlchemy models (11 таблиц)
│   ├── schemas/      # Pydantic schemas
│   ├── services/     # Бизнес-логика
│   ├── alembic/      # Database migrations
│   ├── scripts/      # Утилиты и seed скрипты
│   └── main.py       # Entry point
├── bot/              # Telegram Bot (aiogram 3.x)
│   ├── core/         # Config, logging
│   ├── routers/      # Handlers для каждого раздела
│   ├── keyboards/    # Inline keyboards
│   ├── states/       # FSM states
│   ├── services/     # API client
│   ├── middlewares/  # Auth, i18n
│   ├── utils/        # Форматтеры, валидаторы
│   ├── locales/      # Переводы (ru/en)
│   └── main.py       # Entry point
├── frontend/         # Next.js 14 Web Interface (DEPRECATED - see new-frontend)
│   ├── src/
│   │   ├── app/     # App Router pages
│   │   ├── components/ # React компоненты
│   │   ├── lib/     # Утилиты, API client
│   │   └── types/   # TypeScript типы
│   └── package.json
├── new-frontend/     # Vite + React 19 Web Interface (CURRENT)
│   ├── pages/       # Application pages (Auth, Socks, Pptp, History)
│   ├── components/  # React components (Layout, modals)
│   ├── lib/         # API client, constants, utilities
│   ├── hooks/       # Custom hooks (usePurchaseFlow)
│   ├── types/       # TypeScript type definitions
│   └── package.json
├── admin/           # Admin Panel (Next.js 14)
└── docker-compose.yml # Docker Compose для всего стека
```

## 🚀 Быстрый старт

**1. Клонировать репозиторий:**
```bash
git clone <repository-url>
cd proxy-shop
```

**2. Настроить переменные окружения:**
```bash
# Backend
cp backend/.env.example backend/.env

# Bot
cp bot/.env.example bot/.env

# Отредактировать .env файлы
```

**3. Запустить через Docker Compose:**
```bash
docker-compose up -d
```

Это запустит:
- PostgreSQL (порт 5432)
- pgAdmin (порт 5050)
- Redis (порт 6379)
- Backend API (порт 8000)
- Telegram Bot
- New Frontend (порт 3000)
- Admin Panel (порт 3001)

**4. Применить миграции:**
```bash
docker-compose exec backend alembic upgrade head
```

**5. Seed данные (опционально):**
```bash
docker-compose exec backend python scripts/init_db.py
```

**6. Проверить работу:**
- New Frontend: http://localhost:3000 (старый Next.js фронтенд отключен по умолчанию)
- Backend API: http://localhost:8000/api/docs
- Admin Panel: http://localhost:3001
- pgAdmin: http://localhost:5050
- Telegram Bot: отправить /start боту в Telegram

## 📚 Документация

- [Backend API Documentation](backend/README.md)
- [Telegram Bot Documentation](bot/README.md)
- [New Frontend Documentation](new-frontend/README.md) ⭐ CURRENT
- [Old Frontend Documentation](frontend/README.md) (deprecated)
- [Testing Guide](TESTING_GUIDE.md)
- [Architecture Documentation](architecture_bot.md)
- API Docs (Swagger): http://localhost:8000/api/docs
- API Docs (ReDoc): http://localhost:8000/api/redoc

## 🛠 Технологический стек

**Backend:**
- Python 3.11
- FastAPI - веб-фреймворк
- SQLAlchemy 2.0 (async) - ORM
- PostgreSQL - база данных
- Alembic - миграции
- Pydantic - валидация
- python-jose - JWT токены
- httpx - HTTP клиент
- Heleket API - universal crypto payment processing

**Telegram Bot:**
- Python 3.11
- aiogram 3.2.0 - Telegram bot framework
- Redis - FSM storage
- httpx - HTTP клиент для backend API
- Babel - i18n (ru/en)

**Frontend:**

**New Frontend (Current):**
- Node.js 20
- Vite 6 - Lightning-fast build tool
- React 19 - Latest React with improved performance
- TypeScript - Type safety
- Tailwind CSS - Utility-first styling
- React Router DOM - Client-side routing
- Axios - HTTP client with interceptors
- lucide-react - Icon library

**Old Frontend (Deprecated):**
- Node.js 20
- Next.js 14 (App Router) - React framework
- TypeScript - type safety
- shadcn/ui + Chakra UI + NextUI - UI компоненты
- Tailwind CSS - стилизация
- Zustand - state management
- React Query - server state
- next-intl - i18n (ru/en)
- Axios - HTTP client

**Database:**
- PostgreSQL 16
- 11 таблиц (users, user_addresses, user_transactions, user_logs, catalog, products, proxy_history, pptp_history, coupons, user_coupon_activation, environment_variables)

**Infrastructure:**
- Docker & Docker Compose
- Redis для FSM и кеширования
- Nginx (для production)

## 🔐 Безопасность

- JWT токены для аутентификации
- MD5 signature verification для Heleket webhooks
- Атомарные транзакции БД для платежей
- CheckConstraints для защиты от отрицательного баланса
- Валидация всех пользовательских вводов
- Rate limiting (планируется)

## 📊 API Endpoints

**Authentication:**
- POST /api/auth/register - регистрация
- POST /api/auth/login - вход по access_code
- POST /api/auth/verify - проверка токена
- POST /api/auth/link-telegram - привязка Telegram
- POST /api/auth/refresh - обновление токена

**User:**
- GET /api/user/profile - профиль пользователя
- GET /api/user/history - история действий
- POST /api/user/coupon/activate - активация купона
- GET /api/user/referrals/{userId} - список рефералов

**Payment:**
- POST /api/payment/generate-address - создание платежного инвойса (Heleket)
- POST /api/payment/webhook/heleket - Heleket webhook для подтверждения платежей
- POST /api/payment/webhook/ipn - Legacy webhook (deprecated)
- GET /api/payment/history/{userId} - история платежей
- GET /api/payment/addresses - legacy адреса (deprecated)

**Products:**
- GET /api/products/socks5 - каталог SOCKS5
- GET /api/products/pptp - каталог PPTP
- GET /api/products/countries - список стран
- GET /api/products/states/{country} - список штатов

**Purchase:**
- POST /api/purchase/socks5 - купить SOCKS5
- POST /api/purchase/pptp - купить PPTP
- GET /api/purchase/history/{userId} - история покупок
- POST /api/purchase/validate/{proxyId} - проверка статуса
- POST /api/purchase/extend/{proxyId} - продление

## 🌍 Многоязычность

- Русский (ru) - основной язык
- English (en) - полная поддержка
- Автоматическое определение языка из Telegram
- Возможность смены языка через /lang

## 🐳 Docker Compose

**Сервисы:**
- `postgres` - PostgreSQL 16
- `pgadmin` - pgAdmin 4
- `redis` - Redis 7
- `backend` - FastAPI backend
- `bot` - Telegram bot
- `new-frontend` - Vite + React 19 frontend (старый Next.js фронтенд закомментирован)
- `admin` - Admin panel (Next.js 14)

**Управление:**
```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f bot
docker-compose logs -f backend

# Остановка
docker-compose down

# Полная очистка (включая volumes)
docker-compose down -v
```

## 📝 Разработка

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

### Telegram Bot

```bash
cd bot
pip install -r ../backend/requirements.txt
python -m bot.main
```

### Frontend

```bash
# New Vite Frontend (Current)
cd new-frontend
npm install
npm run dev

# Old Next.js Frontend (Deprecated)
# cd frontend
# npm install
# npm run dev
```

### Миграции БД

```bash
# Создать новую миграцию
alembic revision --autogenerate -m "description"

# Применить миграции
alembic upgrade head

# Откатить последнюю миграцию
alembic downgrade -1
```

## 🧪 Тестирование

```bash
# Backend tests
cd backend
pytest

# Bot tests (если есть)
cd bot
pytest
```

Для полного руководства по тестированию нового фронтенда, см. [TESTING_GUIDE.md](TESTING_GUIDE.md).

## 🔄 Frontend Migration (November 2024)

### Миграция с Next.js на Vite

**Причина миграции:**
- Значительно улучшенная производительность при разработке
- Более быстрые сборки (в 5-10 раз быстрее)
- Упрощенная архитектура без необходимости Server Components
- React 19 с улучшенной производительностью

**Изменения:**
- Те же функции и API интеграция
- Тот же порт (3000) для бесшовной миграции
- Улучшенная горячая перезагрузка модулей (< 100ms)
- Меньший размер бандла

**Откат:**
- Старый Next.js фронтенд остается в репозитории
- Для отката раскомментируйте секцию `frontend` в docker-compose.yml
- Закомментируйте секцию `new-frontend`

**Преимущества новой версии:**
- ⚡ Мгновенный старт dev-сервера (< 1 секунда)
- 🔥 Горячая перезагрузка без потери состояния
- 📦 Оптимизированные production сборки
- 🎨 Полная поддержка темной темы
- 🚀 React 19 features (использование, оптимизация)

## 📝 Лицензия

Проприетарное ПО. Все права защищены.

## 👥 Контакты

- Поддержка: Telegram ID 8171638354
- Email: support@proxy-shop.com

## 🚧 Roadmap

- [x] Authentication API ✅
- [x] Payment API (Heleket universal crypto payments) ✅
- [x] Products & Purchase API ✅
- [x] User Profile & Referral API ✅
- [x] Telegram Bot ✅
- [x] Web Frontend (Next.js 14) ✅
- [x] New Vite Frontend (React 19) - Improved performance and DX ✅
- [ ] Админ-панель (отдельный домен)
- [ ] Уведомления о успешных платежах
- [ ] Broadcast сообщений
- [ ] Rate limiting
- [ ] Аналитика и статистика
- [ ] Дополнительные способы оплаты (карты, электронные кошельки)
- [ ] CI/CD pipeline
- [ ] Production deployment

## 🔄 Recent Updates

**v2.1 - Frontend Migration to Vite (November 2024)**
- ✅ Migrated from Next.js 14 to Vite 6 + React 19
- ✅ Improved build times and hot module replacement
- ✅ Simplified architecture with React Router DOM
- ✅ All features preserved: auth, catalog, purchase, history, payments
- ✅ Maintained backward compatibility with backend API
- 📝 Old Next.js frontend deprecated but available for rollback

**v2.0 - Heleket Payment Integration (November 2024)**
- ✅ Migrated from cryptocurrencyapi.net to Heleket API
- ✅ Implemented Mode B universal payment links
- ✅ Support for 20+ cryptocurrencies with automatic USD conversion
- ✅ Simplified payment flow - no chain selection needed
- ✅ Enhanced security with MD5 webhook signature verification
- ✅ Updated frontend and Telegram bot for new payment flow
- 📝 Legacy endpoints maintained for backward compatibility

For detailed testing procedures, see [TESTING_GUIDE.md](TESTING_GUIDE.md).

