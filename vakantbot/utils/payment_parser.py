"""@humocardbot va to'lov bildirishnomalarini tahlil qilish (avto to'lov)."""
import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def extract_payment_amount(text: str) -> Optional[int]:
    """
    @humocardbot, SMS yoki to'lov xabaridan aniq summani ajratib oladi.
    Masalan:
    'Popolnenie: 50 003.00 UZS' -> 50003
    'Karta to'ldirildi: 1003 so'm' -> 1003
    'Karta to'ldirildi: +1 003.00 UZS' -> 1003
    'Summa: 1003' -> 1003
    """
    if not text:
        return None

    # Bo'shliqlarni tozalash va standartlashtirish
    cleaned = text.replace('\xa0', ' ').replace('&nbsp;', ' ')

    # 1-variant: UZS / so'm / sum bilan kelgan summa
    # Masalan: 50 003.00 UZS, 1 003 so'm, 1003.00UZS
    pattern_currency = r'(?:[+]?\s*)(\d{1,3}(?:[\s\xa0]\d{3})*|\d+)(?:[.,](\d{2}))?\s*(?:UZS|so[\'"`]?m|sum)'
    match = re.search(pattern_currency, cleaned, re.IGNORECASE)
    if match:
        main_sum_str = match.group(1).replace(' ', '').replace('\xa0', '')
        try:
            return int(main_sum_str)
        except ValueError:
            pass

    # 2-variant: Popolnenie yoki Summa so'zidan keyingi raqam
    pattern_keyword = r'(?:Popolnenie|To[\'"`]?ldirildi|Summa|Postuplenie|Prihod|Tushum)[\s:]*([+]?\s*\d[\d\s]*)(?:[.,]\d{2})?'
    match2 = re.search(pattern_keyword, cleaned, re.IGNORECASE)
    if match2:
        digits = re.sub(r'[^\d]', '', match2.group(1))
        if digits:
            try:
                return int(digits)
            except ValueError:
                pass

    # 3-variant: Faqat raqamning o'zi yuborilgan bo'lsa
    only_digits = cleaned.strip()
    if only_digits.isdigit() and len(only_digits) >= 4:
        return int(only_digits)

    return None
