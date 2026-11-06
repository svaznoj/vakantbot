"""Inline va reply klaviaturalar (Custom Emoji va keng qatorlar bilan)."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import JOB_TYPES
from database import get_posting_channels, get_all_mandatory_channels, get_setting
from config_emojis import get_emoji_id


def btn(text: str, callback_data: str = None, url: str = None, emoji_key: str = None) -> InlineKeyboardButton:
    """Tugma yaratish — agar Custom Emoji ID kiritilgan bo'lsa uni qo'shadi."""
    kwargs = {"text": text}
    if callback_data:
        kwargs["callback_data"] = callback_data
    if url:
        kwargs["url"] = url
    emoji_id = get_emoji_id(emoji_key) if emoji_key else None
    if emoji_id:
        kwargs["icon_custom_emoji_id"] = emoji_id
    return InlineKeyboardButton(**kwargs)


def main_menu_kb() -> InlineKeyboardMarkup:
    """Asosiy menyu — tugmalar keng va alohida qatorlarda."""
    buttons = [
        [btn("✨ E'lon berish", callback_data="new_post", emoji_key="star")],
        [btn("📋 Mening e'lonlarim", callback_data="my_posts", emoji_key="my_posts")],
        [
            btn("📢 Kanallarimiz", callback_data="show_channels", emoji_key="channels"),
            btn("💰 Narxlar", callback_data="show_prices", emoji_key="prices")
        ],
        [btn("📞 Aloqa va Yordam", callback_data="contact_admin", emoji_key="phone")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def post_mode_kb() -> InlineKeyboardMarkup:
    """E'lon berish usulini tanlash (Tayyor reklama yoki savol-javob)."""
    buttons = [
        [btn("🚀 Tayyor reklamam bor (Tezkor joylash)", callback_data="mode_ready_post", emoji_key="fast_post")],
        [btn("📝 Bosqichma-bosqich to'ldirish (Savol-javob)", callback_data="mode_wizard_post", emoji_key="wizard_post")],
        [btn("❌ Bekor qilish", callback_data="cancel", emoji_key="cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def channels_selection_kb(selected: list) -> InlineKeyboardMarkup:
    """Tanlangan kanallar bilan ro'yxat."""
    channels = get_posting_channels(only_active=True)
    buttons = []

    for key, ch in channels.items():
        price_formatted = f"{ch['price']:,}".replace(",", " ")
        check = "✅" if key in selected else "⬜"
        text = f"{check} {ch['name']} — {price_formatted} UZS"
        buttons.append([btn(text, callback_data=f"toggle_ch_{key}")])

    if selected:
        total = sum(channels[k]["price"] for k in selected if k in channels)
        total_formatted = f"{total:,}".replace(",", " ")
        buttons.append([
            btn(f"💳 Jami: {total_formatted} UZS — Davom etish ➡️", callback_data="channels_done", emoji_key="card")
        ])
    else:
        buttons.append([
            btn("👆 Kamida bitta kanal tanlang", callback_data="noop")
        ])

    buttons.append([btn("❌ Bekor qilish", callback_data="cancel", emoji_key="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def photo_choice_kb() -> InlineKeyboardMarkup:
    """E'lon uchun rasm turi tanlovi."""
    buttons = [
        [btn("📸 O'z rasmimni yuklayman", callback_data="photo_upload_custom", emoji_key="photo")],
        [btn("🖼 Umumiy banner qo'yilsin", callback_data="photo_use_default", emoji_key="photo")],
        [btn("📄 Rasmsiz (Faqat matn)", callback_data="photo_skip")],
        [btn("❌ Bekor qilish", callback_data="cancel", emoji_key="cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def job_types_kb() -> InlineKeyboardMarkup:
    """Ish turlari — har qatorda 2 tadan qulay joylashgan."""
    buttons = []
    row = []
    for i, jt in enumerate(JOB_TYPES):
        row.append(btn(jt, callback_data=f"job_{i}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([btn("❌ Bekor qilish", callback_data="cancel", emoji_key="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_vacancy_kb() -> InlineKeyboardMarkup:
    """E'lonni tasdiqlash."""
    buttons = [
        [btn("✅ Tasdiqlash va to'lovga o'tish", callback_data="confirm_vacancy", emoji_key="check")],
        [btn("✏️ Tahrirlash", callback_data="edit_vacancy", emoji_key="edit")],
        [btn("❌ Bekor qilish", callback_data="cancel", emoji_key="cancel")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def edit_fields_kb() -> InlineKeyboardMarkup:
    """Tahrirlash maydonlari — keng va chiroyli."""
    buttons = [
        [btn("🏢 Kompaniya nomi", callback_data="edit_company"),
         btn("💼 Ish turi", callback_data="edit_job_type")],
        [btn("👥 Kerakli ishchilar", callback_data="edit_workers"),
         btn("💵 Oylik maosh", callback_data="edit_salary")],
        [btn("⏳ Ish vaqti", callback_data="edit_schedule"),
         btn("📍 Manzil", callback_data="edit_address")],
        [btn("📲 Telefon raqami", callback_data="edit_phone"),
         btn("📝 Talablar", callback_data="edit_requirements")],
        [btn("🖼 Rasm / Banner", callback_data="edit_photo", emoji_key="photo"),
         btn("📌 Qo'shimcha", callback_data="edit_additional")],
        [btn("⬅️ Ortga (Preview)", callback_data="back_to_preview")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def payment_kb(vacancy_id: int) -> InlineKeyboardMarkup:
    """Foydalanuvchi to'lov ekrani tugmalari."""
    buttons = [
        [btn("⚡️ To'lovni tekshirish", callback_data=f"check_payment_{vacancy_id}", emoji_key="check")],
        [btn("📸 Chek screenshotini yuborish", callback_data=f"send_receipt_{vacancy_id}", emoji_key="photo")],
        [btn("❌ Bekor qilish", callback_data="cancel", emoji_key="cancel")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_payment_kb(vacancy_id: int) -> InlineKeyboardMarkup:
    """Admin to'lov tasdiqlash."""
    buttons = [
        [
            btn("✅ Tasdiqlash", callback_data=f"admin_approve_{vacancy_id}", emoji_key="check"),
            btn("🚀 HOZIR chiqarish", callback_data=f"admin_approve_and_post_{vacancy_id}", emoji_key="send_now"),
        ],
        [btn("❌ Rad etish", callback_data=f"admin_reject_{vacancy_id}", emoji_key="cancel")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def skip_kb(field_name: str = "") -> InlineKeyboardMarkup:
    buttons = [
        [btn("⏭ O'tkazib yuborish", callback_data=f"skip_{field_name}")],
        [btn("❌ Bekor qilish", callback_data="cancel", emoji_key="cancel")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_to_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [btn("🏠 Bosh menyu", callback_data="main_menu")]
    ])


# ==================== ADMIN KLAVIATURALARI ====================

def admin_menu_kb() -> InlineKeyboardMarkup:
    """Mukammal Admin boshqaruv menyusi."""
    buttons = [
        [btn("💳 Kutilayotgan to'lovlar", callback_data="admin_pending", emoji_key="card")],
        [btn("⏳ Navbatdagi e'lonlar", callback_data="admin_queue", emoji_key="queue")],
        [btn("📢 Majburiy obuna kanallari", callback_data="admin_mandatory_channels", emoji_key="channels")],
        [btn("💼 E'lon kanallari & Narxlar", callback_data="admin_posting_channels", emoji_key="prices")],
        [btn("🖼 Umumiy rasm / Banner", callback_data="admin_banner_settings", emoji_key="photo")],
        [btn("💳 Karta sozlamalari", callback_data="admin_card_settings", emoji_key="card")],
        [btn("📊 Mukammal Statistika", callback_data="admin_stats", emoji_key="stats")],
        [btn("📨 Xabar tarqatish (Broadcast)", callback_data="admin_broadcast", emoji_key="broadcast")],
        [btn("🏠 Bosh menyuga qaytish", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_mandatory_channels_kb() -> InlineKeyboardMarkup:
    channels = get_all_mandatory_channels()
    buttons = []
    for ch in channels:
        status_icon = "🟢" if ch["is_active"] else "🔴"
        title = ch["title"]
        buttons.append([
            btn(f"{status_icon} {title}", callback_data=f"adm_mch_info_{ch['channel_id']}"),
            btn("❌ O'chirish", callback_data=f"adm_mch_del_{ch['channel_id']}", emoji_key="cancel")
        ])

    buttons.append([btn("➕ Yangi majburiy kanal qo'shish", callback_data="adm_mch_add")])
    buttons.append([btn("⬅️ Admin panelga qaytish", callback_data="admin_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_posting_channels_kb() -> InlineKeyboardMarkup:
    channels = get_posting_channels(only_active=False)
    buttons = []
    for key, ch in channels.items():
        price = f"{ch['price']:,}".replace(",", " ")
        buttons.append([
            btn(f"📢 {ch['name']} ({price} so'm)", callback_data=f"adm_pch_info_{key}"),
            btn("❌ O'chirish", callback_data=f"adm_pch_del_{key}", emoji_key="cancel")
        ])

    buttons.append([btn("➕ Yangi e'lon kanali qo'shish", callback_data="adm_pch_add")])
    buttons.append([btn("⬅️ Admin panelga qaytish", callback_data="admin_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_banner_kb() -> InlineKeyboardMarkup:
    current_banner = get_setting("default_banner_file_id", "")
    buttons = []
    if current_banner:
        buttons.append([btn("👁 Hozirgi bannerni ko'rish", callback_data="adm_banner_view")])
        buttons.append([btn("🗑 Bannerni o'chirish", callback_data="adm_banner_remove", emoji_key="cancel")])
    buttons.append([btn("📤 Yangi banner yuklash", callback_data="adm_banner_set", emoji_key="photo")])
    buttons.append([btn("⬅️ Admin panelga qaytish", callback_data="admin_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
