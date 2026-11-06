# 🤖 Vakansiya E'lon Bot (Professional Versiya)

Ish va vakansiya kanallari uchun e'lon berish, to'lovni avtomatlashtirish va kanallarga joylash tizimi.

---

## 🌟 Yangi qo'shilgan va to'liq sozlangan funksiyalar

### 1. ⚡️ @humocardbot / SMS orqali 100% AVTO TO'LOV
- **To'lovlarni avtomatik ajratib olish (identifikatsiya):**
  Masalan, 1000 so'm to'lov kerak bo'lsa, bot foydalanuvchiga unikal summa beradi: **`1003 so'm`** (1 dan 99 so'mgacha unikal qo'shimcha).
- **Avto tekshirish mexanizmi:**
  - `@humocardbot` yoki Humo/Uzcard SMS xabari botga kelishi yoki forward qilinishi bilan, bot matndagi `1003` so'mni bir zumda aniqlaydi (`Regex`).
  - Bazadagi aynan shu summaga mos e'lon topilib, statusi **`queued` (tasdiqlangan)** ga o'tadi.
  - Foydalanuvchiga tabrik xabari yetkaziladi va admin aralashuvisiz e'lon navbatga qo'yiladi!

### 2. 📢 Xohlagancha Majburiy Obuna Kanallarini Boshqarish
- Admin paneldan:
  - ➕ Istalgancha yangi kanal qo'shish (kanal ID yoki link/username).
  - 📋 Barcha majburiy kanallar holatini ko'rish (faol/nofaol).
  - ❌ Bir bosishda majburiy kanaldan o'chirish.
- Foydalanuvchi botga kirganda barcha kanallarga a'zoligi tekshiriladi, a'zo bo'lmagan kanallar havolasi va **«🔄 Tekshirish»** tugmasi beriladi.

### 3. 🖼 E'lon uchun Rasm (O'z rasmi yoki Umumiy Banner)
- Foydalanuvchi e'lon berayotganda 3 xil variantdan tanlaydi:
  1. **📸 O'z rasmimni yuklayman** — kompaniyaning tayyor reklama rasmi.
  2. **🖼 Umumiy banner qo'yilsin** — admin tomonidan o'rnatilgan rasmiy chiroyli banner biriktiriladi.
  3. **📄 Rasmsiz** — faqat matnli e'lon.
- Admin paneldan umumiy bannerni istalgan paytda yuklash, ko'rish yoki o'chirish mumkin!

### 4. 🔐 Mukammal Admin Panel (`/admin`)
- 💳 **Kutilayotgan to'lovlar** va qo'lda tasdiqlash/rad etish
- 📢 **Majburiy obuna kanallari boshqaruvi**
- 💼 **E'lon kanallari va ularning narxlarini boshqarish**
- 🖼 **Umumiy banner sozlamalari**
- 💳 **Karta raqami va egasini bot ichidan o'zgartirish**
- 📊 **Mukammal statistika** (foydalanuvchilar, daromad, kanallar)
- 📨 **Barcha foydalanuvchilarga xabar tarqatish (Broadcast)**
- ⚡️ `/post_now <id>` orqali navbatni kutmasdan darhol kanalga chiqarish

### 5. ✨ Premium Emojilar va Zamonaviy Format
- Jozibador, qulay o'qiladigan va Telegram formatiga moslashtirilgan estetik ko'rinish.

---

## 🚀 Ishga tushirish

1. `.env` faylida bot tokenini kiriting:
   ```env
   BOT_TOKEN=YOUR_BOT_TOKEN_HERE
   ADMIN_IDS=YOUR_TELEGRAM_ID
   ```

2. Botni ishga tushiring:
   ```bash
   python bot.py
   ```

3. Tizim funksiyalarini tekshirish (Test):
   ```bash
   python test_system.py
   ```
