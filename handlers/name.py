from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from states import Form
import json
import logging
from .age_and_city import ask_age

router = Router()
logger = logging.getLogger(__name__)

# Улучшенные функции работы с профилями
async def load_profile(user_id: int) -> dict:
    """Загрузка профиля с обработкой ошибок и логированием"""
    try:
        with open("user_profiles.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            return data.get(str(user_id), {})
    except FileNotFoundError:
        logger.info("Файл профилей не найден, будет создан новый")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка чтения JSON: {e}")
        return {}
    except Exception as e:
        logger.error(f"Неожиданная ошибка при загрузке профиля: {e}")
        return {}

def save_profile(user_id: int, data: dict) -> bool:
    """Сохранение профиля с улучшенной обработкой ошибок"""
    try:
        # Пытаемся загрузить существующие данные
        try:
            with open("user_profiles.json", "r", encoding="utf-8") as file:
                profiles = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            profiles = {}

        # Обновляем данные пользователя
        profiles[str(user_id)] = data

        # Сохраняем обратно
        with open("user_profiles.json", "w", encoding="utf-8") as file:
            json.dump(profiles, file, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения профиля: {e}")
        return False

# Улучшенное приветствие
@router.message(F.text == "/start")
async def welcome_message(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Создать анкету")],
            [KeyboardButton(text="Моя анкета")]  # Новая кнопка для просмотра существующей анкеты
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer(
        "Привет! Я помогу тебе создать анкету.\n"
        "Выбери действие:",
        reply_markup=keyboard
    )

# Старт анкеты с улучшенной логикой
@router.message(F.text == "Создать анкету")
async def start_profile(message: types.Message, state: FSMContext):
    user_data = await load_profile(message.from_user.id)
    
    # Формируем клавиатуру с предложением использовать сохранённое имя
    if "name" in user_data:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=user_data["name"])],
                [KeyboardButton(text="Изменить имя")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        text = (f"Твоё текущее имя: {user_data['name']}\n"
                "Можешь оставить его или ввести новое:")
    else:
        keyboard = ReplyKeyboardRemove()
        text = "Давай начнём с имени! Как тебя зовут?"

    await message.answer(text, reply_markup=keyboard)
    await state.set_state(Form.name)

# Обработка имени с валидацией
@router.message(Form.name)
async def process_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    
    # Валидация имени
    if not name or len(name) < 2:
        await message.answer("Имя должно содержать хотя бы 2 символа. Попробуй ещё раз!")
        return
        
    if len(name) > 50:
        await message.answer("Имя слишком длинное. Максимум 50 символов.")
        return
    
    # Сохранение с проверкой результата
    user_data = await load_profile(message.from_user.id)
    user_data["name"] = name
    if not save_profile(message.from_user.id, user_data):
        await message.answer("Произошла ошибка при сохранении. Попробуй ещё раз.")
        return
    
    # Переход к следующему шагу
    await message.answer(f"Отлично, {name}! Теперь укажи свой возраст.", 
                        reply_markup=ReplyKeyboardRemove())
    await ask_age(message, state)
