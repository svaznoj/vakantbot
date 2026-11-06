"""
Vakansiya E'lon Bot - Mukammal versiya

Xususiyatlar:
- @humocardbot / SMS bildirishnomalari orqali 100% AVTO to'lov (unikal summa orqali: masalan 1000 emas, 1003 so'm)
- Cheksiz Majburiy obuna kanallarini ulash va o'chirish (Admin panel orqali)
- Tayyor reklama rasmini yuklash yoki hamma uchun umumiy banner biriktirish
- Mukammal Admin Panel (kanallar, narxlar, kutilayotgan to'lovlar, broadcast, karta sozlamalari, statistika)
- Premium estetik emojilar va formatlash
- Avtomatik navbat tizimi

Ishga tushirish: python bot.py
"""
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

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
        logging.FileHandler("bot.log", encoding="utf-8"),
    ]
)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    logger.info("Bot ishga tushmoqda...")
    init_db()
    logger.info("Ma'lumotlar bazasi tayyor va yangilandi.")

    bot_info = await bot.get_me()
    logger.info(f"Bot faol: @{bot_info.username} ({bot_info.full_name})")

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                f"🟢 <b>Bot muvaffaqiyatli ishga tushdi!</b>\n\n"
                f"🤖 @{bot_info.username}\n"
                f"⚡️ Barcha yangi imkoniyatlar (Avto to'lov, Majburiy obuna, Banner, Admin panel) faol!",
                parse_mode="HTML"
            )
        except Exception:
            pass


async def on_shutdown(bot: Bot):
    logger.info("Bot to'xtatilmoqda...")
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, "🔴 <b>Bot to'xtatildi!</b>", parse_mode="HTML")
        except Exception:
            pass


async def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ BOT_TOKEN o'rnatilmagan! Iltimos, .env fayliga haqiqiy bot tokenni kiriting.")
        print("\n" + "=" * 50)
        print("❌ BOT_TOKEN O'RNATILMAGAN!")
        print("Iltimos, .env fayliga @BotFather dan olingan tokenni kiriting.")
        print("=" * 50 + "\n")
        return

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Handler routerlarini ro'yxatdan o'tkazish
    dp.include_router(start.router)
    dp.include_router(posting.router)
    dp.include_router(admin.router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    scheduler = PostScheduler(bot)

    try:
        await scheduler.start()
        logger.info("Avtomatik joylashtirish navbati (Scheduler) ishga tushdi.")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await scheduler.stop()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot qo'lda to'xtatildi.")
    except Exception as e:
        logger.critical(f"Kutilmagan xatolik: {e}")
        raise
