"""Создание бота, диспетчера и состояние. Запуск polling."""
import asyncio
from aiogram import Bot, Dispatcher

from config.settings import get_token

# Токен и экземпляры
bot = Bot(token=get_token())
dp = Dispatcher()

# Состояние пользователей (в памяти)
user_state = {}
user_favorites = {}  # user_id -> set(game_id)
user_progress = {}
user_history = {}  # user_id -> list of diagnostics
user_games_journal = {}  # user_id -> list of {"game_id": ..., "status": ...}
children = {}  # user_id -> list of {"name": ..., "age_code": ...}


async def run_main() -> None:
    """Запуск long polling."""
    await dp.start_polling(bot)
