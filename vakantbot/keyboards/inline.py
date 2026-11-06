"""Inline va reply klaviaturalar (Haqiqiy rangli style va Premium Custom Emoji bilan)."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import JOB_TYPES
from database import get_posting_channels, get_all_mandatory_channels, get_setting
from config_emojis import get_emoji_id


def btn(text: str, callback_data: str = None, url: str = None, emoji_key: str = None, style: str = None) -> InlineKeyboardButton:
    """Tugma yaratish — Premium Custom Emoji ID va rangli style bilan."""
    kwargs = {"text": text}
    if callback_data:
        kwargs["callback_data"] = callback_data
    if url:
        kwargs["url"] = url
    if style:
        kwargs["style"] = style
    emoji_id = get_emoji_id(emoji_key) if emoji_key else None
    if emoji_id:
        kwargs["icon_custom_emoji_id"] = str(emoji_id)
    return InlineKeyboardButton(**kwargs)


def main_menu_kb() -> InlineKeyboardMarkup:
    """Asosiy menyu — Yashil va Ko'k rangli, Premium emojilar bilan."""
    buttons = [
        [btn("✨ E'lon berish", callback_data="new_post", emoji_key="menu_new_post", style="success")],
        [btn("📋 Mening e'lonlarim", callback_data="my_posts", emoji_key="menu_my_posts", style="primary")],
        [
            btn("📢 Kanallarimiz", callback_data="show_channels", emoji_key="menu_channels", style="primary"),
            btn("💰 Narxlar", callback_data="show_prices", emoji_key="menu_prices", style="primary")
        ],
        [btn("📞 Aloqa va Yordam", callback_data="contact_admin", emoji_key="menu_contact", style="primary")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def post_mode_kb() -> InlineKeyboardMarkup:
    """E'lon berish usulini tanlash — Qizil (Olov/Tezkor) va Ko'k."""
    buttons = [
        [btn("🔥 Tayyor reklamam bor (Tezkor)", callback_data="mode_ready_post", emoji_key="mode_fast", style="danger")],
        [btn("📝 Bosqichma-bosqich yaratish", callback_data="mode_wizard_post", emoji_key="mode_wizard", style="primary")],
        [btn("❌ Bekor qilish", callback_data="cancel", emoji_key="action_cancel", style="danger")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def channels_selection_kb(selected: list) -> InlineKeyboardMarkup:
    """Tanlangan kanallar ro'yxati."""
    channels = get_posting_channels(only_active=True)
    buttons = []

    for key, ch in channels.items():
        price_formatted = f"{ch['price']:,}".replace(",", " ")
        if key in selected:
            text = f"✅ {ch['name']} — {price_formatted} UZS"
            buttons.append([btn(text, callback_data=f"toggle_ch_{key}", style="success")])
        else:
            text = f"📢 {ch['name']} — {price_formatted} UZS"
            buttons.append([btn(text, callback_data=f"toggle_ch_{key}", style="primary")])

    if selected:
        total = sum(channels[k]["price"] for k in selected if k in channels)
        total_formatted = f"{total:,}".replace(",", " ")
        buttons.append([
            btn(f"💳 Jami: {total_formatted} UZS — Davom etish ➡️", callback_data="channels_done", emoji_key="action_confirm", style="success")
        ])
    else:
        buttons.append([
            btn("👆 Kamida bitta kanal tanlang", callback_data="noop")
        ])

    buttons.append([btn("❌ Bekor qilish", callback_data="cancel", emoji_key="action_cancel", style="danger")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def photo_choice_kb() -> InlineKeyboardMarkup:
    """Rasm turi tanlovi."""
    buttons = [
        [btn("📸 O'z rasmimni yuklayman", callback_data="photo_upload_custom", emoji_key="photo_custom", style="primary")],
        [btn("🖼 Umumiy banner qo'yilsin", callback_data="photo_use_default", emoji_key="photo_default", style="primary")],
        [btn("📄 Rasmsiz (Faqat matn)", callback_data="photo_skip", emoji_key="photo_skip", style="primary")],
        [btn("❌ Bekor qilish", callback_data="cancel", emoji_key="action_cancel", style="danger")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def job_types_kb() -> InlineKeyboardMarkup:
    """Ish turlari — ko'k tugmalar."""
    buttons = []
    row = []
    for i, jt in enumerate(JOB_TYPES):
        row.append(btn(f"{jt}", callback_data=f"job_{i}", style="primary"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([btn("❌ Bekor qilish", callback_data="cancel", emoji_key="action_cancel", style="danger")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_vacancy_kb() -> InlineKeyboardMarkup:
    """E'lonni tasdiqlash — Yashil va Qizil tugmalar."""
    buttons = [
        [btn("✅ Tasdiqlash va to'lovga o'tish", callback_data="confirm_vacancy", emoji_key="action_confirm", style="success")],
        [
            btn("✏️ Tahrirlash", callback_data="edit_vacancy", emoji_key="action_edit", style="primary"),
            btn("❌ Bekor qilish", callback_data="cancel", emoji_key="action_cancel", style="danger")
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def edit_fields_kb() -> InlineKeyboardMarkup:
    """Tahrirlash maydonlari."""
    buttons = [
        [btn("🏢 Kompaniya", callback_data="edit_company", style="primary"), btn("💼 Ish turi", callback_data="edit_job_type", style="primary")],
        [btn("👥 Xodimlar", callback_data="edit_workers", style="primary"), btn("💵 Maosh", callback_data="edit_salary", style="primary")],
        [btn("⏳ Ish vaqti", callback_data="edit_schedule", style="primary"), btn("📍 Manzil", callback_data="edit_address", style="primary")],
        [btn("📲 Telefon", callback_data="edit_phone", style="primary"), btn("📝 Talablar", callback_data="edit_requirements", style="primary")],
        [btn("🖼 Rasm / Banner", callback_data="edit_photo", emoji_key="photo_custom", style="primary"), btn("📌 Qo'shimcha", callback_data="edit_additional", style="primary")],
        [btn("🏠 Ortga (Preview)", callback_data="back_to_preview", emoji_key="action_back", style="danger")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def payment_kb(vacancy_id: int) -> InlineKeyboardMarkup:
    """To'lov ekrani tugmalari — Yashil (Tekshirish) va Qizil (Bekor qilish)."""
    buttons = [
        [btn("⚡️ To'lovni tekshirish", callback_data=f"check_payment_{vacancy_id}", emoji_key="action_check_pay", style="success")],
        [btn("📸 Chek screenshotini yuborish", callback_data=f"send_receipt_{vacancy_id}", emoji_key="action_receipt", style="primary")],
        [btn("❌ Bekor qilish", callback_data="cancel", emoji_key="action_cancel", style="danger")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_payment_kb(vacancy_id: int) -> InlineKeyboardMarkup:
    """Admin to'lov tasdiqlash — Yashil va Qizil."""
    buttons = [
        [
            btn("✅ Tasdiqlash", callback_data=f"admin_approve_{vacancy_id}", emoji_key="action_confirm", style="success"),
            btn("🚀 HOZIR chiqarish", callback_data=f"admin_approve_and_post_{vacancy_id}", emoji_key="action_post_now", style="success"),
        ],
        [btn("❌ Rad etish", callback_data=f"admin_reject_{vacancy_id}", emoji_key="action_cancel", style="danger")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def skip_kb(field_name: str = "") -> InlineKeyboardMarkup:
    buttons = [
        [btn("⏭ O'tkazib yuborish", callback_data=f"skip_{field_name}", style="primary")],
        [btn("❌ Bekor qilish", callback_data="cancel", emoji_key="action_cancel", style="danger")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_to_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [btn("🏠 Bosh menyu", callback_data="main_menu", emoji_key="action_back", style="primary")]
    ])


# ==================== ADMIN KLAVIATURALARI ====================

def admin_menu_kb() -> InlineKeyboardMarkup:
    """Mukammal Admin boshqaruv menyusi."""
    buttons = [
        [
            btn("💳 Kutilayotgan to'lovlar", callback_data="admin_pending", emoji_key="admin_pending", style="primary"),
            btn("⏳ Navbatdagi e'lonlar", callback_data="admin_queue", emoji_key="admin_queue", style="primary")
        ],
        [btn("📢 Majburiy obuna kanallari", callback_data="admin_mandatory_channels", emoji_key="admin_mandatory", style="primary")],
        [btn("💼 E'lon kanallari & Narxlar", callback_data="admin_posting_channels", emoji_key="admin_channels", style="primary")],
        [
            btn("🖼 Umumiy rasm / Banner", callback_data="admin_banner_settings", emoji_key="admin_banner", style="primary"),
            btn("💳 Karta sozlamalari", callback_data="admin_card_settings", emoji_key="admin_card", style="primary")
        ],
        [
            btn("📊 Mukammal Statistika", callback_data="admin_stats", emoji_key="admin_stats", style="primary"),
            btn("📨 Xabar tarqatish (Broadcast)", callback_data="admin_broadcast", emoji_key="admin_broadcast", style="danger")
        ],
        [btn("🏠 Bosh menyuga qaytish", callback_data="main_menu", emoji_key="action_back", style="primary")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_mandatory_channels_kb() -> InlineKeyboardMarkup:
    channels = get_all_mandatory_channels()
    buttons = []
    for ch in channels:
        status_icon = "🟢" if ch["is_active"] else "🔴"
        title = ch["title"]
        buttons.append([
            btn(f"{status_icon} {title}", callback_data=f"adm_mch_info_{ch['channel_id']}", style="primary"),
            btn("❌ O'chirish", callback_data=f"adm_mch_del_{ch['channel_id']}", emoji_key="action_cancel", style="danger")
        ])

    buttons.append([btn("➕ Yangi majburiy kanal qo'shish", callback_data="adm_mch_add", style="success")])
    buttons.append([btn("🏠 Admin panelga qaytish", callback_data="admin_main", emoji_key="action_back", style="primary")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_posting_channels_kb() -> InlineKeyboardMarkup:
    channels = get_posting_channels(only_active=False)
    buttons = []
    for key, ch in channels.items():
        price = f"{ch['price']:,}".replace(",", " ")
        buttons.append([
            btn(f"📢 {ch['name']} ({price} so'm)", callback_data=f"adm_pch_info_{key}", style="primary"),
            btn("❌ O'chirish", callback_data=f"adm_pch_del_{key}", emoji_key="action_cancel", style="danger")
        ])

    buttons.append([btn("➕ Yangi e'lon kanali qo'shish", callback_data="adm_pch_add", style="success")])
    buttons.append([btn("🏠 Admin panelga qaytish", callback_data="admin_main", emoji_key="action_back", style="primary")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_banner_kb() -> InlineKeyboardMarkup:
    current_banner = get_setting("default_banner_file_id", "")
    buttons = []
    if current_banner:
        buttons.append([btn("👁 Hozirgi bannerni ko'rish", callback_data="adm_banner_view", style="primary")])
        buttons.append([btn("🗑 Bannerni o'chirish", callback_data="adm_banner_remove", emoji_key="action_cancel", style="danger")])
    buttons.append([btn("📤 Yangi banner yuklash", callback_data="adm_banner_set", emoji_key="photo_custom", style="success")])
    buttons.append([btn("🏠 Admin panelga qaytish", callback_data="admin_main", emoji_key="action_back", style="primary")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
