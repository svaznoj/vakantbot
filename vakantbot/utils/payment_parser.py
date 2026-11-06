"""@humocardbot va to'lov bildirishnomalarini tahlil qilish (avto to'lov)."""
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def extract_payment_amount(text: str) -> Optional[int]:
    """
    @humocardbot, SMS, Payme, Click yoki to'lov xabaridan aniq summani ajratib oladi.
    Masalan:
    'Popolnenie: 50 003.00 UZS' -> 50003
    'Karta to'ldirildi: 1003 so'm' -> 1003
    'Karta to'ldirildi: +1 003.00 UZS' -> 1003
    '+1003 UZS' -> 1003
    'Summa: 1003' -> 1003
    'Oplata 1003 uzs' -> 1003
    """
    if not text:
        return None

    # Standartlashtirish
    cleaned = text.replace('\xa0', ' ').replace('&nbsp;', ' ').replace(',', '.')

    # 1. Valyuta (UZS, so'm, sum) bilan kelgan summalar
    # Masalan: 1 003.00 UZS, 50 003 UZS, 1003 so'm, 1003.00
    currency_patterns = [
        r'(?:[+]?\s*)(\d{1,3}(?:[\s]\d{3})*|\d+)(?:\.00)?\s*(?:uzs|so[\'"`]?m|sum)',
        r'(?:summa|oplata|popolnenie|to[\'"`]?ldirildi|tushum|prihod|karta)[\s\:\-]+(?:[+]?\s*)(\d{1,3}(?:[\s]\d{3})*|\d+)(?:\.00)?',
        r'(\d+)\s*(?:uzs|so[\'"`]?m|sum)',
    ]

    for pat in currency_patterns:
        match = re.search(pat, cleaned, re.IGNORECASE)
        if match:
            raw_num = match.group(1).replace(' ', '')
            try:
                val = int(raw_num)
                if val > 0:
                    return val
            except ValueError:
                continue

    # 2. Agar foydalanuvchi faqat raqamning o'zini yuborgan bo'lsa (masalan: 1003)
    clean_digits = re.sub(r'[^\d]', '', cleaned)
    if clean_digits and len(clean_digits) >= 4 and len(clean_digits) <= 9:
        try:
            return int(clean_digits)
        except ValueError:
            pass

    return None
