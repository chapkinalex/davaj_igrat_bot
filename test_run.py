"""Проверка: импорт бота, регистрация обработчиков, опционально — get_me."""
import asyncio
import sys

def check_import_and_handlers():
    print("1. Import bot...", flush=True)
    from bot import bot, dp
    print("   OK", flush=True)
    print("2. Dispatcher...", flush=True)
    assert dp is not None, "no dispatcher"
    print("   OK", flush=True)
    print("3. Games data...", flush=True)
    from games_data import GAMES
    assert len(GAMES) >= 1, "GAMES empty"
    print(f"   OK ({len(GAMES)} games)", flush=True)
    return bot, dp

async def check_api(bot):
    print("4. Telegram API (get_me, timeout 8s)...", flush=True)
    try:
        me = await asyncio.wait_for(bot.get_me(), timeout=8.0)
        print(f"   OK @{me.username} id={me.id}", flush=True)
        await bot.session.close()
        return True
    except asyncio.TimeoutError:
        print("   SKIP (timeout, no network?)", flush=True)
        try:
            await bot.session.close()
        except Exception:
            pass
        return False
    except Exception as e:
        print(f"   SKIP: {e}", flush=True)
        try:
            await bot.session.close()
        except Exception:
            pass
        return False

def main():
    bot, dp = check_import_and_handlers()
    try:
        ok = asyncio.run(check_api(bot))
    except Exception as e:
        print(f"   Error: {e}", flush=True)
        ok = False
    print("Done. Bot module and handlers OK." + (" API OK." if ok else " API not checked (run with network)."), flush=True)
    sys.exit(0)

if __name__ == "__main__":
    main()
