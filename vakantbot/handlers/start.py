"""/start va asosiy komandalar handleri."""
import logging

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from database import get_or_create_user, get_posting_channels, get_setting
from keyboards.inline import main_menu_kb, back_to_menu_kb
from utils.subscription import check_user_subscriptions, get_subscription_keyboard

logger = logging.getLogger(__name__)
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    """Start komandasi — majburiy obuna bilan tekshiriladi."""
    await state.clear()

    user = get_or_create_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name
    )

    # 1. Majburiy obunani tekshirish
    is_subscribed, missing = await check_user_subscriptions(bot, message.from_user.id)
    if not is_subscribed:
        text = f"""👋 <b>Assalomu alaykum, {message.from_user.first_name}!</b>

Botimizdan to'liq foydalanish va vakansiya e'lonlarini joylashtirish uchun quyidagi <b>rasmiy kanallarimizga</b> a'zo bo'ling:"""
        await message.answer(text, parse_mode="HTML", reply_markup=get_subscription_keyboard(missing))
        return

    # Asosiy xush kelibsiz xabari
    text = f"""🤖 <b>Assalomu alaykum, {message.from_user.first_name}!</b>

Men — <b>Vakansiya E'lon Bot</b>iman.

Katta auditoriyaga ega kanallarimizga ish vakansiyalarini tez va avtomatlashtirilgan tarzda joylashtirishingiz mumkin.

✨ <b>Imkoniyatlarimiz:</b>
✅ Ma'lumotlarni bosqichma-bosqich qulay kiritish
✅ O'z rasmingizni yoki umumiy bannerimizni biriktirish
✅ @humocardbot / Karta orqali <b>100% AVTO to'lov</b>
✅ Navbat bo'yicha e'lonni kanallarga avtomatik chiqarish

Quyidagi menyudan kerakli bo'limni tanlang 👇"""

    await message.answer(text.strip(), parse_mode="HTML", reply_markup=main_menu_kb())


@router.callback_query(F.data == "check_subscription")
async def process_check_subscription(callback: CallbackQuery, bot: Bot, state: FSMContext):
    """Foydalanuvchi majburiy obunani tekshirish tugmasini bosganda."""
    is_subscribed, missing = await check_user_subscriptions(bot, callback.from_user.id)
    if not is_subscribed:
        await callback.answer("⚠️ Hali barcha kanallarga a'zo bo'lmadingiz! Iltimos, barchasiga qo'shiling.", show_alert=True)
        return

    await callback.answer("✅ Rahmat! Obuna tasdiqlandi.", show_alert=False)
    await state.clear()

    text = f"""🤖 <b>Bosh menyu</b>

Vakansiya joylashtirish yoki ma'lumotlarni ko'rish uchun tanlang 👇"""
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=main_menu_kb())


@router.callback_query(F.data == "main_menu")
async def show_main_menu(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Asosiy menyuga qaytish."""
    is_subscribed, missing = await check_user_subscriptions(bot, callback.from_user.id)
    if not is_subscribed:
        await callback.message.edit_text(
            "⚠️ Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling:",
            reply_markup=get_subscription_keyboard(missing)
        )
        await callback.answer()
        return

    await state.clear()
    text = "🏠 <b>Bosh menyu</b>\n\nQuyidagi bo'limlardan birini tanlang 👇"
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=main_menu_kb())
    await callback.answer()


@router.message(Command("myid"))
@router.message(Command("id"))
async def cmd_myid(message: Message):
    """Foydalanuvchining Telegram ID raqamini ko'rsatish."""
    await message.answer(
        f"👤 <b>Sizning ma'lumotlaringiz:</b>\n\n"
        f"🆔 Telegram ID: <code>{message.from_user.id}</code>\n"
        f"👤 Ism: {message.from_user.full_name}\n\n"
        f"💡 <i>Admin huquqini olish uchun ushbu ID raqamni Railway Variables dagi <code>ADMIN_IDS</code> ga kiriting.</i>",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "show_channels")
async def show_channels(callback: CallbackQuery):
    """Faol kanallar ro'yxatini ko'rsatish."""
    channels = get_posting_channels(only_active=True)
    text = "📢 <b>Bizning rasmiy e'lon kanallarimiz:</b>\n\n"

    for key, ch in channels.items():
        price_formatted = f"{ch['price']:,}".replace(",", " ")
        text += f"""📌 <b>{ch['name']}</b>
   👥 Obunachilar: {ch.get('subscribers', '10K+')}
   📝 {ch.get('description', '')}
   💰 Narx: <b>{price_formatted} UZS</b>
   🔗 {ch.get('username', '—')}

"""

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✨ E'lon berish", callback_data="new_post")],
        [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu")],
    ])

    await callback.message.edit_text(text.strip(), parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "show_prices")
async def show_prices(callback: CallbackQuery):
    """Narxlarni ko'rsatish."""
    channels = get_posting_channels(only_active=True)
    text = "💰 <b>E'lon joylashtirish narxlari:</b>\n\n"

    for key, ch in channels.items():
        price_formatted = f"{ch['price']:,}".replace(",", " ")
        text += f"📢 <b>{ch['name']}</b> — <code>{price_formatted} UZS</code>\n"

    text += """\n💡 <i>Bir nechta kanalni bir vaqtning o'zida tanlashingiz mumkin. Har bir e'lon to'lov amalga oshirilgach avtomatik navbatga kiritiladi.</i>"""

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✨ E'lon berish", callback_data="new_post")],
        [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu")],
    ])

    await callback.message.edit_text(text.strip(), parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "contact_admin")
async def contact_admin(callback: CallbackQuery):
    """Admin bilan aloqa."""
    phone = get_setting("payment_phone", "+998901234567")
    text = f"""📞 <b>Aloqa va qo'llab-quvvatlash</b>

Savollar, takliflar yoki maxsus hamkorlik bo'yicha murojaat qilishingiz mumkin:

📱 Telefon: <code>{phone}</code>
⏰ Ish vaqti: 09:00 dan 22:00 gacha

Yordam kerak bo'lsa, xush kelibsiz!"""
    await callback.message.edit_text(text.strip(), parse_mode="HTML", reply_markup=back_to_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop_handler(callback: CallbackQuery):
    await callback.answer("👆 Iltimos, kamida bitta kanal tanlang!", show_alert=True)


@router.callback_query(F.data == "cancel")
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ Jarayon bekor qilindi.\n\n🏠 Bosh menyuga qaytish uchun tugmani bosing:",
        reply_markup=back_to_menu_kb()
    )
    await callback.answer()
