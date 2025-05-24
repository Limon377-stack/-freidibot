from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from states import Form
import json
import logging
from datetime import datetime

router = Router()
logger = logging.getLogger(__name__)

async def load_profile(user_id: int) -> dict:
    """Загрузка профиля с улучшенной обработкой ошибок"""
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

async def save_full_profile(user_id: int, data: dict) -> bool:
    """Сохранение полного профиля с фото и всеми данными"""
    try:
        # Загружаем существующие профили
        try:
            with open("user_profiles.json", "r", encoding="utf-8") as file:
                profiles = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            profiles = {}

        # Добавляем дату создания/обновления
        data["last_updated"] = datetime.now().isoformat()
        
        # Сохраняем данные
        profiles[str(user_id)] = data
        
        # Записываем в файл
        with open("user_profiles.json", "w", encoding="utf-8") as file:
            json.dump(profiles, file, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения профиля: {e}")
        return False

async def ask_photo(message: types.Message, state: FSMContext):
    """Запрос фотографии с инструкцией"""
    await message.answer(
        "📸 Отправь свою фотографию для анкеты.\n"
        "Лучше всего подойдёт чёткое фото лица.",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Form.photo)

@router.message(Form.photo, F.content_type == "photo")
async def process_photo(message: types.Message, state: FSMContext):
    """Обработка полученной фотографии"""
    try:
        # Получаем фото с наилучшим качеством
        photo = message.photo[-1].file_id
        await state.update_data(photo=photo)
        data = await state.get_data()

        # Получаем данные из состояния и сохранённого профиля
        user_data = await load_profile(message.from_user.id)
        
        # Формируем данные анкеты
        profile_data = {
            "name": data.get('name', user_data.get('name', 'Имя не указано')),
            "age": data.get('age', user_data.get('age', 'Возраст не указан')),
            "city": data.get('city', user_data.get('city', 'Город не указан')),
            "description": data.get('description', user_data.get('description', '')),
            "photo": photo,
            "created_at": datetime.now().isoformat()
        }

        # Форматируем текст анкеты
        profile_text = (
            f"👤 <b>{profile_data['name']}</b>, {profile_data['age']}, {profile_data['city']}\n"
            f"📝 <i>{profile_data['description'] or 'Нет описания'}</i>"
        )

        # Кнопка подтверждения
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="✅ Готово!")],
                [KeyboardButton(text="🔄 Изменить анкету")]
            ],
            resize_keyboard=True
        )

        # Отправляем фото с анкетой
        await message.answer_photo(
            photo=photo,
            caption=profile_text,
            parse_mode="HTML"
        )
        
        # Сообщение с кнопками
        await message.answer(
            "Вот так будет выглядеть твоя анкета. Всё правильно?",
            reply_markup=keyboard
        )

        # Сохраняем данные в состоянии для возможного редактирования
        await state.set_data(profile_data)
        
    except Exception as e:
        logger.error(f"Ошибка обработки фото: {e}")
        await message.answer("Произошла ошибка при обработке фото. Попробуй ещё раз.")

@router.message(F.text == "✅ Готово!")
async def finish_profile(message: types.Message, state: FSMContext):
    """Финальное сохранение анкеты"""
    try:
        data = await state.get_data()
        
        # Проверяем, что есть все необходимые данные
        if not all(key in data for key in ['name', 'age', 'city', 'photo']):
            await message.answer("Кажется, в анкете не хватает данных. Давай попробуем ещё раз!")
            return

        # Сохраняем профиль
        if await save_full_profile(message.from_user.id, data):
            await message.answer(
                "🎉 Анкета успешно создана!",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await message.answer(
                "Произошла ошибка при сохранении. Попробуй ещё раз.",
                reply_markup=ReplyKeyboardRemove()
            )
        
        # Очищаем состояние
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка завершения анкеты: {e}")
        await message.answer("Произошла ошибка. Попробуй ещё раз.")

@router.message(F.text == "🔄 Изменить анкету")
async def edit_profile(message: types.Message, state: FSMContext):
    """Редактирование анкеты"""
    await message.answer(
        "Давай исправим анкету. С чего начнём?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Изменить имя")],
                [KeyboardButton(text="Изменить возраст")],
                [KeyboardButton(text="Изменить город")],
                [KeyboardButton(text="Изменить описание")],
                [KeyboardButton(text="Изменить фото")]
            ],
            resize_keyboard=True
        )
    )
