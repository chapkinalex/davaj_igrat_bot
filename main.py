"""Точка входа: регистрация обработчиков и запуск бота."""
import asyncio

# Импорт регистрирует все обработчики на dp
import bot.handlers  # noqa: F401
from bot.main import run_main

if __name__ == "__main__":
    print("Бот запускается...")
    asyncio.run(run_main())
