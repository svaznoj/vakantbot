"""
Telegram Premium Custom Emoji va Rangli Tugmalar yordamchisi.
"""
from config_emojis import CUSTOM_EMOJI_IDS


def tg_icon(key: str, fallback: str = "✨") -> str:
    """
    Xabar matnida haqiqiy Telegram Premium Custom Emoji ko'rsatish.
    Telegram Premium bor akkauntlarda ushbu ID animatsiyali rangli emoji bo'lib ko'rinadi.
    """
    emoji_id = CUSTOM_EMOJI_IDS.get(key, "").strip()
    if emoji_id:
        return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'
    return fallback
