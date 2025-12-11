#!/bin/bash
# =============================================================================
# Скрипт деплоя Proxy Shop с использованием GHCR
# =============================================================================
#
# Использование:
#   ./deploy.sh [команда]
#
# Команды:
#   setup    - Первоначальная настройка (логин в GHCR, создание .env)
#   pull     - Скачать последние образы
#   up       - Запустить все сервисы
#   down     - Остановить все сервисы
#   restart  - Перезапустить все сервисы
#   update   - Обновить образы и перезапустить (pull + up)
#   logs     - Показать логи
#   status   - Показать статус сервисов
#
# =============================================================================

set -e

COMPOSE_FILE="docker-compose.ghcr.yml"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка наличия .env файла
check_env() {
    if [ ! -f ".env" ]; then
        log_error ".env файл не найден!"
        log_info "Создайте .env файл на основе .env.example или запустите: ./deploy.sh setup"
        exit 1
    fi
}

# Проверка наличия GHCR_OWNER в .env
check_ghcr_owner() {
    if ! grep -q "^GHCR_OWNER=" .env 2>/dev/null; then
        log_error "GHCR_OWNER не установлен в .env файле!"
        log_info "Добавьте: GHCR_OWNER=your-github-username"
        exit 1
    fi
}

# Первоначальная настройка
setup() {
    log_info "Начинаем настройку..."
    
    # Запрос GitHub username
    read -p "Введите ваш GitHub username или organization: " GITHUB_USER
    
    # Запрос GitHub token
    echo ""
    log_info "Для доступа к GHCR нужен GitHub Personal Access Token с правами read:packages"
    log_info "Создать токен: https://github.com/settings/tokens/new?scopes=read:packages"
    echo ""
    read -sp "Введите GitHub Personal Access Token: " GITHUB_TOKEN
    echo ""
    
    # Логин в GHCR
    log_info "Авторизация в GitHub Container Registry..."
    echo "$GITHUB_TOKEN" | docker login ghcr.io -u "$GITHUB_USER" --password-stdin
    
    # Создание .env файла если не существует
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_info "Создан .env файл из .env.example"
        else
            touch .env
            log_info "Создан пустой .env файл"
        fi
    fi
    
    # Добавление GHCR_OWNER в .env
    if grep -q "^GHCR_OWNER=" .env; then
        sed -i "s/^GHCR_OWNER=.*/GHCR_OWNER=$GITHUB_USER/" .env
    else
        echo "GHCR_OWNER=$GITHUB_USER" >> .env
    fi
    
    # Добавление IMAGE_TAG если не существует
    if ! grep -q "^IMAGE_TAG=" .env; then
        echo "IMAGE_TAG=latest" >> .env
    fi
    
    log_info "Настройка завершена!"
    log_info "Отредактируйте .env файл и затем запустите: ./deploy.sh up"
}

# Скачать образы
pull() {
    check_env
    check_ghcr_owner
    log_info "Скачивание образов из GHCR..."
    docker-compose -f "$COMPOSE_FILE" pull
    log_info "Образы успешно скачаны!"
}

# Запустить сервисы
up() {
    check_env
    check_ghcr_owner
    log_info "Запуск сервисов..."
    docker-compose -f "$COMPOSE_FILE" up -d
    log_info "Сервисы запущены!"
    status
}

# Остановить сервисы
down() {
    log_info "Остановка сервисов..."
    docker-compose -f "$COMPOSE_FILE" down
    log_info "Сервисы остановлены!"
}

# Перезапустить сервисы
restart() {
    log_info "Перезапуск сервисов..."
    docker-compose -f "$COMPOSE_FILE" restart
    log_info "Сервисы перезапущены!"
}

# Обновить и перезапустить
update() {
    check_env
    check_ghcr_owner
    log_info "Обновление сервисов..."
    pull
    docker-compose -f "$COMPOSE_FILE" up -d --force-recreate
    log_info "Сервисы обновлены!"
    status
}

# Показать логи
logs() {
    docker-compose -f "$COMPOSE_FILE" logs -f "$@"
}

# Показать статус
status() {
    echo ""
    log_info "Статус сервисов:"
    docker-compose -f "$COMPOSE_FILE" ps
}

# Главный обработчик команд
case "${1:-help}" in
    setup)
        setup
        ;;
    pull)
        pull
        ;;
    up)
        up
        ;;
    down)
        down
        ;;
    restart)
        restart
        ;;
    update)
        update
        ;;
    logs)
        shift
        logs "$@"
        ;;
    status)
        status
        ;;
    *)
        echo "Proxy Shop - Скрипт деплоя с GHCR"
        echo ""
        echo "Использование: ./deploy.sh [команда]"
        echo ""
        echo "Команды:"
        echo "  setup    - Первоначальная настройка (логин в GHCR, создание .env)"
        echo "  pull     - Скачать последние образы"
        echo "  up       - Запустить все сервисы"
        echo "  down     - Остановить все сервисы"
        echo "  restart  - Перезапустить все сервисы"
        echo "  update   - Обновить образы и перезапустить"
        echo "  logs     - Показать логи (можно указать сервис: ./deploy.sh logs backend)"
        echo "  status   - Показать статус сервисов"
        ;;
esac



