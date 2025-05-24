import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os

from handlers import age_and_city, name, description, photo

# Загрузка переменных из .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("Токен бота не найден в .env!")

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())

# Подключение роутеров
routers = [
    name.router,
    age_and_city.router,
    description.router,
    photo.router
]

for router in routers:
    dp.include_router(router)

async def main():
    try:
        logger.info("Бот запущен...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception(f"Произошла ошибка: {e}")
    finally:
        await bot.session.close()
        logger.info("Бот остановлен.")

if __name__ == "__main__":
    asyncio.run(main())
