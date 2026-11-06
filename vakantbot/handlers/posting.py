"""E'lon berish jarayoni va to'lov handleri (avto to'lov + rasm qo'shish)."""
import json
import logging
from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from config import ADMIN_IDS, JOB_TYPES
from database import (
    create_vacancy, update_vacancy, get_vacancy,
    get_user_vacancies, log_event, get_posting_channels,
    generate_unique_payment_amount, find_vacancy_by_exact_amount,
    add_to_queue, get_queue_count, get_setting
)
from keyboards.inline import (
    channels_selection_kb, job_types_kb, confirm_vacancy_kb,
    edit_fields_kb, payment_kb, skip_kb, back_to_menu_kb,
    photo_choice_kb, admin_payment_kb
)
from handlers.states import VacancyForm
from utils.formatter import (
    format_vacancy, format_vacancy_preview,
    format_payment_info, format_admin_notification
)
from utils.subscription import check_user_subscriptions, get_subscription_keyboard
from utils.payment_parser import extract_payment_amount

logger = logging.getLogger(__name__)
router = Router()


# ==================== E'LON BERISHNI BOSHLASH ====================

@router.callback_query(F.data == "new_post")
async def start_new_post(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Yangi e'lon berish boshlanishi."""
    # Majburiy obunani tekshirish
    is_sub, missing = await check_user_subscriptions(bot, callback.from_user.id)
    if not is_sub:
        await callback.message.edit_text(
            "⚠️ E'lon berish uchun avvalo quyidagi kanallarimizga a'zo bo'ling:",
            reply_markup=get_subscription_keyboard(missing)
        )
        await callback.answer()
        return

    await state.clear()
    vacancy_id = create_vacancy(callback.from_user.id)
    await state.update_data(vacancy_id=vacancy_id, selected_channels=[])

    text = """📢 <b>Kanallarni tanlang</b>

E'loningiz qaysi kanallarga joylashtirilishini istaysiz?
Bir yoki bir nechta kanalni tanlashingiz mumkin:"""

    await state.set_state(VacancyForm.selecting_channels)
    await callback.message.edit_text(
        text.strip(),
        parse_mode="HTML",
        reply_markup=channels_selection_kb([])
    )
    await callback.answer()


@router.message(Command("post"))
async def start_new_post_cmd(message: Message, state: FSMContext, bot: Bot):
    """Komanda orqali boshlash."""
    is_sub, missing = await check_user_subscriptions(bot, message.from_user.id)
    if not is_sub:
        await message.answer(
            "⚠️ E'lon berish uchun avvalo quyidagi kanallarimizga a'zo bo'ling:",
            reply_markup=get_subscription_keyboard(missing)
        )
        return

    await state.clear()
    vacancy_id = create_vacancy(message.from_user.id)
    await state.update_data(vacancy_id=vacancy_id, selected_channels=[])

    text = """📢 <b>Kanallarni tanlang</b>

E'loningiz qaysi kanallarga joylashtirilishini istaysiz?
Bir yoki bir nechta kanalni tanlashingiz mumkin:"""

    await state.set_state(VacancyForm.selecting_channels)
    await message.answer(
        text.strip(),
        parse_mode="HTML",
        reply_markup=channels_selection_kb([])
    )


# ==================== KANAL TANLASH ====================

@router.callback_query(VacancyForm.selecting_channels, F.data.startswith("toggle_ch_"))
async def toggle_channel(callback: CallbackQuery, state: FSMContext):
    """Kanal tanlash yoki olib tashlash."""
    channel_key = callback.data.replace("toggle_ch_", "")
    data = await state.get_data()
    selected = data.get("selected_channels", [])

    if channel_key in selected:
        selected.remove(channel_key)
    else:
        selected.append(channel_key)

    await state.update_data(selected_channels=selected)
    await callback.message.edit_reply_markup(reply_markup=channels_selection_kb(selected))
    await callback.answer()


@router.callback_query(VacancyForm.selecting_channels, F.data == "channels_done")
async def channels_selected(callback: CallbackQuery, state: FSMContext):
    """Kanal tanlash yakunlandi -> narx va unikal to'lov summasi hisoblanadi."""
    data = await state.get_data()
    selected = data.get("selected_channels", [])

    if not selected:
        await callback.answer("⚠️ Kamida bitta kanal tanlashingiz shart!", show_alert=True)
        return

    channels = get_posting_channels(only_active=False)
    base_price = sum(channels[k]["price"] for k in selected if k in channels)
    exact_amount = generate_unique_payment_amount(base_price)

    update_vacancy(
        data["vacancy_id"],
        channels=json.dumps(selected),
        base_price=base_price,
        exact_amount=exact_amount,
        total_price=exact_amount
    )

    await state.set_state(VacancyForm.company_name)
    text = """🏢 <b>Kompaniya / Tashkilot nomi</b>

Kompaniya yoki brendingiz nomini kiriting:
<i>Masalan: "Artel", "Korzinka", "Smart IT Academy"</i>"""

    await callback.message.edit_text(text.strip(), parse_mode="HTML")
    await callback.answer()


# ==================== MA'LUMOTLARNI YIG'ISH ====================

@router.message(VacancyForm.company_name, F.text)
async def process_company_name(message: Message, state: FSMContext):
    data = await state.get_data()
    update_vacancy(data["vacancy_id"], company_name=message.text.strip())
    await state.update_data(company_name=message.text.strip())

    text = """💼 <b>Vakansiya / Kasb yo'nalishi</b>

Qaysi soha yoki lavozim uchun xodim izlamoqdasiz?
Quyidagilardan birini tanlang yoki o'zingiz yozib yuboring:"""

    await state.set_state(VacancyForm.job_type)
    await message.answer(text.strip(), parse_mode="HTML", reply_markup=job_types_kb())


@router.callback_query(VacancyForm.job_type, F.data.startswith("job_"))
async def process_job_type_button(callback: CallbackQuery, state: FSMContext):
    job_index = int(callback.data.replace("job_", ""))
    job_type = JOB_TYPES[job_index]

    data = await state.get_data()
    update_vacancy(data["vacancy_id"], job_type=job_type)
    await state.update_data(job_type=job_type)

    text = """👥 <b>Kerakli xodimlar soni</b>

Nechta mutaxassis qidirilmoqda?
<i>Masalan: "1 nafar", "3 kishi", "10-15 nafar"</i>"""

    await state.set_state(VacancyForm.workers_count)
    await callback.message.edit_text(text.strip(), parse_mode="HTML")
    await callback.answer()


@router.message(VacancyForm.job_type, F.text)
async def process_job_type_text(message: Message, state: FSMContext):
    data = await state.get_data()
    update_vacancy(data["vacancy_id"], job_type=message.text.strip())
    await state.update_data(job_type=message.text.strip())

    text = """👥 <b>Kerakli xodimlar soni</b>

Nechta mutaxassis qidirilmoqda?
<i>Masalan: "1 nafar", "3 kishi", "10-15 nafar"</i>"""

    await state.set_state(VacancyForm.workers_count)
    await message.answer(text.strip(), parse_mode="HTML")


@router.message(VacancyForm.workers_count, F.text)
async def process_workers_count(message: Message, state: FSMContext):
    data = await state.get_data()
    update_vacancy(data["vacancy_id"], workers_count=message.text.strip())
    await state.update_data(workers_count=message.text.strip())

    text = """💰 <b>Oylik maosh</b>

Ish haqi miqdorini kiriting:
<i>Masalan: "4 000 000 - 6 000 000 so'm", "$600+", "Suhbat asosida"</i>"""

    await state.set_state(VacancyForm.salary)
    await message.answer(text.strip(), parse_mode="HTML")


@router.message(VacancyForm.salary, F.text)
async def process_salary(message: Message, state: FSMContext):
    data = await state.get_data()
    update_vacancy(data["vacancy_id"], salary=message.text.strip())
    await state.update_data(salary=message.text.strip())

    text = """⏰ <b>Ish vaqti va tartibi</b>

Ish grafigini ko'rsating:
<i>Masalan: "09:00 - 18:00 (5/2)", "Smenali grafik", "Erkin grafik"</i>"""

    await state.set_state(VacancyForm.work_schedule)
    await message.answer(text.strip(), parse_mode="HTML")


@router.message(VacancyForm.work_schedule, F.text)
async def process_work_schedule(message: Message, state: FSMContext):
    data = await state.get_data()
    update_vacancy(data["vacancy_id"], work_schedule=message.text.strip())
    await state.update_data(work_schedule=message.text.strip())

    text = """📍 <b>Ish joyi manzili</b>

Mo'ljal yoki aniq manzilni yozing:
<i>Masalan: "Toshkent sh., Yunusobod tumani", "Samarqand sh."</i>"""

    await state.set_state(VacancyForm.address)
    await message.answer(text.strip(), parse_mode="HTML")


@router.message(VacancyForm.address, F.text)
async def process_address(message: Message, state: FSMContext):
    data = await state.get_data()
    update_vacancy(data["vacancy_id"], address=message.text.strip())
    await state.update_data(address=message.text.strip())

    text = """📞 <b>Aloqa uchun telefon raqami</b>

Murojaat uchun raqam va bog'lanish usulini kiriting:
<i>Masalan: "+998 90 123 45 67 (Telegram bor)"</i>"""

    await state.set_state(VacancyForm.phone)
    await message.answer(text.strip(), parse_mode="HTML")


@router.message(VacancyForm.phone, F.text)
async def process_phone(message: Message, state: FSMContext):
    data = await state.get_data()
    update_vacancy(data["vacancy_id"], phone=message.text.strip())
    await state.update_data(phone=message.text.strip())

    text = """📋 <b>Nomzodga qo'yiladigan talablar</b>

Kerakli talablarni yozing:
<i>Masalan:
- Kamida 1 yil tajriba
- Rus tilida erkin so'zlasha olish
- Mas'uliyatli va intizomli</i>

Talablar bo'lmasa o'tkazib yuboring 👇"""

    await state.set_state(VacancyForm.requirements)
    await message.answer(text.strip(), parse_mode="HTML", reply_markup=skip_kb("requirements"))


@router.callback_query(VacancyForm.requirements, F.data == "skip_requirements")
async def skip_requirements(callback: CallbackQuery, state: FSMContext):
    await ask_additional_info(callback.message, state, is_edit=True)
    await callback.answer()


@router.message(VacancyForm.requirements, F.text)
async def process_requirements(message: Message, state: FSMContext):
    data = await state.get_data()
    update_vacancy(data["vacancy_id"], requirements=message.text.strip())
    await state.update_data(requirements=message.text.strip())
    await ask_additional_info(message, state)


async def ask_additional_info(message, state: FSMContext, is_edit: bool = False):
    text = """ℹ️ <b>Qo'shimcha ma'lumotlar / Qulayliklar</b>

Qo'shimcha imtiyozlar bo'lsa kiriting:
<i>Masalan: "Tushlik va yo'l haqi beriladi", "Yotoqxona mavjud"</i>

Bo'lmasa o'tkazib yuborishingiz mumkin 👇"""

    await state.set_state(VacancyForm.additional_info)
    if is_edit:
        await message.edit_text(text.strip(), parse_mode="HTML", reply_markup=skip_kb("additional"))
    else:
        await message.answer(text.strip(), parse_mode="HTML", reply_markup=skip_kb("additional"))


@router.callback_query(VacancyForm.additional_info, F.data == "skip_additional")
async def skip_additional(callback: CallbackQuery, state: FSMContext):
    await ask_photo_choice(callback.message, state, is_edit=True)
    await callback.answer()


@router.message(VacancyForm.additional_info, F.text)
async def process_additional_info(message: Message, state: FSMContext):
    data = await state.get_data()
    update_vacancy(data["vacancy_id"], additional_info=message.text.strip())
    await state.update_data(additional_info=message.text.strip())
    await ask_photo_choice(message, state)


# ==================== RASM VA BANNER TANLOVI ====================

async def ask_photo_choice(message, state: FSMContext, is_edit: bool = False):
    """Foydalanuvchidan rasm turini so'rash."""
    text = """🖼 <b>E'lon uchun rasm / reklama banneri</b>

E'loningiz qanday ko'rinishda bo'lishini xohlaysiz?

1️⃣ <b>O'z rasmimni yuklayman</b> — kompaniyangiz yoki reklamangiz tayyor rasmini yuborasiz.
2️⃣ <b>Umumiy banner qo'yilsin</b> — kanalimizning professional umumiy rasmi qo'yiladi.
3️⃣ <b>Faqat matn</b> — rasmsiz e'lon joylanadi.

👇 Tanlang:"""

    await state.set_state(VacancyForm.photo_choice)
    if is_edit:
        await message.edit_text(text.strip(), parse_mode="HTML", reply_markup=photo_choice_kb())
    else:
        await message.answer(text.strip(), parse_mode="HTML", reply_markup=photo_choice_kb())


@router.callback_query(VacancyForm.photo_choice, F.data == "photo_upload_custom")
async def handle_photo_custom(callback: CallbackQuery, state: FSMContext):
    """O'z rasmini yuklashni tanlaganda."""
    await state.set_state(VacancyForm.waiting_custom_photo)
    text = "📸 <b>Iltimos, e'lon uchun rasmni (banner) yuboring:</b>"
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=skip_kb("custom_photo"))
    await callback.answer()


@router.message(VacancyForm.waiting_custom_photo, F.photo)
async def process_custom_photo(message: Message, state: FSMContext):
    """Foydalanuvchi yuborgan rasmni qabul qilish."""
    photo = message.photo[-1]
    data = await state.get_data()
    update_vacancy(
        data["vacancy_id"],
        photo_file_id=photo.file_id,
        use_default_photo=0
    )
    await show_preview(message, state)


@router.callback_query(VacancyForm.waiting_custom_photo, F.data == "skip_custom_photo")
async def skip_custom_photo(callback: CallbackQuery, state: FSMContext):
    """Rasmni o'tkazib yuborish."""
    data = await state.get_data()
    update_vacancy(data["vacancy_id"], photo_file_id=None, use_default_photo=0)
    await show_preview(callback.message, state, is_edit=True)
    await callback.answer()


@router.callback_query(VacancyForm.photo_choice, F.data == "photo_use_default")
async def handle_photo_default(callback: CallbackQuery, state: FSMContext):
    """Umumiy bannerni tanlaganda."""
    data = await state.get_data()
    update_vacancy(data["vacancy_id"], photo_file_id=None, use_default_photo=1)
    await show_preview(callback.message, state, is_edit=True)
    await callback.answer()


@router.callback_query(VacancyForm.photo_choice, F.data == "photo_skip")
async def handle_photo_skip(callback: CallbackQuery, state: FSMContext):
    """Faqat matnni tanlaganda."""
    data = await state.get_data()
    update_vacancy(data["vacancy_id"], photo_file_id=None, use_default_photo=0)
    await show_preview(callback.message, state, is_edit=True)
    await callback.answer()


# ==================== PREVIEW VA TASDIQLASH ====================

async def show_preview(message, state: FSMContext, is_edit: bool = False):
    """E'lon ko'rinishini ko'rsatish."""
    data = await state.get_data()
    vacancy = get_vacancy(data["vacancy_id"])
    if not vacancy:
        await message.answer("❌ Xatolik yuz berdi. Iltimos, /start buyrug'ini bering.", reply_markup=back_to_menu_kb())
        await state.clear()
        return

    selected_channels = json.loads(vacancy["channels"]) if isinstance(vacancy["channels"], str) else vacancy.get("channels", [])
    formatted_text = format_vacancy(vacancy)
    update_vacancy(vacancy["id"], formatted_text=formatted_text)

    preview_text = format_vacancy_preview(vacancy, selected_channels)
    await state.set_state(VacancyForm.preview)

    photo_id = vacancy.get("photo_file_id")
    default_banner = get_setting("default_banner_file_id", "")
    banner_to_show = photo_id or (default_banner if vacancy.get("use_default_photo") else None)

    # Agar rasm bo'lsa send_photo bilan ko'rsatamiz
    if banner_to_show:
        try:
            await message.answer_photo(
                photo=banner_to_show,
                caption=preview_text,
                parse_mode="HTML",
                reply_markup=confirm_vacancy_kb()
            )
            return
        except Exception:
            pass

    if is_edit:
        await message.edit_text(preview_text, parse_mode="HTML", reply_markup=confirm_vacancy_kb())
    else:
        await message.answer(preview_text, parse_mode="HTML", reply_markup=confirm_vacancy_kb())


@router.callback_query(VacancyForm.preview, F.data == "confirm_vacancy")
async def confirm_vacancy(callback: CallbackQuery, state: FSMContext):
    """E'lonni tasdiqlab, to'lov sahifasiga o'tish."""
    data = await state.get_data()
    vacancy = get_vacancy(data["vacancy_id"])

    if not vacancy:
        await callback.message.edit_text("❌ Xatolik!", reply_markup=back_to_menu_kb())
        await state.clear()
        await callback.answer()
        return

    # Holatni to'lov kutilmoqda rejimiga o'tkazish
    update_vacancy(vacancy["id"], status="pending_payment")

    exact_amount = vacancy.get("exact_amount") or vacancy.get("total_price") or 0
    payment_text = format_payment_info(exact_amount, vacancy["id"])

    await state.set_state(VacancyForm.waiting_payment)

    # Agar xabar fotosurat bilan bo'lsa, edit_caption qilamiz
    if callback.message.photo:
        await callback.message.edit_caption(
            caption=payment_text,
            parse_mode="HTML",
            reply_markup=payment_kb(vacancy["id"])
        )
    else:
        await callback.message.edit_text(
            payment_text,
            parse_mode="HTML",
            reply_markup=payment_kb(vacancy["id"])
        )
    await callback.answer()


# ==================== TAHRIRLASH ====================

@router.callback_query(VacancyForm.preview, F.data == "edit_vacancy")
async def edit_vacancy_menu(callback: CallbackQuery, state: FSMContext):
    text = "✏️ <b>Qaysi ma'lumotni o'zgartirishni xohlaysiz?</b>\n\nTanlang 👇"
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text, parse_mode="HTML", reply_markup=edit_fields_kb())
    else:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=edit_fields_kb())
    await callback.answer()


@router.callback_query(F.data == "back_to_preview")
async def back_to_preview_handler(callback: CallbackQuery, state: FSMContext):
    await show_preview(callback.message, state, is_edit=False)
    await callback.answer()


EDIT_MAP = {
    "edit_company": ("company_name", "🏢 Kompaniya nomini yangilang:"),
    "edit_job_type": ("job_type", "💼 Vakansiya turini yangilang:"),
    "edit_workers": ("workers_count", "👥 Kerakli xodimlar sonini yangilang:"),
    "edit_salary": ("salary", "💰 Oylik maoshni yangilang:"),
    "edit_schedule": ("work_schedule", "⏰ Ish vaqtini yangilang:"),
    "edit_address": ("address", "📍 Manzilni yangilang:"),
    "edit_phone": ("phone", "📞 Telefon raqamini yangilang:"),
    "edit_requirements": ("requirements", "📋 Talablarni yangilang:"),
    "edit_additional": ("additional_info", "ℹ️ Qo'shimcha ma'lumotni yangilang:"),
}


@router.callback_query(F.data.in_(EDIT_MAP.keys()))
async def edit_field_start(callback: CallbackQuery, state: FSMContext):
    field_name, prompt = EDIT_MAP[callback.data]
    await state.update_data(editing_field_name=field_name)
    await state.set_state(VacancyForm.editing_field)
    await callback.message.edit_text(prompt, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "edit_photo")
async def edit_photo_start(callback: CallbackQuery, state: FSMContext):
    await ask_photo_choice(callback.message, state, is_edit=True)
    await callback.answer()


@router.message(VacancyForm.editing_field, F.text)
async def process_edit_field(message: Message, state: FSMContext):
    data = await state.get_data()
    field_name = data.get("editing_field_name")
    vacancy_id = data.get("vacancy_id")
    if field_name and vacancy_id:
        update_vacancy(vacancy_id, **{field_name: message.text.strip()})
    await show_preview(message, state)


# ==================== TO'LOV VA AVTO TEKSHIRUV ====================

@router.callback_query(F.data.startswith("check_payment_"))
async def check_payment_callback(callback: CallbackQuery, bot: Bot):
    """Foydalanuvchi '⚡️ To'lovni tekshirish' tugmasini bosganda."""
    vacancy_id = int(callback.data.replace("check_payment_", ""))
    vacancy = get_vacancy(vacancy_id)

    if not vacancy:
        await callback.answer("❌ E'lon topilmadi!", show_alert=True)
        return

    # Agar allaqachon tasdiqlangan bo'lsa
    if vacancy["status"] in ["queued", "posted"]:
        await callback.message.edit_text(
            f"🎉 <b>To'lov tasdiqlangan!</b>\n\nE'loningiz <code>#{vacancy_id}</code> navbatga qo'yilgan va tez orada kanalga joylanadi.",
            parse_mode="HTML",
            reply_markup=back_to_menu_kb()
        )
        await callback.answer("✅ To'lov allaqachon tasdiqlangan!")
        return

    exact_amount = vacancy.get("exact_amount", 0)
    await callback.answer(
        f"⏳ To'lov tekshirilmoqda... Agar aynan {exact_amount} so'm o'tkazgan bo'lsangiz, bir necha daqiqa kuting yoki chek screenshotini yuboring.",
        show_alert=True
    )


@router.callback_query(F.data.startswith("send_receipt_"))
async def send_receipt_start(callback: CallbackQuery, state: FSMContext):
    """Chek screenshotini yuborish rejimiga o'tish."""
    vacancy_id = int(callback.data.replace("send_receipt_", ""))
    await state.update_data(vacancy_id=vacancy_id)
    await state.set_state(VacancyForm.sending_receipt)

    text = "📸 <b>Iltimos, to'lov cheki screenshotini (rasmini) yuboring:</b>"
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text, parse_mode="HTML")
    else:
        await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


@router.message(VacancyForm.sending_receipt, F.photo)
async def process_receipt_photo(message: Message, state: FSMContext, bot: Bot):
    """Foydalanuvchi chek rasmini yuborganda."""
    data = await state.get_data()
    vacancy_id = data.get("vacancy_id")
    vacancy = get_vacancy(vacancy_id)

    if not vacancy:
        await message.answer("❌ E'lon topilmadi!", reply_markup=back_to_menu_kb())
        await state.clear()
        return

    photo = message.photo[-1]
    update_vacancy(
        vacancy_id,
        payment_screenshot_file_id=photo.file_id,
        status="payment_sent"
    )

    await message.answer(
        f"✅ <b>To'lov cheki qabul qilindi!</b>\n\n"
        f"📌 E'lon raqami: <code>#{vacancy_id}</code>\n"
        f"💰 Kutilgan unikal summa: <b>{vacancy.get('exact_amount', 0)} UZS</b>\n\n"
        f"⏳ To'lov avtomatik yoki admin tomonidan tekshirilib, tasdiqlangach e'loningiz kanalga chiqariladi.",
        parse_mode="HTML",
        reply_markup=back_to_menu_kb()
    )

    # Adminlarga yuborish
    user_info = {
        "full_name": message.from_user.full_name,
        "username": message.from_user.username
    }
    admin_text = format_admin_notification(vacancy, user_info)

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_photo(
                chat_id=admin_id,
                photo=photo.file_id,
                caption=admin_text,
                parse_mode="HTML",
                reply_markup=admin_payment_kb(vacancy_id)
            )
        except Exception as e:
            logger.error(f"Admin {admin_id} ga chek yuborishda xatolik: {e}")

    log_event("payment_sent", message.from_user.id, vacancy_id)
    await state.clear()


# ==================== @humocardbot VA TO'LOV BILDIRIShNOMALARI (AVTO USHLASH) ====================

@router.message(F.text | F.caption)
async def handle_auto_payment_text(message: Message, bot: Bot):
    """
    @humocardbot dan forward qilingan xabarlar yoki SMS matnlarini avtomatik tahlil qilish.
    Agar xabarda aniq summa (masalan, 1003 yoki 50003) topilsa, o'sha vakansiyani 100% AVTO tasdiqlaydi!
    """
    raw_text = message.text or message.caption or ""
    amount = extract_payment_amount(raw_text)
    if not amount:
        return

    vacancy = find_vacancy_by_exact_amount(amount)
    if not vacancy:
        # Bunday summali kutilayotgan vakansiya yo'q
        return

    vacancy_id = vacancy["id"]

    # Avtomatik tasdiqlash!
    update_vacancy(
        vacancy_id,
        status="queued",
        payment_confirmed_at=datetime.now().isoformat(),
        payment_note=f"AVTO TO'LOV (@humocardbot/SMS): {amount} UZS"
    )

    channels = json.loads(vacancy["channels"]) if isinstance(vacancy["channels"], str) else vacancy.get("channels", [])
    for ch_key in channels:
        add_to_queue(vacancy_id, ch_key)

    queue_count = get_queue_count()

    # Foydalanuvchiga bir zumda xabar
    try:
        await bot.send_message(
            chat_id=vacancy["user_id"],
            text=f"⚡️ <b>TO'LOV AVTOMATIK TASDIQLANDI!</b>\n\n"
                 f"📌 E'lon raqami: <code>#{vacancy_id}</code>\n"
                 f"💰 Qabul qilingan summa: <b>{amount:,} UZS</b>\n"
                 f"📋 E'loningiz muvaffaqiyatli navbatga qo'yildi (Hozir navbatda: {queue_count} ta)!\n\n"
                 f"🚀 Belgilangan vaqt oralig'ida kanallarga avtomatik chiqariladi.",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Foydalanuvchiga avto to'lov xabarini yetkazishda xatolik: {e}")

    # Adminlarga bildirishnoma
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=f"🟢 <b>AVTO TO'LOV TASDIQLANDI!</b>\n\n"
                     f"📌 E'lon: <code>#{vacancy_id}</code>\n"
                     f"👤 User: <code>{vacancy['user_id']}</code>\n"
                     f"💰 Summa: <b>{amount:,} UZS</b>\n"
                     f"🏢 Kompaniya: {vacancy.get('company_name', '—')}\n"
                     f"📋 Navbatga qo'yildi.",
                parse_mode="HTML"
            )
        except Exception:
            pass

    log_event("auto_payment_success", vacancy["user_id"], vacancy_id, {"amount": amount})
    await message.reply(f"✅ <b>To'lov avtomatik aniqlandi va tasdiqlandi!</b> (E'lon #{vacancy_id})", parse_mode="HTML")


# ==================== MENING E'LONLARIM ====================

@router.callback_query(F.data == "my_posts")
async def my_posts(callback: CallbackQuery):
    vacancies = get_user_vacancies(callback.from_user.id)
    if not vacancies:
        await callback.message.edit_text(
            "📋 Sizda hali e'lonlar mavjud emas.\n\n✨ Yangi e'lon berish uchun tugmani bosing:",
            reply_markup=back_to_menu_kb()
        )
        await callback.answer()
        return

    STATUS_MAP = {
        "draft": "📝 Qoralama",
        "pending_payment": "💳 To'lov kutilmoqda",
        "payment_sent": "⏳ Tekshirilmoqda",
        "queued": "📋 Navbatda",
        "posted": "✅ Joylashtirildi",
        "cancelled": "❌ Bekor qilingan",
        "rejected": "🚫 Rad etilgan",
    }

    text = "📋 <b>Sizning e'lonlaringiz:</b>\n\n"
    for v in vacancies[:10]:
        st = STATUS_MAP.get(v["status"], v["status"])
        amt = v.get("exact_amount") or v.get("total_price") or 0
        text += f"📌 <code>#{v['id']}</code> — <b>{v.get('company_name', 'Nomsiz')}</b>\n   Holati: {st} ({amt:,} UZS)\n\n"

    text += "🏠 Bosh menyuga qaytish uchun tugmani bosing:"
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=back_to_menu_kb())
    await callback.answer()
