# Деплой Proxy Shop через GHCR

## Обзор

Проект настроен для **автоматической сборки и деплоя**:
1. При пуше в `main`/`master` → образы собираются и публикуются в GHCR
2. После сборки → автоматический деплой на production сервер через SSH

## Архитектура

```
GitHub Repository
       │
       ▼ (push to main/master)
GitHub Actions
       │
       ├──────────────────────┐
       ▼                      ▼
GHCR (ghcr.io)          SSH Deploy
(build & push)          (pull & restart)
       │                      │
       └──────────────────────┘
                 │
                 ▼
        Production Server
```

## Образы

После пуша в main/master автоматически собираются и публикуются:

- `ghcr.io/<owner>/proxy-shop/backend:latest` - Backend API
- `ghcr.io/<owner>/proxy-shop/bot:latest` - Telegram Bot
- `ghcr.io/<owner>/proxy-shop/frontend:latest` - Frontend (new-frontend)
- `ghcr.io/<owner>/proxy-shop/admin:latest` - Admin Panel

## Настройка GitHub Repository

### 1. Включите GitHub Actions

GitHub Actions включены по умолчанию. Убедитесь, что workflow файл находится в `.github/workflows/build-and-push.yml`.

### 2. Настройте права packages

Перейдите в **Settings → Actions → General** и убедитесь что:
- Workflow permissions: **"Read and write permissions"**

### 3. Настройте секреты для автодеплоя (ОБЯЗАТЕЛЬНО)

Перейдите в **Settings → Secrets and variables → Actions → Secrets** и добавьте:

| Секрет | Описание | Пример |
|--------|----------|--------|
| `SERVER_HOST` | IP или домен сервера | `123.45.67.89` |
| `SERVER_USER` | Пользователь SSH | `root` или `deploy` |
| `SSH_PRIVATE_KEY` | Приватный SSH ключ | Содержимое `~/.ssh/id_rsa` |
| `SERVER_PORT` | Порт SSH (опционально) | `22` |
| `PROJECT_PATH` | Путь к проекту (опционально) | `/root/proxy-shop` |
| `GHCR_TOKEN` | GitHub PAT с правами `read:packages` | `ghp_xxxx...` |

#### Как создать SSH ключ для деплоя:

```bash
# На вашем компьютере (не на сервере!)
ssh-keygen -t ed25519 -C "github-deploy" -f ~/.ssh/github_deploy

# Скопируйте публичный ключ на сервер
ssh-copy-id -i ~/.ssh/github_deploy.pub user@your-server

# Содержимое ПРИВАТНОГО ключа добавьте в GitHub Secrets
cat ~/.ssh/github_deploy
# Скопируйте ВСЁ включая -----BEGIN... и -----END...
```

#### Как создать GHCR_TOKEN:

1. Перейдите: https://github.com/settings/tokens/new
2. Выберите: **"Generate new token (classic)"**
3. Права: только `read:packages`
4. Скопируйте токен в секрет `GHCR_TOKEN`

### 4. Настройте переменные для сборки (опционально)

Перейдите в **Settings → Secrets and variables → Actions → Variables** и добавьте:

| Переменная | Описание | Пример |
|------------|----------|--------|
| `VITE_API_URL` | URL вашего API | `https://api.example.com` |
| `VITE_APP_URL` | URL приложения | `https://example.com` |

## Деплой на новый сервер

### Быстрый старт

```bash
# 1. Клонируйте репозиторий (или скачайте только нужные файлы)
git clone https://github.com/<owner>/proxy-shop.git
cd proxy-shop

# 2. Запустите настройку
./deploy.sh setup

# 3. Отредактируйте .env файл
nano .env

# 4. Запустите сервисы
./deploy.sh up
```

### Пошаговая инструкция

#### Шаг 1: Установка Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Перелогиньтесь для применения групп
exit
```

#### Шаг 2: Получение файлов

Вариант A - Клонирование репозитория:
```bash
git clone https://github.com/<owner>/proxy-shop.git
cd proxy-shop
```

Вариант B - Скачивание только нужных файлов:
```bash
mkdir proxy-shop && cd proxy-shop

# Скачайте необходимые файлы
curl -O https://raw.githubusercontent.com/<owner>/proxy-shop/main/docker-compose.ghcr.yml
curl -O https://raw.githubusercontent.com/<owner>/proxy-shop/main/deploy.sh
curl -O https://raw.githubusercontent.com/<owner>/proxy-shop/main/.env.example

chmod +x deploy.sh
```

#### Шаг 3: Авторизация в GHCR

```bash
# Создайте Personal Access Token на GitHub:
# https://github.com/settings/tokens/new?scopes=read:packages

# Залогиньтесь в GHCR
echo "YOUR_GITHUB_TOKEN" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

#### Шаг 4: Настройка окружения

```bash
# Создайте .env из примера
cp .env.example .env

# Добавьте GHCR настройки
echo "GHCR_OWNER=your-github-username" >> .env
echo "IMAGE_TAG=latest" >> .env

# Отредактируйте остальные переменные
nano .env
```

#### Шаг 5: Запуск

```bash
# Скачайте образы
./deploy.sh pull

# Запустите сервисы
./deploy.sh up

# Проверьте статус
./deploy.sh status
```

## Команды deploy.sh

| Команда | Описание |
|---------|----------|
| `./deploy.sh setup` | Первоначальная настройка |
| `./deploy.sh pull` | Скачать последние образы |
| `./deploy.sh up` | Запустить сервисы |
| `./deploy.sh down` | Остановить сервисы |
| `./deploy.sh restart` | Перезапустить сервисы |
| `./deploy.sh update` | Обновить образы и перезапустить |
| `./deploy.sh logs` | Показать логи всех сервисов |
| `./deploy.sh logs backend` | Показать логи конкретного сервиса |
| `./deploy.sh status` | Показать статус сервисов |

## Обновление на production

### Автоматический деплой (рекомендуется)

При пуше в `main`/`master`:

1. ✅ GitHub Actions автоматически собирает новые образы
2. ✅ Образы публикуются в GHCR с тегом `latest`
3. ✅ **Автоматически** подключается к серверу по SSH
4. ✅ Скачивает новые образы и перезапускает сервисы

**Ничего делать не нужно!** Просто пушьте в main.

### Ручной деплой (если нужно)

Если автодеплой отключен или нужно обновить вручную:

```bash
./deploy.sh update
```

## Использование конкретной версии

Для деплоя конкретной версии (по тегу или SHA коммита):

```bash
# По тегу
IMAGE_TAG=v1.2.3 ./deploy.sh up

# По SHA коммита
IMAGE_TAG=abc1234 ./deploy.sh up

# Или установите в .env
echo "IMAGE_TAG=v1.2.3" >> .env
./deploy.sh up
```

## Доступные теги образов

- `latest` - последняя версия из main/master
- `main` или `master` - то же что latest
- `v*` - по git тегам (например: v1.0.0)
- `<sha>` - по короткому SHA коммита

## Troubleshooting

### Ошибка "unauthorized" при pull

```bash
# Перелогиньтесь в GHCR
docker logout ghcr.io
echo "YOUR_TOKEN" | docker login ghcr.io -u YOUR_USERNAME --password-stdin
```

### Образы не обновляются

```bash
# Принудительно пересоздайте контейнеры
docker-compose -f docker-compose.ghcr.yml pull
docker-compose -f docker-compose.ghcr.yml up -d --force-recreate
```

### Проверка доступности образов

```bash
# Проверьте что образы существуют
docker manifest inspect ghcr.io/<owner>/proxy-shop/backend:latest
```

## Минимальные требования сервера

- CPU: 2 cores
- RAM: 4 GB
- Disk: 20 GB
- OS: Ubuntu 20.04+ / Debian 11+
- Docker: 20.10+
- Docker Compose: 2.0+

## Порты

| Сервис | Порт |
|--------|------|
| Frontend | 3000 |
| Admin | 3001 |
| Backend API | 8000 |
| PostgreSQL | 5432 |
| Redis | 6379 |

## Безопасность

⚠️ **Важно для production:**

1. Используйте firewall (ufw):
```bash
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw allow 3000  # Frontend
sudo ufw allow 3001  # Admin (ограничьте по IP!)
sudo ufw enable
```

2. Не открывайте порты 5432 (PostgreSQL) и 6379 (Redis) наружу

3. Используйте reverse proxy (nginx/traefik) с SSL

4. Регулярно обновляйте образы:
```bash
./deploy.sh update
```

