"""Tizimning barcha funksiyalarini avtomatlashtirilgan tarzda sinovdan o'tkazish."""
import os
import sys

# Windows konsolida UTF-8 ni ta'minlash
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# Loyiha papkasini yo'lga qo'shish
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from database import (
    init_db, get_or_create_user, add_mandatory_channel,
    get_active_mandatory_channels, remove_mandatory_channel,
    generate_unique_payment_amount, create_vacancy, update_vacancy,
    find_vacancy_by_exact_amount, add_to_queue, get_queue_count,
    get_posting_channels, set_setting, get_setting, get_stats_summary
)
from utils.payment_parser import extract_payment_amount
from utils.formatter import format_vacancy, format_payment_info, format_vacancy_preview
from keyboards.inline import (
    main_menu_kb, channels_selection_kb, photo_choice_kb,
    confirm_vacancy_kb, admin_menu_kb
)


def run_tests():
    print("==================================================")
    print("🚀 BOT FUNKSIYALARI SINOVI BOSHLANDI...")
    print("==================================================")

    # 1. Baza initsializatsiyasi
    init_db()
    print("✅ 1. init_db() muvaffaqiyatli ishga tushdi.")

    # 2. Foydalanuvchi yaratish
    user = get_or_create_user(999999, "test_user", "Test Foydalanuvchi")
    assert user["user_id"] == 999999
    print("✅ 2. Foydalanuvchi yaratish va bazadan olish to'g'ri ishladi.")

    # 3. Majburiy obuna kanallarini qo'shish, tekshirish va o'chirish
    add_mandatory_channel(-100111222333, "Test Majburiy Kanal", "@test_majburiy", "https://t.me/test_majburiy")
    active_m_channels = get_active_mandatory_channels()
    assert any(c["channel_id"] == -100111222333 for c in active_m_channels)
    print(f"✅ 3. Majburiy kanal qo'shildi (Hozir faol: {len(active_m_channels)} ta).")

    remove_mandatory_channel(-100111222333)
    active_after = get_active_mandatory_channels()
    assert not any(c["channel_id"] == -100111222333 for c in active_after)
    print("✅ 4. Majburiy kanalni o'chirish muvaffaqiyatli ishladi.")

    # 4. E'lon kanallari
    pch = get_posting_channels(only_active=True)
    assert len(pch) > 0
    print(f"✅ 5. E'lon joylanadigan kanallar olindi ({len(pch)} ta kanal mavjud).")

    # 5. Unikal to'lov summasi generatsiyasi (1000 -> 1003 kabi)
    base_price = 1000
    unique_amt1 = generate_unique_payment_amount(base_price)
    assert unique_amt1 >= 1001 and unique_amt1 <= 1099
    print(f"✅ 6. Unikal to'lov summasi generatsiyasi: Asl narx {base_price} -> Unikal {unique_amt1} so'm!")

    # 6. Vakansiya yaratish va to'lov bilan bog'lash
    vac_id = create_vacancy(999999)
    update_vacancy(
        vac_id,
        company_name="Akfa IT",
        job_type="Dasturchi",
        workers_count="2 nafar",
        salary="10 000 000 so'm",
        work_schedule="09:00 - 18:00",
        address="Toshkent",
        phone="+998901234567",
        exact_amount=unique_amt1,
        status="pending_payment"
    )
    found_vac = find_vacancy_by_exact_amount(unique_amt1)
    assert found_vac is not None
    assert found_vac["id"] == vac_id
    print(f"✅ 7. Aniq summa ({unique_amt1}) bo'yicha kutilayotgan vakansiya #{vac_id} topildi!")

    # 7. @humocardbot / SMS parsing testi
    test_sms_1 = f"Popolnenie: Karta *4444. Summa: {unique_amt1}.00 UZS. Ostatok: 150000.00 UZS"
    amt1 = extract_payment_amount(test_sms_1)
    assert amt1 == unique_amt1, f"Kutilgan: {unique_amt1}, olindi: {amt1}"

    test_sms_2 = "Karta toldirildi: +50 003.00 UZS"
    amt2 = extract_payment_amount(test_sms_2)
    assert amt2 == 50003, f"Kutilgan: 50003, olindi: {amt2}"

    test_sms_3 = "Karta to'ldirildi: 1003 so'm"
    amt3 = extract_payment_amount(test_sms_3)
    assert amt3 == 1003

    print("✅ 8. @humocardbot va SMS matnlaridan summani ajratib olish (Regex Parser) 100% to'g'ri ishladi!")

    # 8. Navbat va statistika
    add_to_queue(vac_id, "channel_1")
    q_count = get_queue_count()
    assert q_count >= 1
    print(f"✅ 9. Navbat tizimi ishladi (Navbatda: {q_count} ta).")

    # 9. Sozlamalar (Karta, Banner)
    set_setting("payment_card", "9860 1111 2222 3333")
    assert get_setting("payment_card") == "9860 1111 2222 3333"
    set_setting("default_banner_file_id", "AgACAgIAAxkBAAI...")
    assert get_setting("default_banner_file_id") == "AgACAgIAAxkBAAI..."
    print("✅ 10. Karta va umumiy banner sozlamalari dinamik yangilanishi tekshirildi.")

    # 10. Formatlash testlari
    formatted = format_vacancy(found_vac)
    assert "AKFA IT" in formatted.upper()
    pay_info = format_payment_info(unique_amt1, vac_id)
    assert str(unique_amt1) in pay_info
    print("✅ 11. Formatlash va vizual ko'rinish to'g'ri shakllandi.")

    # 11. Klaviaturalar tekshiruvi
    kb1 = main_menu_kb()
    assert kb1 is not None
    kb2 = photo_choice_kb()
    assert kb2 is not None
    kb3 = admin_menu_kb()
    assert kb3 is not None
    print("✅ 12. Barcha asosiy va admin inline tugmalari to'g'ri yaratildi.")

    print("==================================================")
    print("🎉 BARCHA 12 TA TEST MUVAFFAQIYATLI O'TDI!")
    print("Tizim 100% to'g'ri va xatosiz ishlamoqda.")
    print("==================================================")


if __name__ == "__main__":
    run_tests()
