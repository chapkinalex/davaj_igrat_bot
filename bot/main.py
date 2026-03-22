"""Создание бота, диспетчера и запуск polling."""
import os

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession

from config.settings import get_token
from data.database import init_db

# Прокси задаётся в .env (BOT_PROXY). Экземпляр бота создаётся в main() внутри event loop.
_proxy_url = os.environ.get("BOT_PROXY", "").strip()
bot = None  # задаётся в main(); для импорта в handlers
dp = Dispatcher()


async def main() -> None:
    init_db()
    import bot.handlers  # noqa: F401 — регистрация обработчиков на dp

    global bot
    if _proxy_url:
        session = AiohttpSession(proxy=_proxy_url)
        bot = Bot(token=get_token(), session=session)
        print(
            f"Используется прокси: {_proxy_url.split('@')[-1] if '@' in _proxy_url else _proxy_url}"
        )
    else:
        bot = Bot(token=get_token())
        print("Подключение к Telegram без прокси.")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        err = str(e).lower()
        if _proxy_url and ("proxy" in err or "timeout" in err):
            print(
                "\nОшибка: прокси недоступен (таймаут). Укажите в BOT_PROXY другой рабочий прокси."
            )
        else:
            print(
                "\nОшибка: с этого сервера нет доступа к api.telegram.org (таймаут/блокировка)."
            )
            print("Варианты: 1) Укажите в .env рабочий BOT_PROXY (socks5://хост:порт).")
            print("          2) Запустите бота на VPS за рубежом (где Telegram не блокируют).")
        raise


# Обратная совместимость со старым именем
async def run_main() -> None:
    await main()


if __name__ == "__main__":
    import asyncio

    print("Бот запускается...")
    asyncio.run(main())
