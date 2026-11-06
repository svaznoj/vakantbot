"""FSM holatlari."""
from aiogram.fsm.state import State, StatesGroup


class VacancyForm(StatesGroup):
    """E'lon yaratish bosqichlari."""
    selecting_channels = State()
    company_name = State()
    job_type = State()
    workers_count = State()
    salary = State()
    work_schedule = State()
    address = State()
    phone = State()
    requirements = State()
    additional_info = State()
    photo_choice = State()       # O'z rasmi yoki umumiy yoki rasmsiz
    waiting_custom_photo = State() # Foydalanuvchi rasm yuborishi kutilmoqda
    preview = State()
    editing_field = State()
    waiting_payment = State()
    sending_receipt = State()


class AdminStates(StatesGroup):
    """Admin boshqaruv holatlari."""
    broadcasting = State()
    
    # Majburiy kanal qo'shish
    adding_mandatory_channel = State()
    
    # E'lon kanali qo'shish
    adding_pch_name = State()
    adding_pch_chat_id = State()
    adding_pch_price = State()
    
    # Banner va karta sozlamalari
    uploading_banner = State()
    editing_card_number = State()
    editing_card_holder = State()
