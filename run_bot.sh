#!/usr/bin/env bash
# Запуск Telegram-бота «Давай играть»
# Использование: вызывается из systemd или вручную из каталога проекта.

set -e

# Каталог, где лежит этот скрипт (и bot.py, games_data.py и т.д.)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Виртуальное окружение: если есть папка venv в каталоге проекта — используем её
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Запуск бота (python3 для Linux)
exec python3 main.py
