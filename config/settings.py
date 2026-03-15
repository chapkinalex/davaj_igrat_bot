"""Настройки приложения. Токен берётся из переменной окружения BOT_TOKEN."""
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def get_token() -> str:
    token = os.environ.get("BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit(
            "Не задан BOT_TOKEN. Задайте переменную окружения или создайте файл .env с строкой BOT_TOKEN=..."
        )
    return token
