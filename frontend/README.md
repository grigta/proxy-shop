# Proxy Shop Frontend

Веб-интерфейс для Proxy Shop на Next.js 14 с TypeScript.

## Технологический стек

**Core:**
- Next.js 14 (App Router)
- React 18
- TypeScript 5

**UI Libraries:**
- shadcn/ui - основные компоненты (формы, диалоги, таблицы, кнопки)
- Chakra UI - layout компоненты (Stack, Grid, Container)
- NextUI - специфичные компоненты (Avatar, Badge, Chip)
- Tailwind CSS - стилизация
- next-themes - dark mode

**State Management:**
- Zustand - глобальное состояние (auth, user)
- React Query - server state и кеширование

**Forms & Validation:**
- React Hook Form - управление формами
- Zod - валидация схем

**i18n:**
- next-intl - интернационализация (ru/en)

**HTTP Client:**
- Axios - API запросы с автоматическим JWT refresh

**Utilities:**
- date-fns - форматирование дат
- qrcode.react - отображение QR-кодов
- js-cookie - работа с cookies
- lucide-react - иконки

## Структура проекта

```
frontend/
├── src/
│   ├── app/
│   │   ├── [locale]/          # Локализованные роуты
│   │   │   ├── login/         # Страница входа
│   │   │   ├── dashboard/     # Главная страница (профиль)
│   │   │   ├── socks5/        # Каталог SOCKS5
│   │   │   ├── pptp/          # Каталог PPTP
│   │   │   ├── history/       # История покупок
│   │   │   ├── payment/       # Пополнение баланса
│   │   │   └── referrals/     # Рефералы
│   │   ├── layout.tsx         # Root layout
│   │   └── globals.css        # Глобальные стили
│   ├── components/
│   │   ├── ui/                # shadcn/ui компоненты
│   │   ├── layout/            # Layout компоненты (Navbar)
│   │   ├── proxy-card.tsx     # Карточка прокси
│   │   ├── country-selector.tsx # Выбор страны
│   │   └── providers.tsx      # Все провайдеры
│   ├── lib/
│   │   ├── api-client.ts      # HTTP клиент для backend API
│   │   ├── utils.ts           # Утилиты
│   │   └── constants.ts       # Константы
│   ├── hooks/
│   │   └── use-api.ts         # React Query hooks
│   ├── store/
│   │   └── auth-store.ts      # Zustand store для auth
│   ├── types/
│   │   └── api.ts             # TypeScript типы из backend schemas
│   ├── i18n.ts                # next-intl конфигурация
│   └── middleware.ts          # Next.js middleware (i18n + auth)
├── messages/
│   ├── ru.json                # Русские переводы
│   └── en.json                # Английские переводы
├── public/                    # Статические файлы
├── .env.example               # Шаблон переменных окружения
├── next.config.js             # Next.js конфигурация
├── tailwind.config.ts         # Tailwind конфигурация
├── tsconfig.json              # TypeScript конфигурация
└── package.json               # Зависимости
```

## Установка и запуск

### 1. Установить зависимости:
```bash
npm install
# или
yarn install
```

### 2. Настроить переменные окружения:
```bash
cp .env.example .env.local
# Отредактировать .env.local
```

### 3. Запустить development сервер:
```bash
npm run dev
# или
yarn dev
```

Приложение будет доступно на http://localhost:3000

### 4. Собрать для production:
```bash
npm run build
npm run start
```

## Основные возможности

**Аутентификация:**
- Вход по access_code (формат: XXX-XXX-XXX)
- JWT токены (access + refresh) в httpOnly cookies (managed server-side via Route Handlers)
- Автоматический refresh при истечении access token
- Синхронизация с Telegram ботом

**Профиль пользователя:**
- Просмотр баланса, даты регистрации, ID
- Реферальные ссылки (бот + веб)
- Статистика по рефералам
- История действий

**Каталог прокси:**
- SOCKS5: фильтрация по стране, штату, городу, ZIP
- PPTP: выбор региона (USA/EUROPE)
- Пагинация (10 прокси на страницу)
- Детальная информация о каждом прокси

**Покупка прокси:**
- Выбор количества (для SOCKS5)
- Применение купонов на скидку
- Просмотр истории покупок
- Проверка статуса прокси (онлайн/офлайн)
- Продление прокси

**Пополнение баланса:**
- 7 криптовалют: BTC, ETH, LTC, BNB, USDT (TRC-20, ERC-20, BEP-20)
- Генерация адреса с QR-кодом
- Минимальная сумма: 10 USD
- История платежей

## Интеграция с Backend API

Frontend использует следующие эндпоинты:

- **Auth:** /api/auth/login, /api/auth/refresh, /api/auth/verify
- **User:** /api/user/profile, /api/user/history, /api/user/referrals/{userId}
- **Payment:** /api/payment/generate-address, /api/payment/history/{userId}
- **Products:** /api/products/socks5, /api/products/pptp, /api/products/countries
- **Purchase:** /api/purchase/socks5, /api/purchase/pptp, /api/purchase/history/{userId}, /api/purchase/validate/{proxyId}, /api/purchase/extend/{proxyId}

**Аутентификация:**
- JWT токены хранятся в httpOnly cookies (set by server-side Route Handlers)
- Автоматический refresh access token при истечении (30 минут)
- При 401 Unauthorized автоматический logout

## Многоязычность (i18n)

Приложение поддерживает русский и английский языки:
- Язык определяется автоматически из браузера
- Переводы хранятся в messages/ru.json и messages/en.json
- Форматирование дат и чисел адаптируется под локаль

## Dark Mode

- Автоматическое определение темы из системных настроек
- Переключатель темы в navbar
- Все компоненты адаптируются под тему

## Responsive Design

- Mobile (< 768px): вертикальный layout, карточки вместо таблиц
- Tablet (768-1023px): 2 колонки
- Desktop (>= 1024px): полный layout, 3 колонки

## Переменные окружения

```env
# Backend API URL (публичная переменная)
NEXT_PUBLIC_API_URL=http://localhost:8000

# App URL (для реферальных ссылок)
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

## Разработка

### Добавить новую страницу:
1. Создать файл в `src/app/[locale]/новая-страница/page.tsx`
2. Добавить переводы в `messages/ru.json` и `messages/en.json`
3. Добавить ссылку в Navbar

### Добавить новый API эндпоинт:
1. Добавить типы в `src/types/api.ts`
2. Добавить метод в `src/lib/api-client.ts`
3. Создать React Query hook в `src/hooks/use-api.ts`

### Добавить новый UI компонент:
1. Создать файл в `src/components/ui/`
2. Использовать Tailwind CSS и shadcn/ui паттерны
3. Экспортировать компонент

## Troubleshooting

**Приложение не запускается:**
- Проверить Node.js >= 18.17.0
- Выполнить `npm install`
- Проверить .env.local

**API запросы не работают:**
- Проверить что backend запущен на NEXT_PUBLIC_API_URL
- Проверить CORS настройки в backend
- Проверить network tab в DevTools

**Токены не сохраняются:**
- Проверить что cookies включены в браузере
- Для production настроить правильные домены

**Переводы не работают:**
- Проверить что messages/ru.json и messages/en.json существуют
- Проверить middleware конфигурацию

