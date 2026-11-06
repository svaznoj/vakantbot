"""Bot konfiguratsiyasi."""
import os
from dotenv import load_dotenv

load_dotenv()

# ==================== BOT SOZLAMALARI ====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# ==================== ADMIN ====================
# Admin Telegram ID lari (vergul bilan ajratilgan)
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

# ==================== KANALLAR ====================
# Kanallar ro'yxati: {kanal_id: {nom, narx, username}}
CHANNELS = {
    # Namuna kanallar - o'zingizning kanallaringizni qo'shing
    "channel_1": {
        "name": "💼 Ish Topish | Toshkent",
        "username": "@ish_topish_toshkent",
        "chat_id": -1001234567890,  # Kanal chat ID
        "price": 50000,  # UZS
        "currency": "UZS",
        "description": "Toshkent shahridagi eng yirik vakansiya kanali",
        "subscribers": "50K+",
    },
    "channel_2": {
        "name": "🏢 Vakansiyalar O'zbekiston",
        "username": "@vakansiyalar_uz",
        "chat_id": -1001234567891,
        "price": 80000,
        "currency": "UZS",
        "description": "O'zbekiston bo'ylab vakansiyalar",
        "subscribers": "100K+",
    },
    "channel_3": {
        "name": "👨‍💻 IT Vakansiyalar",
        "username": "@it_vakansiyalar",
        "chat_id": -1001234567892,
        "price": 100000,
        "currency": "UZS",
        "description": "IT sohasidagi vakansiyalar",
        "subscribers": "30K+",
    },
}

# ==================== TO'LOV ====================
PAYMENT_CARD = os.getenv("PAYMENT_CARD", "8600 1234 5678 9012")
PAYMENT_CARD_HOLDER = os.getenv("PAYMENT_CARD_HOLDER", "ISMINGIZ FAMILIYANGIZ")
PAYMENT_PHONE = os.getenv("PAYMENT_PHONE", "+998901234567")

# To'lov tekshirish turi: "manual" (admin tasdiqlaydi) yoki "auto" (chek screenshot)
PAYMENT_CHECK_MODE = os.getenv("PAYMENT_CHECK_MODE", "manual")

# ==================== E'LON SOZLAMALARI ====================
# E'lon navbati - har necha daqiqada bir e'lon joylanadi
POST_INTERVAL_MINUTES = int(os.getenv("POST_INTERVAL_MINUTES", "30"))

# E'lon joylash vaqti oralig'i (soat)
POST_START_HOUR = int(os.getenv("POST_START_HOUR", "8"))
POST_END_HOUR = int(os.getenv("POST_END_HOUR", "22"))

# E'lon necha kun turadi kanalda (0 = o'chirilmaydi)
POST_LIFETIME_DAYS = int(os.getenv("POST_LIFETIME_DAYS", "0"))

# ==================== MA'LUMOTLAR BAZASI ====================
DATABASE_PATH = os.getenv("DATABASE_PATH", "vacancy_bot.db")

# ==================== ISH TURLARI ====================
JOB_TYPES = [
    "👨‍💻 IT / Dasturchi",
    "📊 Buxgalter / Moliyachi",
    "🏗 Qurilish",
    "🍽 Oshpaz / Ofitsiant",
    "🚗 Haydovchi",
    "🏪 Sotuvchi",
    "📞 Operator / Call-center",
    "🔧 Usta / Texnik",
    "📋 Ofis xodimi",
    "👨‍🏫 O'qituvchi / Mentor",
    "💊 Tibbiyot",
    "🏭 Zavod / Fabrika",
    "📦 Omborchi / Yuk tashuvchi",
    "🧹 Tozalik xodimi",
    "🛡 Qorovul / Xavfsizlik",
    "📱 SMM / Marketing",
    "🎨 Dizayner",
    "🏠 Uy xodimlari",
    "🔄 Boshqa",
]

# ==================== EMOJILAR ====================
EMOJI = {
    "company": "🏢",
    "job": "💼",
    "workers": "👥",
    "salary": "💰",
    "schedule": "🕐",
    "address": "📍",
    "phone": "📞",
    "info": "📝",
    "check": "✅",
    "cross": "❌",
    "money": "💳",
    "time": "⏰",
    "channel": "📢",
    "star": "⭐",
    "rocket": "🚀",
    "warning": "⚠️",
}
