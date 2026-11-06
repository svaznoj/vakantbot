"""
Auto Forwarder — @humocardbot dan to'lov xabarlarini Vakansiya Botiga avtomatik yetkazuvchi modul.

Ishlash tartibi:
1. my.telegram.org saytidan olingan API_ID va API_HASH orqali akkauntingizga ulanadi.
2. @humocardbot dan kelgan har bir yangi to'lov xabarini 1 soniyada Vakansiya botingizga uzatadi.
3. Vakansiya boti unikal summani (masalan, 1003 so'm) o'qib, e'lonni 100% AVTOMATIK tasdiqlaydi!

Ishga tushirish:
python auto_forwarder.py
"""
import os
import sys
import logging
from dotenv import load_dotenv

# UTF-8 konsol chiqishi
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [AutoForwarder] - %(levelname)s - %(message)s"
)
logger = logging.getLogger("AutoForwarder")

API_ID_ENV = os.getenv("TELEGRAM_API_ID", "")
API_HASH_ENV = os.getenv("TELEGRAM_API_HASH", "")
TARGET_BOT_USERNAME = os.getenv("TARGET_BOT_USERNAME", "").replace("@", "").strip()
MONITOR_BOTS = [b.replace("@", "").strip().lower() for b in os.getenv("MONITOR_BOTS", "humocardbot").split(",") if b.strip()]

try:
    from telethon import TelegramClient, events
except ImportError:
    logger.critical("Telethon o'rnatilmagan! 'pip install telethon' buyrug'ini bering.")
    sys.exit(1)


def check_configuration():
    """Sozlamalarni tekshirish."""
    if not API_ID_ENV or not API_HASH_ENV or API_ID_ENV == "12345678":
        print("\n" + "=" * 60)
        print("⚠️ DIQQAT: TELEGRAM_API_ID yoki TELEGRAM_API_HASH SOZLANMAGAN!")
        print("=" * 60)
        print("1. https://my.telegram.org saytiga kiring (telefon raqamingiz bilan)")
        print("2. 'API development tools' bo'limiga o'ting")
        print("3. Yangi ilova yarating va berilgan API ID hamda API HASH ni oling")
        print("4. .env fayliga quyidagilarni kiriting:")
        print("   TELEGRAM_API_ID=sizning_api_id")
        print("   TELEGRAM_API_HASH=sizning_api_hash")
        print("   TARGET_BOT_USERNAME=@sizning_vakansiya_botingiz")
        print("   MONITOR_BOTS=humocardbot")
        print("=" * 60 + "\n")
        return False
    return True


async def start_forwarder():
    """Forwarderni ishga tushirish."""
    if not check_configuration():
        return

    api_id = int(API_ID_ENV)
    api_hash = API_HASH_ENV

    session_name = "payment_monitor_session"
    client = TelegramClient(session_name, api_id, api_hash)

    print("\n🟢 Telegram akkauntga ulanilmoqda...")
    await client.start()
    
    me = await client.get_me()
    print(f"✅ Akkaunt faol: {me.first_name} (@{me.username or me.phone})")
    print(f"👀 Kuzatilayotgan botlar: {', '.join(['@' + b for b in MONITOR_BOTS])}")
    print(f"🎯 Xabarlar yuboriladigan bot: @{TARGET_BOT_USERNAME}")
    print("⚡️ Forwarder ishlamoqda. @humocardbot dan kelgan xabarlar avtomatik uzatiladi...\n")

    @client.on(events.NewMessage)
    async def handle_incoming(event):
        try:
            sender = await event.get_sender()
            sender_username = getattr(sender, "username", "") or ""
            sender_username_clean = sender_username.lower().replace("@", "")

            # Agar xabar kuzatilayotgan botlardan kelgan bo'lsa
            if sender_username_clean in MONITOR_BOTS:
                logger.info(f"Yangi to'lov xabari qabul qilindi: @{sender_username}")
                # Vakansiya botiga forward qilish
                await client.forward_messages(TARGET_BOT_USERNAME, event.message)
                logger.info(f"✅ Xabar muvaffaqiyatli @{TARGET_BOT_USERNAME} ga uzatildi!")

        except Exception as err:
            logger.error(f"Xabarni uzatishda xatolik: {err}")

    await client.run_until_disconnected()


if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(start_forwarder())
    except KeyboardInterrupt:
        print("\n🔴 Forwarder to'xtatildi.")
