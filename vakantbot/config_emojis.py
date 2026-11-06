"""
Telegram Premium Custom Emoji konfiguratsiyasi.
@emojiid_get_bot orqali olingan haqiqiy Premium Custom Emoji ID raqamlari ulandi!
"""

CUSTOM_EMOJI_IDS = {
    # 🏠 ASOSIY MENYU TUGMALARI
    "menu_new_post": "5458910988063490081",       # ✨ E'lon berish
    "menu_my_posts": "5271628569754222702",       # 📋 Mening e'lonlarim
    "menu_channels": "5458603970916270333",       # 📢 Kanallarimiz
    "menu_prices": "5224257782013769471",         # 💰 Narxlar
    "menu_contact": "5947494995798789024",        # 📞 Aloqa va Yordam

    # 🚀 E'LON BERISH USULI
    "mode_fast": "5458660222102945723",           # 🔥 Tayyor reklama (Tezkor)
    "mode_wizard": "5837003105228558796",         # 📝 Bosqichma-bosqich

    # 💳 TO'LOV VA AMALLAR
    "action_confirm": "5460889834115579771",      # ✅ Tasdiqlash
    "action_check_pay": "5220195537520711716",    # ⚡️ To'lovni tekshirish
    "action_receipt": "4967502231877190509",      # 📸 Chek screenshot yuborish
    "action_post_now": "5188481279963715781",     # 🚀 Hozir kanalga chiqarish
    "action_edit": "5395444784611480792",         # ✏️ Tahrirlash
    "action_cancel": "5458584785297358372",       # ❌ Bekor qilish
    "action_back": "5416041192905265756",         # 🏠 Bosh menyu / Ortga

    # 🖼 RASM TANLOVI
    "photo_custom": "4967502231877190509",        # 📸 O'z rasmim
    "photo_default": "5458643952766829184",       # 🖼 Umumiy banner
    "photo_skip": "5271628569754222702",          # 📄 Rasmsiz

    # 🔐 ADMIN PANEL TUGMALARI
    "admin_pending": "5059845514799875196",       # 💳 Kutilayotgan to'lovlar
    "admin_queue": "5319190934510904031",         # ⏳ Navbat
    "admin_mandatory": "5458603970916270333",     # 📢 Majburiy kanallar
    "admin_channels": "5458603970916270333",      # 💼 E'lon kanallari
    "admin_banner": "5458643952766829184",        # 🎨 / 🖼 Banner sozlamalari
    "admin_card": "5059845514799875196",          # 💳 Karta sozlamalari
    "admin_stats": "5203993413346680064",         # 📊 Statistika
    "admin_broadcast": "5253742260054409879",     # 📨 Xabar tarqatish
}


def get_emoji_id(key: str) -> str:
    """Emoji ID sini olish."""
    val = CUSTOM_EMOJI_IDS.get(key, "").strip()
    return val if val else None
