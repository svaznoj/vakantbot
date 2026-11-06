"""Mukammal Admin Panel handleri."""
import json
import logging
from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from config import ADMIN_IDS
from database import (
    get_vacancy, update_vacancy, get_pending_payments,
    get_stats_summary, add_to_queue, get_queue_count,
    log_event, get_all_vacancies_by_status, get_all_users,
    add_mandatory_channel, remove_mandatory_channel, get_all_mandatory_channels,
    add_or_update_posting_channel, remove_posting_channel, get_posting_channels,
    get_setting, set_setting
)
from keyboards.inline import (
    admin_menu_kb, admin_mandatory_channels_kb, admin_posting_channels_kb,
    admin_banner_kb, back_to_menu_kb
)
from handlers.states import AdminStates
from utils.formatter import format_stats
from utils.scheduler import PostScheduler

logger = logging.getLogger(__name__)
router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ==================== ASOSIY ADMIN PANEL ====================

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Sizda admin huquqi mavjud emas.")
        return

    await state.clear()
    await message.answer(
        "🔐 <b>MUKAMMAL ADMIN PANEL</b>\n\nBarcha sozlamalar va operatsiyalarni quyidagi menyu orqali boshqaring:",
        parse_mode="HTML",
        reply_markup=admin_menu_kb()
    )


@router.callback_query(F.data == "admin_main")
async def callback_admin_main(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
        return

    await state.clear()
    await callback.message.edit_text(
        "🔐 <b>MUKAMMAL ADMIN PANEL</b>\n\nBo'limni tanlang:",
        parse_mode="HTML",
        reply_markup=admin_menu_kb()
    )
    await callback.answer()


# ==================== MAJBURIY OBUNA KANALLARI BOSHQARUVI ====================

@router.callback_query(F.data == "admin_mandatory_channels")
async def admin_mandatory_channels_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    text = """📢 <b>MAJBURIY OBUNA KANALLARI</b>

Foydalanuvchi botdan foydalanishi uchun ushbu kanallarning barchasiga a'zo bo'lishi shart qilinadi.
<i>(Bot ushbu kanallarda administrator bo'lishi lozim)</i>"""

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=admin_mandatory_channels_kb())
    await callback.answer()


@router.callback_query(F.data == "adm_mch_add")
async def admin_mch_add_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(AdminStates.adding_mandatory_channel)
    text = """➕ <b>Yangi majburiy kanal qo'shish</b>

Iltimos, kanal ma'lumotlarini quyidagi ko'rinishda yuboring:
<code>Kanal_ID | Kanal_Nomi | @username_yoki_havola</code>

<i>Misollar:</i>
<code>-1001234567890 | Ish Bor Toshkent | @ishbor_toshkent</code>
<code>-1009876543210 | Kun yangiliklari | https://t.me/+AbCdEfGh</code>

⚠️ <i>Eslatma: Botni ushbu kanalga admin qilib qo'shishni unutmang!</i>"""

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="admin_mandatory_channels")]
    ])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.message(AdminStates.adding_mandatory_channel, F.text)
async def admin_mch_add_finish(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return

    parts = [p.strip() for p in message.text.split("|")]
    if len(parts) < 2:
        await message.answer("⚠️ Format noto'g'ri! Misol: <code>-1001234567890 | Nom | @username</code>")
        return

    try:
        channel_id = int(parts[0])
    except ValueError:
        await message.answer("❌ Kanal ID manfiy butun son bo'lishi kerak (masalan: <code>-1001234567890</code>)!")
        return

    title = parts[1]
    link_or_user = parts[2] if len(parts) > 2 else ""
    username = link_or_user if link_or_user.startswith("@") else None
    invite_link = link_or_user if link_or_user.startswith("http") else None

    # Kanalga kirib ko'rish
    try:
        chat = await bot.get_chat(channel_id)
        if chat.title:
            title = chat.title
        if chat.username:
            username = f"@{chat.username}"
    except Exception as e:
        logger.warning(f"Kanal ma'lumotini olishda ogohlantirish: {e}")

    add_mandatory_channel(channel_id, title, username, invite_link)
    await state.clear()
    await message.answer(
        f"✅ <b>Kanal muvaffaqiyatli qo'shildi!</b>\n\n📌 <b>{title}</b> (<code>{channel_id}</code>)",
        parse_mode="HTML",
        reply_markup=admin_mandatory_channels_kb()
    )


@router.callback_query(F.data.startswith("adm_mch_del_"))
async def admin_mch_delete(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    channel_id = int(callback.data.replace("adm_mch_del_", ""))
    remove_mandatory_channel(channel_id)
    await callback.answer("✅ Kanal majburiy obunadan olib tashlandi!", show_alert=True)
    await callback.message.edit_reply_markup(reply_markup=admin_mandatory_channels_kb())


# ==================== E'LON KANALLARI VA NARXLAR ====================

@router.callback_query(F.data == "admin_posting_channels")
async def admin_posting_channels_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    text = """💼 <b>E'LON CHIQARILADIGAN KANALLAR VA NARXLAR</b>

Foydalanuvchilar e'lon berayotganda ushbu ro'yxatdan kerakli kanallarni tanlaydilar."""
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=admin_posting_channels_kb())
    await callback.answer()


@router.callback_query(F.data == "adm_pch_add")
async def admin_pch_add_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(AdminStates.adding_pch_name)
    text = """➕ <b>Yangi e'lon kanali qo'shish</b>

Iltimos, ma'lumotlarni quyidagi tartibda bitta xabarda yuboring:
<code>Kanal_Kaliti | Kanal_Nomi | Chat_ID | Narxi | @username</code>

<i>Misol:</i>
<code>channel_it | IT Vakansiyalar | -1001234567890 | 75000 | @it_vakansiya</code>"""

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="admin_posting_channels")]
    ])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.message(AdminStates.adding_pch_name, F.text)
async def admin_pch_add_finish(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    parts = [p.strip() for p in message.text.split("|")]
    if len(parts) < 4:
        await message.answer("⚠️ Ma'lumotlar to'liq emas! Misol: <code>it_ch | IT Ish | -1001234567 | 50000 | @username</code>")
        return

    key = parts[0]
    name = parts[1]
    try:
        chat_id = int(parts[2])
        price = int(parts[3].replace(" ", ""))
    except ValueError:
        await message.answer("❌ Chat_ID va Narx to'g'ri son bo'lishi kerak!")
        return

    username = parts[4] if len(parts) > 4 else ""

    add_or_update_posting_channel(key, name, chat_id, price, username)
    await state.clear()
    await message.answer(
        f"✅ <b>E'lon kanali qo'shildi:</b>\n\n📢 {name} — {price:,} UZS",
        parse_mode="HTML",
        reply_markup=admin_posting_channels_kb()
    )


@router.callback_query(F.data.startswith("adm_pch_del_"))
async def admin_pch_delete(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    key = callback.data.replace("adm_pch_del_", "")
    remove_posting_channel(key)
    await callback.answer("✅ Kanal o'chirildi!", show_alert=True)
    await callback.message.edit_reply_markup(reply_markup=admin_posting_channels_kb())


# ==================== BANNER SOZLAMALARI ====================

@router.callback_query(F.data == "admin_banner_settings")
async def admin_banner_settings_menu(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    current = get_setting("default_banner_file_id", "")
    status_text = "Mavjud ✅" if current else "O'rnatilmagan (bo'sh) ❌"

    text = f"""🖼 <b>UMUMIY E'LON BANNERI SOZLAMALARI</b>

Agar e'lon beruvchi o'z rasmini yuklamasa va "Umumiy banner"ni tanlasa, ushbu rasm e'longa biriktirilib kanalga chiqariladi.

Hozirgi holat: <b>{status_text}</b>"""

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=admin_banner_kb())
    await callback.answer()


@router.callback_query(F.data == "adm_banner_view")
async def admin_banner_view(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    current = get_setting("default_banner_file_id", "")
    if current:
        await callback.message.answer_photo(photo=current, caption="🖼 <b>Hozirgi faol umumiy banner</b>", parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "adm_banner_remove")
async def admin_banner_remove(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    set_setting("default_banner_file_id", "")
    await callback.answer("🗑 Umumiy banner o'chirildi!", show_alert=True)
    await callback.message.edit_reply_markup(reply_markup=admin_banner_kb())


@router.callback_query(F.data == "adm_banner_set")
async def admin_banner_set_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(AdminStates.uploading_banner)
    text = "📤 <b>Yangi umumiy banner rasmini yuboring:</b>"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="admin_banner_settings")]
    ])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.message(AdminStates.uploading_banner, F.photo)
async def admin_banner_set_finish(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    photo = message.photo[-1]
    set_setting("default_banner_file_id", photo.file_id)
    await state.clear()
    await message.answer("✅ <b>Yangi umumiy banner muvaffaqiyatli saqlandi!</b>", parse_mode="HTML", reply_markup=admin_banner_kb())


# ==================== KARTA SOZLAMALARI ====================

@router.callback_query(F.data == "admin_card_settings")
async def admin_card_settings(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    card = get_setting("payment_card", "8600 0000 0000 0000")
    holder = get_setting("payment_holder", "ADMIN")

    text = f"""💳 <b>TO'LOV KARTASI SOZLAMALARI</b>

Hozirgi karta raqami: <code>{card}</code>
Karta egasi: <b>{holder}</b>

O'zgartirish uchun kerakli tugmani bosing:"""

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Karta raqamini o'zgartirish", callback_data="adm_card_edit_num")],
        [InlineKeyboardButton(text="✏️ Karta egasini o'zgartirish", callback_data="adm_card_edit_name")],
        [InlineKeyboardButton(text="⬅️ Admin panelga qaytish", callback_data="admin_main")]
    ])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "adm_card_edit_num")
async def adm_card_edit_num(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.editing_card_number)
    await callback.message.edit_text("💳 Yangi karta raqamini kiriting:\n<i>Masalan: 8600 1234 5678 9012</i>", parse_mode="HTML")
    await callback.answer()


@router.message(AdminStates.editing_card_number, F.text)
async def adm_card_save_num(message: Message, state: FSMContext):
    set_setting("payment_card", message.text.strip())
    await state.clear()
    await message.answer("✅ Karta raqami muvaffaqiyatli yangilandi!", reply_markup=admin_menu_kb())


@router.callback_query(F.data == "adm_card_edit_name")
async def adm_card_edit_name(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.editing_card_holder)
    await callback.message.edit_text("👤 Yangi karta egasi ism-familiyasini kiriting:", parse_mode="HTML")
    await callback.answer()


@router.message(AdminStates.editing_card_holder, F.text)
async def adm_card_save_name(message: Message, state: FSMContext):
    set_setting("payment_holder", message.text.strip())
    await state.clear()
    await message.answer("✅ Karta egasi muvaffaqiyatli yangilandi!", reply_markup=admin_menu_kb())


# ==================== TO'LOVNI TASDIQLASH VA RAD ETISH ====================

@router.callback_query(F.data.startswith("admin_approve_and_post_"))
async def admin_approve_and_post_now(callback: CallbackQuery, bot: Bot):
    """To'lovni tasdiqlab, DARHOL barcha kanallarga chiqarish."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
        return

    vacancy_id = int(callback.data.replace("admin_approve_and_post_", ""))
    vacancy = get_vacancy(vacancy_id)
    if not vacancy:
        await callback.answer("❌ E'lon topilmadi!", show_alert=True)
        return

    update_vacancy(
        vacancy_id,
        status="queued",
        payment_confirmed_at=datetime.now().isoformat(),
        payment_confirmed_by=callback.from_user.id,
        payment_note=f"Qo'lda tasdiqladi va hozir chiqardi: {callback.from_user.full_name}"
    )

    scheduler = PostScheduler(bot)
    res = await scheduler.post_immediately(vacancy_id)

    caption = callback.message.caption or callback.message.text or ""
    try:
        status_text = "✅ <b>TASDIQLANDI VA HOZIR KANALGA CHIQARILDI! 🚀</b>" if res else "✅ <b>TASDIQLANDI (Navbatga qo'yildi)</b>"
        if callback.message.photo:
            await callback.message.edit_caption(caption=caption + f"\n\n{status_text} ({callback.from_user.full_name})", parse_mode="HTML")
        else:
            await callback.message.edit_text(text=caption + f"\n\n{status_text} ({callback.from_user.full_name})", parse_mode="HTML")
    except Exception:
        pass

    await callback.answer("🚀 Kanalga chiqarildi!")


@router.callback_query(F.data.startswith("admin_approve_"))
async def admin_approve_payment(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
        return

    vacancy_id = int(callback.data.replace("admin_approve_", ""))
    vacancy = get_vacancy(vacancy_id)
    if not vacancy:
        await callback.answer("❌ E'lon topilmadi!", show_alert=True)
        return

    if vacancy["status"] in ["queued", "posted"]:
        await callback.answer("⚠️ Bu e'lon allaqachon tasdiqlangan!", show_alert=True)
        return

    update_vacancy(
        vacancy_id,
        status="queued",
        payment_confirmed_at=datetime.now().isoformat(),
        payment_confirmed_by=callback.from_user.id,
        payment_note=f"Qo'lda tasdiqladi: {callback.from_user.full_name}"
    )

    channels = json.loads(vacancy["channels"]) if isinstance(vacancy["channels"], str) else vacancy.get("channels", [])
    for channel_key in channels:
        add_to_queue(vacancy_id, channel_key)

    queue_count = get_queue_count()

    caption = callback.message.caption or callback.message.text or ""
    try:
        if callback.message.photo:
            await callback.message.edit_caption(
                caption=caption + f"\n\n✅ <b>TASDIQLANDI</b> ({callback.from_user.full_name})\n📋 Navbatda: {queue_count} ta e'lon",
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                text=caption + f"\n\n✅ <b>TASDIQLANDI</b> ({callback.from_user.full_name})\n📋 Navbatda: {queue_count} ta e'lon",
                parse_mode="HTML"
            )
    except Exception:
        pass

    try:
        await bot.send_message(
            chat_id=vacancy["user_id"],
            text=f"🎉 <b>To'lovingiz muvaffaqiyatli tasdiqlandi!</b>\n\n"
                 f"📌 E'lon: <code>#{vacancy_id}</code>\n"
                 f"📋 Navbatdagi o'rningiz: {queue_count}\n"
                 f"⏰ E'loningiz tez orada belgilangan kanallarga chiqariladi!",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Foydalanuvchiga xabar yetkazishda xatolik: {e}")

    await callback.answer("✅ To'lov tasdiqlandi va navbatga qo'yildi!")


@router.callback_query(F.data.startswith("admin_reject_"))
async def admin_reject_payment(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        return

    vacancy_id = int(callback.data.replace("admin_reject_", ""))
    vacancy = get_vacancy(vacancy_id)
    if not vacancy:
        await callback.answer("❌ E'lon topilmadi!", show_alert=True)
        return

    update_vacancy(vacancy_id, status="rejected")

    caption = callback.message.caption or callback.message.text or ""
    try:
        if callback.message.photo:
            await callback.message.edit_caption(caption=caption + f"\n\n❌ <b>RAD ETILDI</b> ({callback.from_user.full_name})", parse_mode="HTML")
        else:
            await callback.message.edit_text(text=caption + f"\n\n❌ <b>RAD ETILDI</b> ({callback.from_user.full_name})", parse_mode="HTML")
    except Exception:
        pass

    try:
        await bot.send_message(
            chat_id=vacancy["user_id"],
            text=f"❌ <b>To'lovingiz tasdiqlanmadi</b>\n\n📌 E'lon: <code>#{vacancy_id}</code>\n"
                 f"Sabab: To'lov cheki mos kelmadi yoki summa to'liq tushmadi.\n"
                 f"Iltimos, qaytadan tekshiring yoki adminga murojaat qiling.",
            parse_mode="HTML"
        )
    except Exception:
        pass

    await callback.answer("❌ Rad etildi!")


# ==================== KUTILAYOTGAN TO'LOVLAR & NAVBAT & STATISTIKA ====================

@router.callback_query(F.data == "admin_pending")
async def admin_pending_payments_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    pending = get_pending_payments()
    if not pending:
        await callback.message.edit_text("✅ Hozirda kutilayotgan to'lovlar mavjud emas.", reply_markup=admin_menu_kb())
        await callback.answer()
        return

    text = f"💳 <b>Kutilayotgan to'lovlar ({len(pending)} ta):</b>\n\n"
    for v in pending[:15]:
        amt = v.get("exact_amount") or v.get("total_price") or 0
        text += (
            f"📌 <code>#{v['id']}</code> — <b>{v.get('company_name', 'Nomsiz')}</b>\n"
            f"   👤 {v.get('full_name', '—')} (@{v.get('username', '—')})\n"
            f"   💰 Aniq summa: <b>{amt:,} UZS</b>\n"
            f"   Holat: <code>{v['status']}</code>\n\n"
        )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=admin_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "admin_queue")
async def admin_queue_list(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    queued = get_all_vacancies_by_status("queued")
    count = get_queue_count()
    text = f"📋 <b>Navbatdagi e'lonlar (Jami: {count} ta kanal navbati):</b>\n\n"

    buttons = []
    if not queued:
        text += "<i>Hozircha navbatda e'lonlar yo'q. Kanal bo'sh!</i>"
    else:
        for v in queued[:10]:
            text += f"📌 <code>#{v['id']}</code> — <b>{v.get('company_name', 'Nomsiz')}</b> ({v.get('job_type', '—')})\n"
            buttons.append([
                InlineKeyboardButton(text=f"🚀 #{v['id']} ni HOZIR chiqarish", callback_data=f"admin_post_now_btn_{v['id']}")
            ])

    buttons.append([InlineKeyboardButton(text="⬅️ Admin panelga qaytish", callback_data="admin_main")])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


@router.callback_query(F.data == "admin_stats")
async def admin_stats_show(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    stats = get_stats_summary()
    text = format_stats(stats)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=admin_menu_kb())
    await callback.answer()


# ==================== XABAR TARQATISH (BROADCAST) ====================

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    await state.set_state(AdminStates.broadcasting)
    text = """📨 <b>Barcha foydalanuvchilarga xabar tarqatish</b>

Iltimos, tarqatiladigan xabarni yuboring (matn yoki rasm bilan):"""

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="admin_main")]
    ])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.message(AdminStates.broadcasting)
async def admin_broadcast_finish(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return

    users = get_all_users()
    total = len(users)
    sent = 0
    failed = 0

    status_msg = await message.answer(f"⏳ Xabar tarqatilmoqda... (0/{total})")

    for u in users:
        try:
            await message.copy_to(chat_id=u["user_id"])
            sent += 1
        except Exception:
            failed += 1

    await state.clear()
    await status_msg.edit_text(
        f"✅ <b>Xabar tarqatish yakunlandi!</b>\n\n"
        f"👥 Jami foydalanuvchilar: {total}\n"
        f"✅ Yetkazildi: {sent}\n"
        f"❌ Yetib bormadi (bloklagan): {failed}",
        parse_mode="HTML",
        reply_markup=admin_menu_kb()
    )


# ==================== DARHOL JOYLASH KOMANDASI ====================

@router.message(Command("post_now"))
async def cmd_post_now(message: Message, bot: Bot):
    if not is_admin(message.from_user.id):
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer("Foydalanish: <code>/post_now &lt;vacancy_id&gt;</code>", parse_mode="HTML")
        return

    try:
        vacancy_id = int(args[1])
    except ValueError:
        await message.answer("❌ Noto'g'ri ID!")
        return

    scheduler = PostScheduler(bot)
    res = await scheduler.post_immediately(vacancy_id)
    if res:
        await message.answer(f"✅ <b>E'lon #{vacancy_id} darhol barcha kanallarga joylashtirildi!</b>", parse_mode="HTML")
    else:
        await message.answer(f"❌ E'lon #{vacancy_id} ni chiqarishda xatolik yuz berdi.", parse_mode="HTML")
