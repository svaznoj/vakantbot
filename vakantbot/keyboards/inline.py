"""Inline va reply klaviaturalar."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import JOB_TYPES
from database import get_posting_channels, get_all_mandatory_channels, get_setting


def main_menu_kb() -> InlineKeyboardMarkup:
    """Asosiy menyu."""
    buttons = [
        [InlineKeyboardButton(text="✨ E'lon berish", callback_data="new_post")],
        [InlineKeyboardButton(text="📋 Mening e'lonlarim", callback_data="my_posts")],
        [InlineKeyboardButton(text="📢 Kanallarimiz", callback_data="show_channels"),
         InlineKeyboardButton(text="💰 Narxlar", callback_data="show_prices")],
        [InlineKeyboardButton(text="📞 Aloqa va Yordam", callback_data="contact_admin")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def channels_selection_kb(selected: list) -> InlineKeyboardMarkup:
    """Tanlangan kanallar bilan dinamik ro'yxat."""
    channels = get_posting_channels(only_active=True)
    buttons = []

    for key, ch in channels.items():
        price_formatted = f"{ch['price']:,}".replace(",", " ")
        check = "✅" if key in selected else "⬜"
        text = f"{check} {ch['name']} — {price_formatted} UZS"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"toggle_ch_{key}")])

    if selected:
        total = sum(channels[k]["price"] for k in selected if k in channels)
        total_formatted = f"{total:,}".replace(",", " ")
        buttons.append([
            InlineKeyboardButton(
                text=f"💳 Jami: {total_formatted} UZS — Davom etish ➡️",
                callback_data="channels_done"
            )
        ])
    else:
        buttons.append([
            InlineKeyboardButton(text="👆 Kamida bitta kanal tanlang", callback_data="noop")
        ])

    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def photo_choice_kb() -> InlineKeyboardMarkup:
    """E'lon uchun rasm turi tanlovi."""
    buttons = [
        [InlineKeyboardButton(text="📸 O'z rasmimni yuklayman", callback_data="photo_upload_custom")],
        [InlineKeyboardButton(text="🖼 Umumiy banner qo'yilsin", callback_data="photo_use_default")],
        [InlineKeyboardButton(text="📄 Rasmsiz (Faqat matn)", callback_data="photo_skip")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def job_types_kb() -> InlineKeyboardMarkup:
    """Ish turlari."""
    buttons = []
    row = []
    for i, jt in enumerate(JOB_TYPES):
        row.append(InlineKeyboardButton(text=jt, callback_data=f"job_{i}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_vacancy_kb() -> InlineKeyboardMarkup:
    """E'lonni tasdiqlash."""
    buttons = [
        [
            InlineKeyboardButton(text="✅ Tasdiqlash va to'lovga o'tish", callback_data="confirm_vacancy"),
        ],
        [
            InlineKeyboardButton(text="✏️ Tahrirlash", callback_data="edit_vacancy"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def edit_fields_kb() -> InlineKeyboardMarkup:
    """Tahrirlash uchun maydonlar."""
    buttons = [
        [InlineKeyboardButton(text="🏢 Kompaniya nomi", callback_data="edit_company"),
         InlineKeyboardButton(text="💼 Ish turi", callback_data="edit_job_type")],
        [InlineKeyboardButton(text="👥 Kerakli ishchilar", callback_data="edit_workers"),
         InlineKeyboardButton(text="💰 Oylik maosh", callback_data="edit_salary")],
        [InlineKeyboardButton(text="🕐 Ish vaqti", callback_data="edit_schedule"),
         InlineKeyboardButton(text="📍 Manzil", callback_data="edit_address")],
        [InlineKeyboardButton(text="📞 Telefon raqami", callback_data="edit_phone"),
         InlineKeyboardButton(text="📋 Talablar", callback_data="edit_requirements")],
        [InlineKeyboardButton(text="🖼 Rasm / Banner", callback_data="edit_photo"),
         InlineKeyboardButton(text="ℹ️ Qo'shimcha", callback_data="edit_additional")],
        [InlineKeyboardButton(text="⬅️ Ortga (Preview)", callback_data="back_to_preview")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def payment_kb(vacancy_id: int) -> InlineKeyboardMarkup:
    """Foydalanuvchi to'lov ekrani tugmalari."""
    buttons = [
        [InlineKeyboardButton(text="⚡️ To'lovni tekshirish", callback_data=f"check_payment_{vacancy_id}")],
        [InlineKeyboardButton(text="📸 Chek screenshotini yuborish", callback_data=f"send_receipt_{vacancy_id}")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_payment_kb(vacancy_id: int) -> InlineKeyboardMarkup:
    """Admin to'lov tasdiqlash."""
    buttons = [
        [
            InlineKeyboardButton(text="✅ To'lovni tasdiqlash", callback_data=f"admin_approve_{vacancy_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"admin_reject_{vacancy_id}"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def skip_kb(field_name: str = "") -> InlineKeyboardMarkup:
    """O'tkazib yuborish tugmasi."""
    buttons = [
        [InlineKeyboardButton(text="⏭ O'tkazib yuborish", callback_data=f"skip_{field_name}")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_to_menu_kb() -> InlineKeyboardMarkup:
    """Bosh menyuga qaytish."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu")]
    ])


# ==================== ADMIN KLAVIATURALARI ====================

def admin_menu_kb() -> InlineKeyboardMarkup:
    """Mukammal Admin boshqaruv menyusi."""
    buttons = [
        [InlineKeyboardButton(text="💳 Kutilayotgan to'lovlar", callback_data="admin_pending"),
         InlineKeyboardButton(text="📋 Navbatdagi e'lonlar", callback_data="admin_queue")],
        [InlineKeyboardButton(text="📢 Majburiy obuna kanallari", callback_data="admin_mandatory_channels")],
        [InlineKeyboardButton(text="💼 E'lon kanallari & Narxlar", callback_data="admin_posting_channels")],
        [InlineKeyboardButton(text="🖼 Umumiy rasm / Banner", callback_data="admin_banner_settings"),
         InlineKeyboardButton(text="💳 Karta sozlamalari", callback_data="admin_card_settings")],
        [InlineKeyboardButton(text="📊 Mukammal Statistika", callback_data="admin_stats"),
         InlineKeyboardButton(text="📨 Xabar tarqatish (Broadcast)", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🏠 Bosh menyuga qaytish", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_mandatory_channels_kb() -> InlineKeyboardMarkup:
    """Majburiy kanallar boshqaruvi."""
    channels = get_all_mandatory_channels()
    buttons = []
    for ch in channels:
        status_icon = "🟢" if ch["is_active"] else "🔴"
        title = ch["title"]
        buttons.append([
            InlineKeyboardButton(text=f"{status_icon} {title}", callback_data=f"adm_mch_info_{ch['channel_id']}"),
            InlineKeyboardButton(text="❌ O'chirish", callback_data=f"adm_mch_del_{ch['channel_id']}")
        ])

    buttons.append([InlineKeyboardButton(text="➕ Yangi majburiy kanal qo'shish", callback_data="adm_mch_add")])
    buttons.append([InlineKeyboardButton(text="⬅️ Admin panelga qaytish", callback_data="admin_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_posting_channels_kb() -> InlineKeyboardMarkup:
    """E'lon chiqadigan kanallar boshqaruvi."""
    channels = get_posting_channels(only_active=False)
    buttons = []
    for key, ch in channels.items():
        price = f"{ch['price']:,}".replace(",", " ")
        buttons.append([
            InlineKeyboardButton(text=f"📢 {ch['name']} ({price} so'm)", callback_data=f"adm_pch_info_{key}"),
            InlineKeyboardButton(text="❌ O'chirish", callback_data=f"adm_pch_del_{key}")
        ])

    buttons.append([InlineKeyboardButton(text="➕ Yangi e'lon kanali qo'shish", callback_data="adm_pch_add")])
    buttons.append([InlineKeyboardButton(text="⬅️ Admin panelga qaytish", callback_data="admin_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_banner_kb() -> InlineKeyboardMarkup:
    """Banner sozlamalari."""
    current_banner = get_setting("default_banner_file_id", "")
    buttons = []
    if current_banner:
        buttons.append([InlineKeyboardButton(text="👁 Hozirgi bannerni ko'rish", callback_data="adm_banner_view")])
        buttons.append([InlineKeyboardButton(text="🗑 Bannerni o'chirish", callback_data="adm_banner_remove")])
    buttons.append([InlineKeyboardButton(text="📤 Yangi banner yuklash", callback_data="adm_banner_set")])
    buttons.append([InlineKeyboardButton(text="⬅️ Admin panelga qaytish", callback_data="admin_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
