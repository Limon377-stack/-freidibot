import json
import logging
from typing import Dict, Any
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from states import Form
from handlers import photo

router = Router()
logger = logging.getLogger(__name__)

# Кеш профилей (опционально)
PROFILES_CACHE: Dict[str, Any] = {}

def get_skip_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Пропустить")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

async def load_profile(user_id: int) -> dict:
    """Загружает профиль из кеша или файла."""
    if str(user_id) in PROFILES_CACHE:
        return PROFILES_CACHE[str(user_id)]
    
    try:
        with open("user_profiles.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            PROFILES_CACHE.update(data)
            return data.get(str(user_id), {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_profile(user_id: int, data: dict) -> None:
    """Сохраняет профиль в файл и кеш."""
    try:
        with open("user_profiles.json", "r+", encoding="utf-8") as file:
            try:
                profiles = json.load(file)
            except json.JSONDecodeError:
                profiles = {}
            
            profiles[str(user_id)] = data
            PROFILES_CACHE[str(user_id)] = data
            
            file.seek(0)
            json.dump(profiles, file, ensure_ascii=False, indent=4)
            file.truncate()
    except Exception as e:
        logger.error(f"Ошибка сохранения профиля: {e}")
        raise

@router.message(Form.description)
async def process_description(message: types.Message, state: FSMContext):
    description = message.text.strip()
    user_id = message.from_user.id
    logger.info(f"User {user_id} submitted description: {description}")

    if description.lower() == "пропустить":
        await message.answer("✅ Описание пропущено.", reply_markup=ReplyKeyboardRemove())
        await photo.ask_photo(message, state)
        return

    if len(description) < 10 or len(description.split()) < 2:
        await message.answer("❌ Описание должно быть не короче 10 символов и 2 слов.")
        return

    forbidden_words = ["реклама", "спам", "мат"]
    if any(word in description.lower() for word in forbidden_words):
        await message.answer("❌ Обнаружены запрещённые слова.")
        return

    try:
        user_data = await load_profile(user_id)
        user_data["description"] = description
        save_profile(user_id, user_data)
        await message.answer("✅ Описание сохранено!", reply_markup=ReplyKeyboardRemove())
        await photo.ask_photo(message, state)
    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")
        await message.answer("❌ Ошибка. Попробуйте позже.")
