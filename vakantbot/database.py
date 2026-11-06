"""Ma'lumotlar bazasi bilan ishlash moduli."""
import sqlite3
import json
import random
from datetime import datetime
from typing import Optional, List, Dict, Any
from config import DATABASE_PATH, CHANNELS, PAYMENT_CARD, PAYMENT_CARD_HOLDER, PAYMENT_PHONE


def get_connection():
    """Ma'lumotlar bazasiga ulanish."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Ma'lumotlar bazasini yaratish va yangilash."""
    conn = get_connection()
    cursor = conn.cursor()

    # Sozlamalar jadvali (dinamik parametrlar)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bot_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # Foydalanuvchilar jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_posts INTEGER DEFAULT 0,
            is_blocked INTEGER DEFAULT 0
        )
    """)

    # Majburiy obuna kanallari
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mandatory_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id INTEGER NOT NULL UNIQUE,
            title TEXT NOT NULL,
            username TEXT,
            invite_link TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # E'lon chiqadigan kanallar (admin boshqara oladi)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posting_channels (
            channel_key TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            username TEXT,
            chat_id INTEGER NOT NULL,
            price INTEGER NOT NULL DEFAULT 50000,
            currency TEXT DEFAULT 'UZS',
            description TEXT,
            subscribers TEXT DEFAULT '10K+',
            is_active INTEGER DEFAULT 1
        )
    """)

    # E'lonlar jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vacancies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            
            -- E'lon ma'lumotlari
            company_name TEXT,
            job_type TEXT,
            workers_count TEXT,
            salary TEXT,
            work_schedule TEXT,
            address TEXT,
            phone TEXT,
            requirements TEXT,
            additional_info TEXT,
            
            -- Rasm / Banner
            photo_file_id TEXT,
            use_default_photo INTEGER DEFAULT 0,
            
            -- Tanlangan kanallar (JSON list)
            channels TEXT DEFAULT '[]',
            
            -- Narx va unikal to'lov
            base_price INTEGER DEFAULT 0,
            exact_amount INTEGER DEFAULT 0, -- masalan: 50003 (unikal identifikator)
            total_price INTEGER DEFAULT 0,
            
            -- Holati
            status TEXT DEFAULT 'draft',
            -- draft, pending_payment, payment_sent, payment_confirmed, 
            -- queued, posted, cancelled, rejected
            
            -- To'lov
            payment_screenshot_file_id TEXT,
            payment_confirmed_at TIMESTAMP,
            payment_confirmed_by INTEGER,
            payment_note TEXT,
            
            -- Tayyor e'lon matni
            formatted_text TEXT,
            
            -- Joylash
            posted_at TIMESTAMP,
            posted_message_ids TEXT DEFAULT '{}',
            
            -- Vaqtlar
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # Ustunlar bor-yo'qligini tekshirib qo'shish (migration)
    cursor.execute("PRAGMA table_info(vacancies)")
    columns = [col[1] for col in cursor.fetchall()]
    if "photo_file_id" not in columns:
        cursor.execute("ALTER TABLE vacancies ADD COLUMN photo_file_id TEXT")
    if "use_default_photo" not in columns:
        cursor.execute("ALTER TABLE vacancies ADD COLUMN use_default_photo INTEGER DEFAULT 0")
    if "base_price" not in columns:
        cursor.execute("ALTER TABLE vacancies ADD COLUMN base_price INTEGER DEFAULT 0")
    if "exact_amount" not in columns:
        cursor.execute("ALTER TABLE vacancies ADD COLUMN exact_amount INTEGER DEFAULT 0")
    if "payment_note" not in columns:
        cursor.execute("ALTER TABLE vacancies ADD COLUMN payment_note TEXT")

    # E'lon navbati
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS post_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vacancy_id INTEGER NOT NULL,
            channel_key TEXT NOT NULL,
            scheduled_at TIMESTAMP,
            posted_at TIMESTAMP,
            message_id INTEGER,
            status TEXT DEFAULT 'waiting',
            
            FOREIGN KEY (vacancy_id) REFERENCES vacancies(id)
        )
    """)

    # Statistika
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            user_id INTEGER,
            vacancy_id INTEGER,
            data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Boshlang'ich posting kanallarni to'ldirish (agar bo'sh bo'lsa)
    cursor.execute("SELECT COUNT(*) FROM posting_channels")
    if cursor.fetchone()[0] == 0:
        for key, ch in CHANNELS.items():
            cursor.execute("""
                INSERT OR REPLACE INTO posting_channels 
                (channel_key, name, username, chat_id, price, currency, description, subscribers, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                key, ch["name"], ch.get("username", ""), ch["chat_id"],
                ch["price"], ch.get("currency", "UZS"), ch.get("description", ""), ch.get("subscribers", "10K+")
            ))

    # Boshlang'ich sozlamalar
    defaults = {
        "payment_card": PAYMENT_CARD,
        "payment_holder": PAYMENT_CARD_HOLDER,
        "payment_phone": PAYMENT_PHONE,
        "default_banner_file_id": "",
        "auto_payment_enabled": "1"
    }
    for k, v in defaults.items():
        cursor.execute("INSERT OR IGNORE INTO bot_settings (key, value) VALUES (?, ?)", (k, v))

    conn.commit()
    conn.close()


# ==================== SOZLAMALAR ====================

def get_setting(key: str, default: str = "") -> str:
    """Sozlamani olish."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM bot_settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key: str, value: str):
    """Sozlamani o'rnatish."""
    conn = get_connection()
    conn.execute("INSERT OR REPLACE INTO bot_settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()


# ==================== FOYDALANUVCHILAR ====================

def get_or_create_user(user_id: int, username: str = None, full_name: str = None) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute(
            "INSERT INTO users (user_id, username, full_name) VALUES (?, ?, ?)",
            (user_id, username, full_name)
        )
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
    else:
        cursor.execute(
            "UPDATE users SET username = ?, full_name = ? WHERE user_id = ?",
            (username, full_name, user_id)
        )
        conn.commit()

    conn.close()
    return dict(user)


def get_all_users() -> List[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE is_blocked = 0")
    users = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return users


# ==================== MAJBURIY OBUNA KANALLARI ====================

def add_mandatory_channel(channel_id: int, title: str, username: str = None, invite_link: str = None) -> bool:
    """Majburiy kanal qo'shish."""
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO mandatory_channels (channel_id, title, username, invite_link, is_active)
            VALUES (?, ?, ?, ?, 1)
        """, (channel_id, title, username, invite_link))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        conn.execute("""
            UPDATE mandatory_channels SET title = ?, username = ?, invite_link = ?, is_active = 1
            WHERE channel_id = ?
        """, (title, username, invite_link, channel_id))
        conn.commit()
        return True
    finally:
        conn.close()


def remove_mandatory_channel(channel_id: int) -> bool:
    """Majburiy kanalni o'chirish."""
    conn = get_connection()
    conn.execute("DELETE FROM mandatory_channels WHERE channel_id = ?", (channel_id,))
    conn.commit()
    conn.close()
    return True


def get_active_mandatory_channels() -> List[dict]:
    """Barcha faol majburiy kanallarni olish."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM mandatory_channels WHERE is_active = 1 ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_mandatory_channels() -> List[dict]:
    """Barcha majburiy kanallarni olish."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM mandatory_channels ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ==================== E'LON CHIQADIGAN KANALLAR ====================

def get_posting_channels(only_active: bool = True) -> Dict[str, dict]:
    """E'lon chiqariladigan kanallarni olish."""
    conn = get_connection()
    cursor = conn.cursor()
    if only_active:
        cursor.execute("SELECT * FROM posting_channels WHERE is_active = 1")
    else:
        cursor.execute("SELECT * FROM posting_channels")
    rows = cursor.fetchall()
    conn.close()

    result = {}
    for r in rows:
        result[r["channel_key"]] = dict(r)
    return result


def add_or_update_posting_channel(channel_key: str, name: str, chat_id: int, price: int, username: str = "", description: str = ""):
    conn = get_connection()
    conn.execute("""
        INSERT INTO posting_channels (channel_key, name, username, chat_id, price, description, is_active)
        VALUES (?, ?, ?, ?, ?, ?, 1)
        ON CONFLICT(channel_key) DO UPDATE SET
            name=excluded.name,
            username=excluded.username,
            chat_id=excluded.chat_id,
            price=excluded.price,
            description=excluded.description,
            is_active=1
    """, (channel_key, name, username, chat_id, price, description))
    conn.commit()
    conn.close()


def remove_posting_channel(channel_key: str):
    conn = get_connection()
    conn.execute("DELETE FROM posting_channels WHERE channel_key = ?", (channel_key,))
    conn.commit()
    conn.close()


# ==================== VAKANSIYA VA TO'LOV ====================

def create_vacancy(user_id: int) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO vacancies (user_id) VALUES (?)", (user_id,))
    conn.commit()
    vacancy_id = cursor.lastrowid
    conn.close()
    return vacancy_id


def generate_unique_payment_amount(base_amount: int) -> int:
    """
    To'lovni identifikatsiya qilish uchun unikal summa yaratish.
    Masalan, 50 000 bo'lsa -> 50 001 dan 50 099 gacha bo'sh bo'lgan summani tanlaydi.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT exact_amount FROM vacancies 
        WHERE status IN ('pending_payment', 'payment_sent') 
        AND exact_amount > 0
    """)
    used_amounts = {r[0] for r in cursor.fetchall()}
    conn.close()

    # 1 dan 99 gacha tasodifiy farq tanlash
    candidates = list(range(1, 100))
    random.shuffle(candidates)

    for offset in candidates:
        candidate_amount = base_amount + offset
        if candidate_amount not in used_amounts:
            return candidate_amount

    # Agar barchasi band bo'lsa (juda kam holatda), kattaroq offset
    return base_amount + random.randint(100, 999)


def find_vacancy_by_exact_amount(amount: int) -> Optional[dict]:
    """Aynan shu summaga to'lov kutilayotgan vakansiyani topish."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM vacancies 
        WHERE exact_amount = ? AND status IN ('pending_payment', 'payment_sent')
        ORDER BY id DESC LIMIT 1
    """, (amount,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_vacancy(vacancy_id: int, **kwargs):
    conn = get_connection()
    kwargs["updated_at"] = datetime.now().isoformat()
    set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
    values = list(kwargs.values()) + [vacancy_id]
    conn.execute(f"UPDATE vacancies SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()


def get_vacancy(vacancy_id: int) -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vacancies WHERE id = ?", (vacancy_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_vacancies(user_id: int, status: str = None) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    if status:
        cursor.execute(
            "SELECT * FROM vacancies WHERE user_id = ? AND status = ? ORDER BY created_at DESC",
            (user_id, status)
        )
    else:
        cursor.execute(
            "SELECT * FROM vacancies WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_pending_payments() -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT v.*, u.username, u.full_name FROM vacancies v 
        JOIN users u ON v.user_id = u.user_id 
        WHERE v.status IN ('payment_sent', 'pending_payment') 
        ORDER BY v.updated_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ==================== NAVBAT VA STATISTIKA ====================

def add_to_queue(vacancy_id: int, channel_key: str, scheduled_at: str = None):
    conn = get_connection()
    conn.execute(
        "INSERT INTO post_queue (vacancy_id, channel_key, scheduled_at) VALUES (?, ?, ?)",
        (vacancy_id, channel_key, scheduled_at)
    )
    conn.commit()
    conn.close()


def get_next_in_queue() -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute("""
        SELECT pq.*, v.formatted_text, v.photo_file_id, v.user_id FROM post_queue pq 
        JOIN vacancies v ON pq.vacancy_id = v.id 
        WHERE pq.status = 'waiting' AND (pq.scheduled_at IS NULL OR pq.scheduled_at <= ?) 
        ORDER BY pq.id ASC LIMIT 1
    """, (now,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_queue_item(queue_id: int, **kwargs):
    conn = get_connection()
    set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
    values = list(kwargs.values()) + [queue_id]
    conn.execute(f"UPDATE post_queue SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()


def get_queue_count() -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM post_queue WHERE status = 'waiting'")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_all_vacancies_by_status(status: str) -> list:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT v.*, u.username, u.full_name FROM vacancies v 
        JOIN users u ON v.user_id = u.user_id 
        WHERE v.status = ? ORDER BY v.updated_at DESC
    """, (status,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def log_event(event_type: str, user_id: int = None, vacancy_id: int = None, data: dict = None):
    conn = get_connection()
    conn.execute(
        "INSERT INTO stats (event_type, user_id, vacancy_id, data) VALUES (?, ?, ?, ?)",
        (event_type, user_id, vacancy_id, json.dumps(data) if data else None)
    )
    conn.commit()
    conn.close()


def get_stats_summary() -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    stats = {}
    cursor.execute("SELECT COUNT(*) FROM users")
    stats["total_users"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM vacancies")
    stats["total_vacancies"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM vacancies WHERE status = 'posted'")
    stats["posted_vacancies"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM vacancies WHERE status IN ('payment_sent', 'pending_payment')")
    stats["pending_payments"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM post_queue WHERE status = 'waiting'")
    stats["queue_count"] = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(exact_amount), SUM(total_price), 0) FROM vacancies WHERE status IN ('queued', 'posted')")
    stats["total_revenue"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM mandatory_channels WHERE is_active = 1")
    stats["mandatory_channels_count"] = cursor.fetchone()[0]

    conn.close()
    return stats
