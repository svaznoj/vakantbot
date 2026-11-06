"""Vakansiya e'lonini premium ko'rinishda formatlash."""
import json
from database import get_setting, get_posting_channels

# Zamonaviy premium emojilar va belgilar
ICONS = {
    "star": "✨",
    "fire": "🔥",
    "pin": "📍",
    "briefcase": "💼",
    "company": "🏢",
    "team": "👥",
    "money": "💰",
    "clock": "⏰",
    "phone": "📞",
    "doc": "📋",
    "info": "ℹ️",
    "rocket": "🚀",
    "check": "✅",
    "cross": "❌",
    "card": "💳",
    "warning": "⚠️",
    "bell": "🔔",
    "sparkles": "🌟",
}


def format_vacancy(data: dict) -> str:
    """Vakansiya e'lonini chiroyli va qulay formatda tayyorlash."""

    company = data.get('company_name', '—')
    job_type = data.get('job_type', '—')
    workers = data.get('workers_count', '—')
    salary = data.get('salary', '—')
    schedule = data.get('work_schedule', '—')
    address = data.get('address', '—')
    phone = data.get('phone', '—')
    requirements = data.get('requirements')
    additional_info = data.get('additional_info')

    text = f"""🔥 <b>VAKANSIYA: {job_type.upper()}</b>

{ICONS['company']} <b>Tashkilot / Kompaniya:</b> <code>{company}</code>
{ICONS['briefcase']} <b>Yo'nalish:</b> {job_type}
{ICONS['team']} <b>Talab qilinadigan xodimlar:</b> {workers}
{ICONS['money']} <b>Oylik maosh:</b> <b>{salary}</b>
{ICONS['clock']} <b>Ish tartibi:</b> {schedule}
{ICONS['pin']} <b>Manzil:</b> {address}
{ICONS['phone']} <b>Aloqa:</b> <code>{phone}</code>"""

    if requirements:
        text += f"""\n\n{ICONS['doc']} <b>Talablar:</b>\n{requirements}"""

    if additional_info:
        text += f"""\n\n{ICONS['info']} <b>Qo'shimcha ma'lumot:</b>\n{additional_info}"""

    text += f"""\n\n━━━━━━━━━━━━━━━━━━━━━━\n{ICONS['rocket']} <i>Bog'lanish uchun yuqoridagi raqamga murojaat qiling!</i>"""

    return text.strip()


def format_vacancy_for_channel(data: dict) -> str:
    """Kanalga chiqariladigan e'lon formati."""
    return format_vacancy(data)


def format_vacancy_preview(data: dict, selected_channels: list) -> str:
    """Foydalanuvchiga e'lonni tasdiqlash uchun ko'rsatish."""
    vacancy_text = format_vacancy(data)
    channels_dict = get_posting_channels(only_active=False)

    channels_info = ""
    for key in selected_channels:
        if key in channels_dict:
            ch = channels_dict[key]
            price_formatted = f"{ch['price']:,}".replace(",", " ")
            channels_info += f"  📢 <b>{ch['name']}</b> — {price_formatted} UZS\n"

    exact_amount = data.get("exact_amount") or data.get("total_price") or 0
    exact_formatted = f"{exact_amount:,}".replace(",", " ")

    photo_status = "🖼 O'z rasmingiz biriktirilgan" if data.get("photo_file_id") else (
        "🖼 Umumiy kanal banneri qo'yiladi" if data.get("use_default_photo") else "📄 Faqat matnli e'lon"
    )

    text = f"""👁 <b>E'LON KO'RINIShI (PREVIEW):</b>

{vacancy_text}

━━━━━━━━━━━━━━━━━━━━━━
{photo_status}

📢 <b>Tanlangan kanallar:</b>
{channels_info if channels_info else '  <i>(Hech qanday kanal tanlanmagan)</i>'}
💳 <b>To'lov summasi:</b> <b>{exact_formatted} UZS</b>

{ICONS['check']} <i>Hammasi to'g'ri bo'lsa, tasdiqlang yoki tahrirlang:</i>"""

    return text.strip()


def format_payment_info(exact_amount: int, vacancy_id: int) -> str:
    """
    To'lov ma'lumotlari: @humocardbot orqali avto to'lov va unikal summa.
    """
    card = get_setting("payment_card", "8600 0000 0000 0000")
    holder = get_setting("payment_holder", "ADMIN")
    exact_formatted = f"{exact_amount:,}".replace(",", " ")

    text = f"""💳 <b>TO'LOV VA AVTOMATIK TEKSHIRUV</b>

📌 E'lon raqami: <code>#{vacancy_id}</code>

⚡️ <b>O'TKAZISHINGIZ KERAK BO'LGAN ANIQ SUMMA:</b>
👉 <b><code>{exact_amount}</code></b> so'm (yoki <code>{exact_formatted} UZS</code>)

⚠️ <b>DIQQAT! TO'LOV AVTO TASDIQLANISHI UCHUN:</b>
Aynan <b><code>{exact_amount}</code> so'm</b> o'tkazishingiz shart! 
<i>(Masalan, oddiy 50 000 emas, balki aynan oxiridagi so'mlarigacha aniq o'tkazing, tizim to'lovni avtomat darhol tanib oladi!)</i>

━━━━━━━━━━━━━━━━━━━━━━
💳 <b>Karta raqami:</b>
<code>{card}</code>

👤 <b>Qabul qiluvchi:</b> {holder}
━━━━━━━━━━━━━━━━━━━━━━

🤖 <b>TO'LOVNI TEKSHIRISH:</b>
1. Pulni o'tkazing (Click, Payme, Uzum va h.k.).
2. Pul tushgach, pastdagi <b>«⚡️ To'lovni tekshirish»</b> tugmasini bosing yoki chek rasmini yuboring.
3. @humocardbot / SMS bildirishnomasi orqali to'lov <b>AVTOMATIK</b> tasdiqlanadi va e'lon navbatga qo'yiladi!"""

    return text.strip()


def format_admin_notification(vacancy: dict, user_info: dict) -> str:
    """Admin uchun to'lov xabarnomasi."""
    channels_dict = get_posting_channels(only_active=False)
    channels_text = ""
    ch_keys = json.loads(vacancy["channels"]) if isinstance(vacancy["channels"], str) else vacancy.get("channels", [])
    for key in ch_keys:
        if key in channels_dict:
            channels_text += f"  📢 {channels_dict[key]['name']}\n"

    exact_amount = vacancy.get('exact_amount', vacancy.get('total_price', 0))
    price_formatted = f"{exact_amount:,}".replace(",", " ")

    text = f"""🔔 <b>YANGI TO'LOV CHEKI / HARAKATI!</b>

📌 E'lon: <code>#{vacancy['id']}</code>
👤 Foydalanuvchi: {user_info.get('full_name', '—')} (@{user_info.get('username', '—')})
🆔 User ID: <code>{vacancy['user_id']}</code>

💰 Kutilgan unikal summa: <b>{price_formatted} UZS</b> (<code>{exact_amount}</code>)
🏢 Kompaniya: <b>{vacancy.get('company_name', '—')}</b>
💼 Vakansiya: <b>{vacancy.get('job_type', '—')}</b>

📢 Joylanadigan kanallar:
{channels_text}"""

    return text.strip()


def format_stats(stats: dict) -> str:
    """Statistikani chiroyli ko'rsatish."""
    revenue_formatted = f"{stats.get('total_revenue', 0):,}".replace(",", " ")

    text = f"""📊 <b>BOTNING MUKAMMAL STATISTIKASI</b>

👥 <b>Jami foydalanuvchilar:</b> {stats.get('total_users', 0)} ta
📢 <b>Faol majburiy kanallar:</b> {stats.get('mandatory_channels_count', 0)} ta
📝 <b>Jami arizalar/e'lonlar:</b> {stats.get('total_vacancies', 0)} ta
✅ <b>Kanalga joylangan:</b> {stats.get('posted_vacancies', 0)} ta
⏳ <b>To'lov kutilayotgan:</b> {stats.get('pending_payments', 0)} ta
📋 <b>Hozir navbatda:</b> {stats.get('queue_count', 0)} ta

💵 <b>Jami tushum:</b> <b>{revenue_formatted} UZS</b>"""

    return text.strip()
