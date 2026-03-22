"""Точка входа: init_db, регистрация обработчиков и запуск бота."""
import asyncio

from bot.main import main

if __name__ == "__main__":
    print("Бот запускается...")
    asyncio.run(main())
