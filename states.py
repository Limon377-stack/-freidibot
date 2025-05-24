from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# Настройка логирования
logger = logging.getLogger(__name__)

class Form(StatesGroup):
    """Класс состояний для FSM, расширенный дополнительными методами"""
    name = State()
    age = State()
    city = State()
    description = State()
    photo = State()
    
    @classmethod
    def get_all_states(cls) -> list:
        """Возвращает все состояния анкеты"""
        return [cls.name, cls.age, cls.city, cls.description, cls.photo]

class ProfileManager:
    """Класс для управления профилями с расширенной функциональностью"""
    
    def __init__(self, db_file: str = "user_profiles.json"):
        self.db_file = Path(db_file)
        self._ensure_db_exists()
        
    def _ensure_db_exists(self) -> None:
        """Создает файл БД, если он не существует"""
        if not self.db_file.exists():
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump({}, f)
            logger.info(f"Создан новый файл БД: {self.db_file}")

    def load_profile(self, user_id: int) -> Dict[str, Any]:
        """Загрузка профиля с обработкой ошибок"""
        try:
            with open(self.db_file, 'r', encoding='utf-8') as file:
                data = json.load(file)
                return data.get(str(user_id), {})
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка чтения JSON: {e}")
            return {}
        except Exception as e:
            logger.error(f"Неожиданная ошибка: {e}")
            return {}

    def save_profile(self, user_id: int, data: Dict[str, Any]) -> bool:
        """Сохранение профиля с меткой времени"""
        try:
            # Добавляем/обновляем метку времени
            data['updated_at'] = datetime.now().isoformat()
            
            # Загружаем существующие данные
            try:
                with open(self.db_file, 'r', encoding='utf-8') as file:
                    profiles = json.load(file)
            except (FileNotFoundError, json.JSONDecodeError):
                profiles = {}

            # Обновляем профиль
            profiles[str(user_id)] = data
            
            # Сохраняем обратно
            with open(self.db_file, 'w', encoding='utf-8') as file:
                json.dump(profiles, file, ensure_ascii=False, indent=4)
                
            self._log_profile_save(user_id, data)
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения профиля: {e}")
            return False

    def _log_profile_save(self, user_id: int, data: Dict[str, Any]) -> None:
        """Логирование сохранения профиля"""
        log_data = {
            'user_id': user_id,
            'name': data.get('name', 'неизвестно'),
            'age': data.get('age', '??'),
            'city': data.get('city', 'неизвестно'),
            'has_photo': 'photo' in data,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        logger.info(f"Сохранен профиль: {log_data}")

    def delete_profile(self, user_id: int) -> bool:
        """Удаление профиля"""
        try:
            with open(self.db_file, 'r', encoding='utf-8') as file:
                profiles = json.load(file)
                
            if str(user_id) in profiles:
                del profiles[str(user_id)]
                with open(self.db_file, 'w', encoding='utf-8') as file:
                    json.dump(profiles, file, ensure_ascii=False, indent=4)
                logger.info(f"Удален профиль пользователя {user_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка удаления профиля: {e}")
            return False

    def get_all_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Получение всех профилей"""
        try:
            with open(self.db_file, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            logger.error(f"Ошибка загрузки всех профилей: {e}")
            return {}

# Инициализация менеджера профилей
profile_manager = ProfileManager()

# Пример использования в хэндлерах:
# profile = profile_manager.load_profile(message.from_user.id)
# profile_manager.save_profile(message.from_user.id, new_data)
