"""
Custom (Premium) Emoji konfiguratsiyasi.
Bu yerdagi ID raqamlarni @emojiid_get_bot orqali olib qo'ysangiz,
Telegram tugmalari ichida rangli va chiroyli Custom Emojilar chiqadi!
"""

# @emojiid_get_bot dan olingan ID raqamlar shu yerga yoziladi
CUSTOM_EMOJI_IDS = {
    "star": "",          # ✨ / ⭐ E'lon berish tugmasi
    "my_posts": "",      # 📋 Mening e'lonlarim
    "channels": "",      # 📢 Kanallarimiz
    "prices": "",        # 💰 Narxlar
    "phone": "",         # 📞 Aloqa va Yordam
    "fast_post": "",     # 🚀 Tayyor reklama yuborish
    "wizard_post": "",   # 📝 Bosqichma-bosqich to'ldirish
    "check": "",         # ✅ Tasdiqlash / Tekshirish
    "edit": "",          # ✏️ Tahrirlash
    "cancel": "",        # ❌ Bekor qilish
    "photo": "",         # 📸 Rasm / Banner
    "send_now": "",      # ⚡️ / 🚀 Hozir kanalga chiqarish
    "card": "",          # 💳 To'lov / Karta
    "admin": "",         # 🔐 Admin panel
    "queue": "",         # ⏳ Navbat
    "broadcast": "",     # 📨 Xabar tarqatish
    "stats": "",         # 📊 Statistika
}


def get_emoji_id(key: str) -> str:
    """Emoji ID sini olish (agar bo'sh bo'lsa None qaytaradi)."""
    val = CUSTOM_EMOJI_IDS.get(key, "").strip()
    return val if val else None
