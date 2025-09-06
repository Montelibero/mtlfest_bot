import os
from datetime import datetime

import asyncio
from aiogram import Router, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, FSInputFile
from aiogram_dialog import DialogManager, StartMode
from loguru import logger

from config.bot_config import config
from database.database import (
    update_user_data,
    get_user_data,
    delete_user_data,
    add_log,
    export_utm_to_csv,
    export_tickets_to_csv,
    get_user_ids,
    add_admin_id,
)
from routers import main_dialog

router = Router()


@router.message(CommandStart())
async def command_start_handler(
    message: Message,
    dialog_manager: DialogManager,
    state: FSMContext,
    command: CommandObject,
) -> None:
    logger.info("Entering: command_start_handler")
    user_id = message.from_user.id
    user_data = await get_user_data(user_id)

    # Capture start command arguments
    start_args = command.args
    utm_data = {}

    # Parse UTM parameters
    if start_args:
        params = start_args.split()
        for param in params:
            if param.startswith('utm_'):
                utm_data = param

    # Update user data
    update_data = {}
    if not user_data or not user_data.get("StartDate"):
        update_data["StartDate"] = datetime.utcnow()

    update_data["Lang"] = message.from_user.language_code

    # Add UTM data if present
    if utm_data:
        update_data["utm"] = utm_data
        await add_log("utm", {"user_id": user_id, "utm_data": utm_data})

    # Update database
    await update_user_data(user_id, update_data)

    # Update state
    await state.update_data(lang=message.from_user.language_code)

    # Start dialog
    await dialog_manager.start(main_dialog.MainStates.start, mode=StartMode.RESET_STACK)
    logger.info("Exiting: command_start_handler")


@router.message(Command(commands=["change_lang"]))
async def cmd_change_lang(
    message: Message,
    state: FSMContext,
    dialog_manager: DialogManager,
):
    logger.info("Entering: cmd_change_lang")
    data = await state.get_data()
    lang = 'en' if data.get('lang') == 'ru' else 'ru'
    await message.answer(f"Язык изменен на {lang}")
    await state.update_data(lang=lang)
    await dialog_manager.start(main_dialog.MainStates.start, mode=StartMode.RESET_STACK)
    logger.info("Exiting: cmd_change_lang")


@router.message(Command(commands=["delete_data"]))
async def cmd_delete_data(
    message: Message,
    state: FSMContext,
    dialog_manager: DialogManager,
):
    logger.info("Entering: cmd_delete_data")
    user_id = message.from_user.id
    await delete_user_data(user_id)
    await message.answer(
        "Все ваши данные были успешно удалены. Начнем сначала. /start \n"
        "Обязательно нажмите старт иначе могут быть странные глюки"
    )
    logger.info("Exiting: cmd_delete_data")


@router.message(Command("export_utm"), F.chat.id.in_((-1002167206567, 84131737)))
async def cmd_export_utm(message: Message, state: FSMContext):
    logger.info("Entering: cmd_export_utm")
    await export_utm_to_csv()
    filename = 'data/output.csv'
    if os.path.isfile(filename):
        await message.reply_document(FSInputFile(filename))
    logger.info("Exiting: cmd_export_utm")


@router.message(Command("export_tickets"), F.chat.id.in_((-1002167206567, 84131737)))
async def cmd_export_tickets(message: Message, state: FSMContext):
    logger.info("Entering: cmd_export_tickets")
    await export_tickets_to_csv()
    filename = 'data/output.csv'
    if os.path.isfile(filename):
        await message.reply_document(FSInputFile(filename))
    logger.info("Exiting: cmd_export_tickets")


class ExitState(StatesGroup):
    need_exit = State()


@router.message(Command(commands=["exit"]))
@router.message(Command(commands=["restart"]))
async def cmd_exit(message: Message, state: FSMContext):
    logger.info("Entering: cmd_exit")
    my_state = await state.get_state()
    if message.from_user.username == "itolstov":
        if my_state == ExitState.need_exit:
            await state.set_state(None)
            await message.reply("Chao :[[[")
            exit()
        else:
            await state.set_state(ExitState.need_exit)
            await message.reply(": '['")
    logger.info("Exiting: cmd_exit")


@router.message(Command("send"), F.chat.id.in_((-1002167206567, 84131737)))
async def cmd_send(message: Message, state: FSMContext):
    logger.info("Entering: cmd_send")
    # Split the message text into command and arguments
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await message.reply("Error: No argument provided.")
        logger.info("Exiting: cmd_send (no argument)")
        return

    # Check if the command is in reply to a message
    if not message.reply_to_message:
        await message.reply("Error: This command must be used in reply to a message.")
        logger.info("Exiting: cmd_send (not a reply)")
        return

    arg = command_parts[1]

    if arg.isdigit():
        # Send to specific user ID
        try:
            await message.reply_to_message.copy_to(chat_id=int(arg))
            await message.reply(f"Message sent to user ID: {arg}")
        except Exception as e:
            await message.reply(f"Error sending message: {str(e)}")
    elif arg.lower() in ["all", "en", "ru"]:
        # Send to all users
        all_users = await get_user_ids(arg.lower())
        success_count = 0
        for user_id in all_users:
            try:
                await message.reply_to_message.copy_to(chat_id=user_id)
                success_count += 1
                await asyncio.sleep(0.3)
            except Exception:
                pass
        await message.reply(f"Message sent to {success_count} out of {len(all_users)} users.")
    else:
        await message.reply("Error: Invalid argument. Use a user ID or 'all'.")
    logger.info("Exiting: cmd_send")


@router.message(Command("add"), F.chat.id.in_((-1002167206567, 84131737)))
async def cmd_add(message: Message, state: FSMContext):
    logger.info("Entering: cmd_add")
    # Split the message text into command and arguments
    command_parts = message.text.split(maxsplit=1)
    admin_id = int(command_parts[1])
    config.admins.append(admin_id)
    await add_admin_id(admin_id)
    await message.reply(f"{admin_id} added to admins")
    logger.info("Exiting: cmd_add")
