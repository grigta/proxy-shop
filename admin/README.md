# Proxy Shop Admin Panel (Vite)

Современная админ-панель для управления Proxy Shop, построенная на Vite + React.

## Описание

Новая Vite-based админ-панель для управления пользователями, купонами и прокси. Заменяет предыдущую Next.js версию с более простой и быстрой архитектурой.

## Технологии

- **Vite** - Быстрый сборщик и dev-сервер
- **React 19** - UI библиотека
- **TypeScript** - Типизация
- **Lucide React** - Иконки
- **Recharts** - Графики и визуализация

## Функциональность

- **Dashboard** - Обзор ключевых метрик и статистики
- **Users** - Управление пользователями (блокировка, баланс, история покупок)
- **Coupons** - Создание и управление купонами на скидку
- **Proxies** - Управление прокси-серверами (добавление, редактирование, статус)

## Установка

```bash
npm install
```

## Запуск

### Development (Разработка)
```bash
npm run dev
```
Панель будет доступна на порту 3001.

### Build (Сборка)
```bash
npm run build
```
Собранные файлы будут в директории `dist/`.

### Preview (Предпросмотр сборки)
```bash
npm run preview
```

## Docker

Запуск через Docker Compose (рекомендуется):

```bash
# Запустить все сервисы
docker-compose up

# Только админ-панель
docker-compose up admin
```

Админ-панель будет доступна по адресу `http://localhost:3001`

## Переменные окружения

Создайте файл `.env` на основе `.env.example`:

```env
VITE_API_URL=http://localhost:8000
NODE_ENV=development
```

### Описание переменных:

- `VITE_API_URL` - URL backend API (по умолчанию: http://localhost:8000)
- `NODE_ENV` - Окружение (development/production)

## Структура проекта

```
admin/
├── components/          # React компоненты
│   ├── Dashboard.tsx   # Главная панель
│   ├── Users.tsx       # Управление пользователями
│   ├── Coupons.tsx     # Управление купонами
│   ├── Proxies.tsx     # Управление прокси
│   └── Sidebar.tsx     # Боковое меню
├── App.tsx             # Главный компонент
├── index.tsx           # Точка входа React
├── index.html          # HTML шаблон
├── constants.ts        # Константы и конфигурация API
├── types.ts            # TypeScript типы
├── vite.config.ts      # Конфигурация Vite
├── package.json        # Зависимости
├── tsconfig.json       # Конфигурация TypeScript
├── Dockerfile          # Docker образ
└── .dockerignore       # Исключения для Docker
```

## API Integration

Панель интегрируется с backend API через переменную окружения `VITE_API_URL`. Все API endpoints определены в `constants.ts` и соответствуют структуре backend API в `/backend/api/routes/admin.py`.

### Основные endpoints:

- `GET /api/admin/users` - Список пользователей
- `POST /api/admin/users/{id}/ban` - Блокировка пользователя
- `GET /api/admin/coupons` - Список купонов
- `POST /api/admin/coupons` - Создание купона
- `GET /api/admin/proxies` - Список прокси
- `POST /api/admin/proxies` - Добавление прокси

## Миграция с Next.js

Эта версия заменяет старую Next.js админ-панель со следующими улучшениями:

- **Быстрее dev-сервер** - Vite обеспечивает мгновенный HMR
- **Проще архитектура** - Без app router, server components
- **Меньше зависимостей** - Упрощенный tech stack
- **Такой же backend API** - Полная совместимость с существующим API

### Ключевые изменения:

- `NEXT_PUBLIC_API_URL` → `VITE_API_URL`
- `next.config.js` → `vite.config.ts`
- `.next/` → `dist/`
- Port 3001 (без изменений)

## Разработка

### Добавление нового компонента

1. Создайте файл в `components/`
2. Добавьте необходимые типы в `types.ts`
3. Импортируйте в `App.tsx`

### Обновление API endpoints

Обновите константу `API_BASE_URL` в `constants.ts` для изменения базового URL API.

## Поддержка

При возникновении проблем, проверьте:

1. Переменные окружения (`.env`)
2. Backend API доступен и запущен
3. Порт 3001 не занят другим процессом
4. Node.js версии 20+
