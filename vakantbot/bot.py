"""
Vakansiya E'lon Bot - Mukammal versiya (Railway & Cloud qo'llab-quvvatlash bilan)
"""
import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiohttp import web

from config import BOT_TOKEN, ADMIN_IDS
from database import init_db
from handlers import start, posting, admin
from utils.scheduler import PostScheduler

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)


# Railway/Render uchun Healthcheck server
async def health_check_handler(request):
    return web.Response(text="Bot is running! OK", status=200)


async def start_dummy_web_server():
    """Hosting PORT berganda port tinglovchi server yoqish."""
    port_str = os.getenv("PORT")
    if not port_str:
        return None
    try:
        port = int(port_str)
        app = web.Application()
        app.router.add_get("/", health_check_handler)
        app.router.add_get("/health", health_check_handler)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        logger.info(f"Hosting uchun Healthcheck server ishga tushdi: port {port}")
        return runner
    except Exception as e:
        logger.warning(f"Dummy web server xatosi: {e}")
        return None


async def on_startup(bot: Bot):
    logger.info("Bot ishga tushmoqda...")
    init_db()
    logger.info("Ma'lumotlar bazasi tayyor va yangilandi.")

    try:
        bot_info = await bot.get_me()
        logger.info(f"Bot muvaffaqiyatli ulandi: @{bot_info.username} ({bot_info.full_name})")
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    admin_id,
                    f"🟢 <b>Bot ishga tushdi!</b>\n\n🤖 @{bot_info.username}\n🔐 Admin panel: /admin",
                    parse_mode="HTML"
                )
            except Exception:
                pass
    except Exception as e:
        logger.error(f"Bot ma'lumotlarini olishda xato: {e}")


async def on_shutdown(bot: Bot):
    logger.info("Bot to'xtatilmoqda...")
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, "🔴 <b>Bot to'xtatildi!</b>", parse_mode="HTML")
        except Exception:
            pass


async def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.critical("❌ XATOLIK: BOT_TOKEN o'rnatilmagan! Railway Variables bo'limiga BOT_TOKEN ni kiriting.")
        return

    web_runner = await start_dummy_web_server()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # MUHIM: Admin router birinchi bo'lishi shart!
    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(posting.router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    scheduler = PostScheduler(bot)

    try:
        await scheduler.start()
        logger.info("Avtomatik navbat (Scheduler) ishga tushdi.")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await scheduler.stop()
        if web_runner:
            await web_runner.cleanup()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot to'xtatildi.")
    except Exception as e:
        logger.critical(f"Kutilmagan xatolik: {e}")
        raise
