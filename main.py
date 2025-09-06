import asyncio
from contextlib import suppress

import sentry_sdk
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault, BotCommandScopeAllPrivateChats
from aiogram_dialog.setup import setup_dialogs
from loguru import logger

from config.bot_config import config
from database.database import get_admins_list
from routers import admin, main_dialog


async def set_commands(bot: Bot):
    commands_clear = []
    commands_private = [
        BotCommand(
            command="start",
            description="Start or ReStart bot",
        )
    ]
    commands_private_me = [
        BotCommand(
            command="start",
            description="Start or ReStart bot",
        ),
        BotCommand(
            command="restart",
            description="ReStart bot",
        )
    ]
    commands_private_ru = [
        BotCommand(
            command="start",
            description="Начать с начала",
        )
    ]

    await bot.set_my_commands(commands=commands_clear, scope=BotCommandScopeDefault())
    await bot.set_my_commands(commands=commands_private, scope=BotCommandScopeAllPrivateChats())
    await bot.set_my_commands(commands=commands_private_ru, scope=BotCommandScopeAllPrivateChats(), language_code='ru')
    await bot.set_my_commands(commands=commands_private_me, scope=BotCommandScopeChat(chat_id=84131737))


async def on_startup(bot: Bot, dispatcher: Dispatcher):
    await set_commands(bot)
    config.admins = await get_admins_list()
    with suppress(TelegramBadRequest):
        await bot.send_message(chat_id=84131737, text='Bot started')
    if config.TEST_MODE:
        logger.info("Test mode")


async def main():
    storage = RedisStorage.from_url(url=config.REDIS_URL,
                                    key_builder=DefaultKeyBuilder(with_bot_id=True, with_destiny=True))
    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
    config.bot = bot
    dp = Dispatcher(storage=storage)
    dp.startup.register(on_startup)

    dp.include_router(admin.router)
    dp.include_router(main_dialog.dialog)

    setup_dialogs(dp)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == '__main__':
    logger.add("mtlfest_bot.log", rotation="1 MB", level='INFO')
    sentry_sdk.init(
        dsn=config.SENTRY_DSN,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )
    asyncio.run(main())
