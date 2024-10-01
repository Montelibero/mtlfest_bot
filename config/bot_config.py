import asyncio
import os

from aiogram import Bot
from dotenv import load_dotenv

load_dotenv()


class Config:
    if os.getenv('ENVIRONMENT', 'test') == 'production':
        TEST_MODE: bool = False
        BOT_TOKEN = os.getenv("BOT_TOKEN")
    else:
        TEST_MODE: bool = True
        BOT_TOKEN = os.getenv("TEST_BOT_TOKEN")

    if not BOT_TOKEN:
        raise ValueError("Не задан токен бота. Убедитесь, что в файле .env есть переменная BOT_TOKEN.")

    MONGO_URI = os.getenv("MONGO_URI")
    if not MONGO_URI:
        raise ValueError("Не задан URI для MongoDB. Убедитесь, что в файле .env есть переменная MONGO_URI.")

    SENTRY_DSN = os.getenv("SENTRY_DSN")

    # Другие настройки
    REDIS_URL = "redis://localhost:6379/1"

    bot: Bot = None
    lock = asyncio.Lock()


config = Config()
