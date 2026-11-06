"""Majburiy obunani tekshirish moduli."""
import logging
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_active_mandatory_channels

logger = logging.getLogger(__name__)


async def check_user_subscriptions(bot: Bot, user_id: int) -> tuple[bool, list]:
    """
    Foydalanuvchi majburiy kanallarga a'zo bo'lganmi yoki yo'qligini tekshiradi.
    Qaytaradi: (barchasiga_azo_bolganmi: bool, azo_bolmagan_kanallar: list)
    """
    channels = get_active_mandatory_channels()
    if not channels:
        return True, []

    missing = []
    for ch in channels:
        try:
            member = await bot.get_chat_member(chat_id=ch["channel_id"], user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                missing.append(ch)
        except Exception as e:
            logger.warning(f"Kanalga a'zolikni tekshirishda xatolik ({ch['channel_id']}): {e}")
            # Agar bot kanalga admin bo'lmasa yoki xatolik bo'lsa, foydalanuvchini bloklab qo'ymaslik uchun e'tibor qaratamiz
            # Lekin agar username yoki invite link bor bo'lsa ro'yxatga qo'shamiz
            missing.append(ch)

    return len(missing) == 0, missing


def get_subscription_keyboard(missing_channels: list) -> InlineKeyboardMarkup:
    """A'zo bo'lmagan kanallar ro'yxati va tekshirish tugmasi."""
    buttons = []
    for i, ch in enumerate(missing_channels, 1):
        # Havolani aniqlash
        url = ch.get("invite_link")
        if not url and ch.get("username"):
            username = ch["username"].replace("@", "")
            url = f"https://t.me/{username}"
        elif not url:
            url = f"https://t.me/"

        title = ch.get("title") or f"Kanal #{i}"
        buttons.append([InlineKeyboardButton(text=f"📢 {title}", url=url)])

    buttons.append([InlineKeyboardButton(text="🔄 A'zo bo'ldim / Tekshirish", callback_data="check_subscription")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
