"""Vakansiya e'lonini haqiqiy Telegram Premium Custom Emojilar bilan formatlash."""
import json
from database import get_setting, get_posting_channels
from config_emojis import CUSTOM_EMOJI_IDS


def em(key: str, fallback: str) -> str:
    """Telegram Premium Custom Emoji HTML tegi."""
    eid = CUSTOM_EMOJI_IDS.get(key, "").strip()
    if eid:
        return f'<tg-emoji emoji-id="{eid}">{fallback}</tg-emoji>'
    return fallback


def format_vacancy(data: dict) -> str:
    """Vakansiya e'lonini hashamatli formatda tayyorlash."""

    # Agar foydalanuvchi tayyor reklama yuborgan bo'lsa
    if data.get("company_name") == "Tayyor reklama" and data.get("formatted_text"):
        return data["formatted_text"]

    company = data.get('company_name', '—')
    job_type = data.get('job_type', '—')
    workers = data.get('workers_count', '—')
    salary = data.get('salary', '—')
    schedule = data.get('work_schedule', '—')
    address = data.get('address', '—')
    phone = data.get('phone', '—')
    requirements = data.get('requirements')
    additional_info = data.get('additional_info')

    text = f"""{em('menu_new_post', '✨')} <b>ISh O'RNI: {job_type.upper()}</b>

{em('menu_channels', '🏢')} <b>Kompaniya:</b> <code>{company}</code>
{em('mode_wizard', '💼')} <b>Vakansiya:</b> {job_type}
👥 <b>Kerakli xodimlar:</b> {workers}
{em('menu_prices', '💰')} <b>Oylik maosh:</b> <b>{salary}</b>
{em('admin_queue', '⏳')} <b>Ish tartibi:</b> {schedule}
📍 <b>Manzil:</b> {address}
{em('menu_contact', '📞')} <b>Bog'lanish:</b> <code>{phone}</code>"""

    if requirements:
        text += f"""\n\n{em('mode_wizard', '📝')} <b>Talablar:</b>\n{requirements}"""

    if additional_info:
        text += f"""\n\n{em('menu_channels', '📌')} <b>Qo'shimcha ma'lumot:</b>\n{additional_info}"""

    text += f"""\n\n━━━━━━━━━━━━━━━━━━━━━━\n{em('action_post_now', '🚀')} <i>Murojaat uchun yuqoridagi raqamga qo'ng'iroq qiling yoki yozing!</i>"""

    return text.strip()


def format_vacancy_for_channel(data: dict) -> str:
    return format_vacancy(data)


def format_vacancy_preview(data: dict, selected_channels: list) -> str:
    vacancy_text = format_vacancy(data)
    channels_dict = get_posting_channels(only_active=False)

    channels_info = ""
    for key in selected_channels:
        if key in channels_dict:
            ch = channels_dict[key]
            price_formatted = f"{ch['price']:,}".replace(",", " ")
            channels_info += f"  {em('menu_channels', '📢')} <b>{ch['name']}</b> — {price_formatted} UZS\n"

    exact_amount = data.get("exact_amount") or data.get("total_price") or 0
    exact_formatted = f"{exact_amount:,}".replace(",", " ")

    photo_status = f"{em('photo_custom', '📸')} O'z rasmingiz biriktirilgan" if data.get("photo_file_id") else (
        f"{em('photo_default', '🖼')} Umumiy kanal banneri qo'yiladi" if data.get("use_default_photo") else f"{em('photo_skip', '📄')} Faqat matnli e'lon"
    )

    text = f"""👁 <b>E'LON KO'RINIShI (PREVIEW):</b>

{vacancy_text}

━━━━━━━━━━━━━━━━━━━━━━
{photo_status}

{em('menu_channels', '📢')} <b>Tanlangan kanallar:</b>
{channels_info if channels_info else '  <i>(Hech qanday kanal tanlanmagan)</i>'}
{em('admin_pending', '💳')} <b>To'lov summasi:</b> <b>{exact_formatted} UZS</b>

{em('action_confirm', '✅')} <i>Hammasi to'g'ri bo'lsa, tasdiqlang yoki tahrirlang:</i>"""

    return text.strip()


def format_payment_info(exact_amount: int, vacancy_id: int) -> str:
    card = get_setting("payment_card", "8600 0000 0000 0000")
    holder = get_setting("payment_holder", "ADMIN")
    exact_formatted = f"{exact_amount:,}".replace(",", " ")

    text = f"""{em('admin_pending', '💳')} <b>TO'LOV VA AVTOMATIK TEKSHIRUV</b>

📌 E'lon raqami: <code>#{vacancy_id}</code>

{em('action_check_pay', '⚡️')} <b>O'TKAZISHINGIZ KERAK BO'LGAN ANIQ SUMMA:</b>
👉 <b><code>{exact_amount}</code></b> so'm (<code>{exact_formatted} UZS</code>)

⚠️ <b>DIQQAT! TO'LOV AVTO TASDIQLANISHI UCHUN:</b>
Aynan <b><code>{exact_amount}</code> so'm</b> o'tkazishingiz shart! 
<i>(Tizim ushbu unikal summa orqali to'lovingizni 100% avtomatik aniqlaydi!)</i>

━━━━━━━━━━━━━━━━━━━━━━
{em('admin_pending', '💳')} <b>Karta raqami:</b>
<code>{card}</code>

👤 <b>Qabul qiluvchi:</b> {holder}
━━━━━━━━━━━━━━━━━━━━━━

🤖 <b>AVTO TEKSHIRUV:</b>
1. Pulni o'tkazing (Click, Payme, Uzum va h.k.).
2. Pul tushgach, @humocardbot dan kelgan SMS/chek matnini shu yerga yuboring yoki pastdagi <b>«⚡️ To'lovni tekshirish»</b> tugmasini bosing!
3. To'lov <b>AVTOMATIK</b> tasdiqlanadi va e'lon navbatga qo'yiladi!"""

    return text.strip()


def format_admin_notification(vacancy: dict, user_info: dict) -> str:
    channels_dict = get_posting_channels(only_active=False)
    channels_text = ""
    ch_keys = json.loads(vacancy["channels"]) if isinstance(vacancy["channels"], str) else vacancy.get("channels", [])
    for key in ch_keys:
        if key in channels_dict:
            channels_text += f"  {em('menu_channels', '📢')} {channels_dict[key]['name']}\n"

    exact_amount = vacancy.get('exact_amount', vacancy.get('total_price', 0))
    price_formatted = f"{exact_amount:,}".replace(",", " ")

    text = f"""{em('admin_broadcast', '🔔')} <b>YANGI TO'LOV CHEKI / HARAKATI!</b>

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
    revenue_formatted = f"{stats.get('total_revenue', 0):,}".replace(",", " ")

    text = f"""{em('admin_stats', '📊')} <b>BOTNING MUKAMMAL STATISTIKASI</b>

👥 <b>Jami foydalanuvchilar:</b> {stats.get('total_users', 0)} ta
📢 <b>Faol majburiy kanallar:</b> {stats.get('mandatory_channels_count', 0)} ta
📝 <b>Jami arizalar/e'lonlar:</b> {stats.get('total_vacancies', 0)} ta
✅ <b>Kanalga joylangan:</b> {stats.get('posted_vacancies', 0)} ta
⏳ <b>To'lov kutilayotgan:</b> {stats.get('pending_payments', 0)} ta
📋 <b>Hozir navbatda:</b> {stats.get('queue_count', 0)} ta

💵 <b>Jami tushum:</b> <b>{revenue_formatted} UZS</b>"""

    return text.strip()
