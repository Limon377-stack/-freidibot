from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from states import Form
import json
import logging
from typing import Optional, Dict, Any

router = Router()
logger = logging.getLogger(__name__)

# Функция для загрузки данных из файла с кешированием
PROFILES_CACHE: Dict[str, Any] = {}

async def load_profile(user_id: int) -> Dict[str, Any]:
    """Загружает профиль пользователя с кешированием"""
    try:
        if str(user_id) in PROFILES_CACHE:
            return PROFILES_CACHE[str(user_id)]
            
        with open("user_profiles.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            PROFILES_CACHE[str(user_id)] = data.get(str(user_id), {})
            return PROFILES_CACHE[str(user_id)]
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Ошибка загрузки профиля: {e}")
        return {}
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        return {}

def save_profile(user_id: int, data: Dict[str, Any]) -> bool:
    """Сохраняет профиль пользователя"""
    try:
        # Обновляем кеш
        PROFILES_CACHE[str(user_id)] = data
        
        # Загружаем все профили
        try:
            with open("user_profiles.json", "r", encoding="utf-8") as file:
                profiles = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            profiles = {}

        # Обновляем профиль
        profiles[str(user_id)] = data

        # Сохраняем обратно
        with open("user_profiles.json", "w", encoding="utf-8") as file:
            json.dump(profiles, file, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения профиля: {e}")
        return False

def get_city_keyboard(city: Optional[str] = None) -> ReplyKeyboardMarkup:
    """Возвращает клавиатуру для выбора города"""
    if city:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=city)],
                [KeyboardButton(text="Пропустить")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Пропустить")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_age_keyboard(age: Optional[int] = None) -> ReplyKeyboardMarkup:
    """Возвращает клавиатуру для выбора возраста"""
    if age is not None:
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=str(age))]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    return ReplyKeyboardRemove()

async def ask_age(message: types.Message, state: FSMContext):
    """Запрашивает возраст пользователя"""
    user_data = await load_profile(message.from_user.id)
    age = user_data.get("age")
    
    await message.answer(
        "📅 Введите ваш возраст (от 12 до 99 лет):",
        reply_markup=get_age_keyboard(age)
    )
    await state.set_state(Form.age)

@router.message(Form.age)
async def process_age(message: types.Message, state: FSMContext):
    """Обрабатывает введенный возраст"""
    user_data = await load_profile(message.from_user.id)
    user_id = message.from_user.id
    
    # Если пользователь выбрал сохраненный возраст
    if user_data.get("age") and message.text == str(user_data["age"]):
        await ask_city(message, state)
        return

    # Валидация возраста
    if not message.text.isdigit():
        await message.answer("❌ Возраст должен быть числом. Попробуйте еще раз!")
        return
        
    age = int(message.text)
    
    if age < 12:
        await message.answer("❌ Минимальный возраст - 12 лет.")
        return
    elif age > 99:
        await message.answer("❌ Максимальный возраст - 99 лет.")
        return

    # Сохраняем возраст
    user_data["age"] = age
    if not save_profile(user_id, user_data):
        await message.answer("⚠️ Произошла ошибка при сохранении. Попробуйте позже.")
        return

    await ask_city(message, state)

async def ask_city(message: types.Message, state: FSMContext):
    """Запрашивает город пользователя"""
    user_data = await load_profile(message.from_user.id)
    city = user_data.get("city")
    
    await message.answer(
        "🏙 В каком городе вы живете?",
        reply_markup=get_city_keyboard(city)
    )
    await state.set_state(Form.city)

@router.message(Form.city)
async def process_city(message: types.Message, state: FSMContext):
    """Обрабатывает введенный город"""
    user_data = await load_profile(message.from_user.id)
    user_id = message.from_user.id
    city = message.text.strip()

    # Обработка пропуска
    if city.lower() == "пропустить":
        user_data["city"] = "Не указан"
        if not save_profile(user_id, user_data):
            await message.answer("⚠️ Произошла ошибка при сохранении.")
            return
    else:
        # Валидация города
        if len(city) < 2:
            await message.answer("❌ Название города слишком короткое.")
            return
        if len(city) > 50:
            await message.answer("❌ Название города слишком длинное.")
            return
            
        user_data["city"] = city
        if not save_profile(user_id, user_data):
            await message.answer("⚠️ Произошла ошибка при сохранении.")
            return

    await ask_description(message, state)

async def ask_description(message: types.Message, state: FSMContext):
    """Переход к запросу описания"""
    await message.answer(
        "✏️ Теперь расскажите немного о себе (минимум 10 символов):",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Form.description)
