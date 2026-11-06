"""E'lon navbati va kanallarga joylashtirish moduli (rasmli va rasmsiz)."""
import asyncio
import json
import logging
from datetime import datetime

from aiogram import Bot

from config import POST_INTERVAL_MINUTES, POST_START_HOUR, POST_END_HOUR
from database import (
    get_next_in_queue, update_queue_item, update_vacancy,
    get_vacancy, log_event, get_posting_channels, get_setting
)
from utils.formatter import format_vacancy_for_channel

logger = logging.getLogger(__name__)


class PostScheduler:
    """E'lonlarni kanallarga rejalashtirilgan tartibda joylashtirish."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.is_running = False
        self._task = None

    async def start(self):
        """Schedulerni ishga tushirish."""
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Post scheduler ishga tushdi")

    async def stop(self):
        """Schedulerni to'xtatish."""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Post scheduler to'xtatildi")

    async def _run_loop(self):
        """Asosiy tsikl."""
        while self.is_running:
            try:
                now = datetime.now()
                # Ruxsat etilgan soatlar oralig'ida
                if POST_START_HOUR <= now.hour < POST_END_HOUR:
                    await self._process_queue()

                await asyncio.sleep(POST_INTERVAL_MINUTES * 60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler xatosi: {e}")
                await asyncio.sleep(30)

    async def _send_post_to_channel(self, chat_id: int, text: str, photo_file_id: str = None) -> int:
        """Kanalga rasm yoki oddiy xabar yuborish va message_id qaytarish."""
        default_banner = get_setting("default_banner_file_id", "")
        banner_to_use = photo_file_id or default_banner

        if banner_to_use:
            try:
                msg = await self.bot.send_photo(
                    chat_id=chat_id,
                    photo=banner_to_use,
                    caption=text,
                    parse_mode="HTML"
                )
                return msg.message_id
            except Exception as e:
                logger.warning(f"Rasm bilan yuborishda xatolik, matn bilan urinib ko'rilmoqda: {e}")

        # Agar rasm bo'lmasa yoki rasmda xato bersa
        msg = await self.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="HTML"
        )
        return msg.message_id

    async def _process_queue(self):
        """Navbatdagi e'lonni joylash."""
        queue_item = get_next_in_queue()
        if not queue_item:
            return

        try:
            update_queue_item(queue_item["id"], status="posting")
            channels = get_posting_channels(only_active=False)
            channel_key = queue_item["channel_key"]

            if channel_key not in channels:
                logger.error(f"Kanal topilmadi: {channel_key}")
                update_queue_item(queue_item["id"], status="failed")
                return

            channel = channels[channel_key]
            vacancy = get_vacancy(queue_item["vacancy_id"])
            if not vacancy:
                update_queue_item(queue_item["id"], status="failed")
                return

            post_text = format_vacancy_for_channel(vacancy)
            photo_id = vacancy.get("photo_file_id")

            # Kanalga chiqarish
            message_id = await self._send_post_to_channel(
                chat_id=channel["chat_id"],
                text=post_text,
                photo_file_id=photo_id
            )

            # Navbatni yangilash
            update_queue_item(
                queue_item["id"],
                status="posted",
                posted_at=datetime.now().isoformat(),
                message_id=message_id
            )

            # Vakansiya ma'lumotlarini yangilash
            posted_ids = json.loads(vacancy.get("posted_message_ids", "{}")) if vacancy.get("posted_message_ids") else {}
            posted_ids[channel_key] = message_id
            update_vacancy(
                vacancy["id"],
                posted_message_ids=json.dumps(posted_ids),
                status="posted",
                posted_at=datetime.now().isoformat()
            )

            # Foydalanuvchini xabardor qilish
            try:
                ch_title = channel.get('name') or "Kanal"
                ch_user = channel.get('username') or ""
                await self.bot.send_message(
                    chat_id=vacancy["user_id"],
                    text=f"🚀 <b>Tabriklaymiz!</b> Sizning <code>#{vacancy['id']}</code>-raqamli e'loningiz "
                         f"<b>{ch_title}</b> kanaliga muvaffaqiyatli joylashtirildi!\n\n"
                         f"🔗 {ch_user}",
                    parse_mode="HTML"
                )
            except Exception:
                pass

            log_event("post_published", vacancy["user_id"], vacancy["id"], {
                "channel": channel_key,
                "message_id": message_id
            })

            logger.info(f"E'lon #{vacancy['id']} {channel['name']} kanaliga joylashtirildi")

        except Exception as e:
            logger.error(f"E'lon joylashda xatolik: {e}")
            update_queue_item(queue_item["id"], status="failed")

    async def post_immediately(self, vacancy_id: int) -> bool:
        """Admin komandasi orqali e'lonni zudlik bilan barcha tanlangan kanallarga joylash."""
        vacancy = get_vacancy(vacancy_id)
        if not vacancy:
            return False

        channels_dict = get_posting_channels(only_active=False)
        channels = json.loads(vacancy["channels"]) if isinstance(vacancy["channels"], str) else vacancy.get("channels", [])
        post_text = format_vacancy_for_channel(vacancy)
        photo_id = vacancy.get("photo_file_id")

        success = False
        posted_ids = json.loads(vacancy.get("posted_message_ids", "{}")) if vacancy.get("posted_message_ids") else {}

        for ch_key in channels:
            if ch_key in channels_dict:
                ch = channels_dict[ch_key]
                try:
                    msg_id = await self._send_post_to_channel(
                        chat_id=ch["chat_id"],
                        text=post_text,
                        photo_file_id=photo_id
                    )
                    posted_ids[ch_key] = msg_id
                    success = True
                except Exception as e:
                    logger.error(f"Xatolik e'lon #{vacancy_id} ni {ch['name']} ga joylashda: {e}")

        if success:
            update_vacancy(
                vacancy_id,
                posted_message_ids=json.dumps(posted_ids),
                status="posted",
                posted_at=datetime.now().isoformat()
            )
            # Foydalanuvchiga xabar
            try:
                await self.bot.send_message(
                    chat_id=vacancy["user_id"],
                    text=f"🚀 <b>E'loningiz barcha belgilangan kanallarga joylashtirildi!</b> (E'lon #{vacancy_id})",
                    parse_mode="HTML"
                )
            except Exception:
                pass

        return success
