import os
from datetime import datetime
from typing import Any
from uuid import uuid4

from aiogram.enums import ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.api.entities import ChatEvent
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Checkbox, Group, ManagedCheckbox, SwitchTo
from aiogram_dialog.widgets.media import StaticMedia
from aiogram_dialog.widgets.text import Const, Format
from loguru import logger

from config.bot_config import config
from database.database import add_scan_log, get_last_key, get_user_data, update_user_data
from database.qr_helpers import create_beautiful_code, decode_qr_code

# Absolute path to the data directory
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)


def _get_ticket_info(user_data: dict[str, Any], season: str) -> dict[str, Any]:
    tickets = user_data.get("tickets") if user_data else None
    if isinstance(tickets, dict):
        return tickets.get(season, {}) or {}
    return {}


def _find_ticket_season(user_data: dict[str, Any], ticket_uuid: str) -> str | None:
    tickets = user_data.get("tickets") if user_data else None
    season = config.CURRENT_TICKET_SEASON
    if isinstance(tickets, dict):
        info = tickets.get(season)
        if isinstance(info, dict) and info.get("uuid") == ticket_uuid:
            return season
    return None


def _ensure_ticket_qr(ticket_uuid: str | None, ticket_key: str | None) -> str | None:
    if not ticket_uuid or not ticket_key:
        return None
    file_path = os.path.join(DATA_DIR, f"{ticket_uuid}.png")
    if not os.path.exists(file_path):
        logger.info("Regenerating QR code for ticket %s", ticket_uuid)
        create_beautiful_code(file_path, ticket_uuid, "MTLFEST" + ticket_key)
    return file_path


class MainStates(StatesGroup):
    start = State()
    donate = State()
    support = State()
    calendar = State()
    ticket_start = State()
    ticket_country = State()
    ticket_source = State()
    ticket_dates = State()
    ticket_confirmation = State()
    ticket_scan = State()


async def get_start_data(dialog_manager: DialogManager, state: FSMContext, **kwargs):
    logger.info("Entering: get_start_data")
    data = await state.get_data()
    user_id = dialog_manager.event.from_user.id  # type: ignore[union-attr]
    current_state = dialog_manager.middleware_data["aiogd_context"].state
    user_data = await get_user_data(user_id)

    season = config.CURRENT_TICKET_SEASON
    ticket_info = _get_ticket_info(user_data or {}, season)
    ticket_uuid = ticket_info.get("uuid")
    ticket_key = ticket_info.get("key")
    _ensure_ticket_qr(ticket_uuid, ticket_key)

    dates_selected = ticket_info.get("dates", {}) if isinstance(ticket_info, dict) else {}
    if current_state == MainStates.ticket_dates:
        dialog_manager.dialog_data.update(
            {
                "date_27_11": dates_selected.get("date_27_11", False),
                "date_28_11": dates_selected.get("date_28_11", False),
            }
        )

    lang = data.get("lang", "en")
    if lang == "ru":
        return {
            "welcome_text": "Добро пожаловать! Я бот-помощник фестиваля. Выберите действие:",
            "donate_text": "Наше мероприятие возможно только благодаря вашим пожертвованиям. \n"
            "Пожалуйста, помогайте нам любым удобным способом: \n"
            "<b>EURMTL | USDM | MTL| SATSMTL | XLM </b>\n"
            "<code>GBJ4BPR6WESHII6TO4ZUQBB6NJD3NBTK5LISVNKXMPOMMYSLR5DOXMFD</code>\n"
            "<b>BTC</b>\n"
            "<code>bc1qkyevfyq052dfx3jtlelulz3t2gvkq9jtpsee5m</code>\n"
            "<b>ETH</b>\n"
            "<code>0x7fB2369504ab724A3E5fBBe55C87A0B708B8C672</code>\n"
            "<b>USDT (trc20)</b>\n"
            "<code>TBRsYzKKNxM6jjyD3d1Adva2TbgkiAMLux</code>\n"
            "<b>Monero</b>\n"
            "<code>43RMnD3EDcHHL39eJPRqqDYhU9cWdGKABA3fetY8FNZwUQ9PNPGoxbZNSEaYKHYzeJMq2BsLpzrbhWCF7aueH4Tn7kTV7Pw</code>\n\n",
            "calendar_text": """🎉 Основная программа Monteliber.Zaedno Fest 2025
\n\n📅 27 ноября — открытие фестиваля
\n\nПодгорица, Черногория в отеле <a href="https://maps.app.goo.gl/hKYJWZfxodnRRNcn7?g_st=ipc">Kings Park Hotel</a>
\nФестиваль ждёт вас с 12 часов.
\n📢 Само открытие фестиваля — в 13:00
\nВстречаемся в отеле, знакомимся и начинаются первые лекции.
\nВечером после лекций — вечеринка в неформальной обстановке в уютном баре <a href="https://maps.app.goo.gl/6Ns29oPRzqtRVc598?g_st=ipc">Богарт</a>
\n\n📅 28 ноября – второй день.
\n\n🎤 Лекции и панельные дискуссии на английском языке
\n🌍 Темы: сообщества, предпринимательство, децентрализация, гражданские инициативы
\n🕐 С 12:00 до 19:00
\n🎉 Вечером — Afterparty Montelibero Fest, для тех, кто захочет вместе посидеть за одним столом и обсудить, что итнтересного узнали и какие выводы сделали.
\n\n🎟️ Участие
\n\nФестиваль бесплатный, по предварительной регистрации.
\nКоличество мест ограничено.
\n📢 Следите за обновлениями:
\nНовости и анонсы
\nпубликуются в Telegram-канале <a href="https://t.me/monteliberofestival">Montelibero Fest</a>, так же на <a href="https://mtlfest.me/2025/ru">сайте</a>.
\nЖдём вас! 🤗""",
            "support_text": "По всем вопросам фестиваля можно написать в @mtlfest_support_bot — волонтёры ответят как можно быстрее.",
            "show_ticket_text": "Это твой бесплатный билет на Monteliber.Zaedno Fest 27–28 ноября 2025. Покажи QR на входе с телефона или распечатай его. Если планы изменились — дай знать команде поддержки.",
            "donate_button": "Донатить",
            "ticket_button": "Мой билет",
            "calendar_button": "Расписание",
            "support_button": "Поддержка",
            "back_button": "Назад",
            "ticket_start_text": "Я помогу зарегистрироваться на Monteliber.Zaedno Fest 2025. Нажми Start, чтобы начать.",
            "start_button": "Start",
            "ticket_country_text": "Нам нужно немного информации, чтобы подготовить площадку. В какой стране ты сейчас живёшь?",
            "ticket_source_text": "Расскажи, откуда узнал о фестивале?",
            "ticket_dates_text": "Выбери дни, когда планируешь прийти. Это поможет нам рассчитать нагрузку на площадку.",
            "date_27_11": "27 ноября — открытие и воркшопы",
            "date_28_11": "28 ноября — лекции и afterparty",
            "continue_button": "Продолжить",
            "TicketUUID": ticket_uuid,
            "TicketKey": ticket_key,
            "is_admin": user_id in config.admins,
        }
    else:
        return {
            "welcome_text": "Welcome! I'm the Monteliber.Zaedno Fest assistant bot. Choose an option:",
            "donate_text": "We run this festival thanks to your donations.\n"
            "Please support us in any of the available ways: \n"
            "<b>EURMTL | USDM | MTL | SATSMTL | XLM</b>\n"
            "<code>GBJ4BPR6WESHII6TO4ZUQBB6NJD3NBTK5LISVNKXMPOMMYSLR5DOXMFD</code>\n"
            "<b>BTC</b>\n"
            "<code>bc1qkyevfyq052dfx3jtlelulz3t2gvkq9jtpsee5m</code>\n"
            "<b>ETH</b>\n"
            "<code>0x7fB2369504ab724A3E5fBBe55C87A0B708B8C672</code>\n"
            "<b>USDT (trc20)</b>\n"
            "<code>TBRsYzKKNxM6jjyD3d1Adva2TbgkiAMLux</code>\n"
            "<b>Monero</b>\n"
            "<code>43RMnD3EDcHHL39eJPRqqDYhU9cWdGKABA3fetY8FNZwUQ9PNPGoxbZNSEaYKHYzeJMq2BsLpzrbhWCF7aueH4Tn7kTV7Pw</code>\n",
            "calendar_text": """🎉 Main programme of Monteliber.Zaedno Fest 2025
\n\n📅 27 November — Opening Day
\n\nWelcome session, introductions and first lectures
\nPodgorica, Montenegro at <a href="https://maps.app.goo.gl/hKYJWZfxodnRRNcn7?g_st=ipc">Kings Park Hotel</a>
\nGathering from 12:00
\n📢 The festival itself opens at 13:00
\n✨ Welcome session, introductions and first lectures
\n💬 Informal communication and evening networking
\nIn the evening after the lectures — a party in an informal setting at the cosy <a href="https://maps.app.goo.gl/6Ns29oPRzqtRVc598?g_st=ipc">Bogart bar</a>
\n\n📅 28 November — Second Festival Day
\n\n🎤 Lectures and panel discussions in English
\n🌍 Topics: communities, entrepreneurship, decentralisation, civic initiatives
\n🕐 From 12:00 to 19:00
\n🎉 In the evening — Montelibero Fest Afterparty, for those who want to sit down together and discuss what they have learned and what conclusions they have drawn.
\n\n🎟️ Participation
\n\nThe festival is free, but advance registration is required.
\nThe number of places is limited.
\n📢 Stay tuned for updates:
\nNews and announcements are published on the <a href="https://t.me/monteliberofestival">Montelibero Fest Telegram channel</a> and on the <a href="https://mtlfest.me/2025/en">website</a>. """
            "out via @mtlfest_support_bot. "
            "Our volunteers will get back to you as soon as possible.",
            "support_text": "For any questions message @mtlfest_support_bot — volunteers will reply as soon as possible.",
            "show_ticket_text": "This is your free ticket to the main event on October, 5. You will need to show it at the gates for entrance on your mobile or printed. If you would like to attend other days of the festival please go to the website mtlfest.me/en and book them separately. Thank you",
            "donate_button": "Donate",
            "ticket_button": "My Ticket",
            "calendar_button": "Schedule",
            "support_button": "Support",
            "back_button": "Back",
            "ticket_start_text": "I'm here to help you register for Monteliber.Zaedno Fest 2025. Press Start to begin.",
            "start_button": "Start",
            "ticket_country_text": "We'd love to know where you're based right now to plan better. Which country are you currently in?",
            "ticket_source_text": "How did you hear about the festival?",
            "ticket_dates_text": "Pick the days you plan to attend so we can manage venue capacity.",
            "date_27_11": "27 November — Opening & workshops",
            "date_28_11": "28 November — Lectures & afterparty",
            "continue_button": "Continue",
            "TicketUUID": ticket_uuid,
            "TicketKey": ticket_key,
            "is_admin": user_id in config.admins,
        }
    logger.info("Exiting: get_start_data")


async def on_button_clicked(c: CallbackQuery, button: Button, manager: DialogManager):
    logger.info("Entering: on_button_clicked")
    if button.widget_id == "ticket_start":
        user_id = c.from_user.id
        user_data = await get_user_data(user_id)
        season = config.CURRENT_TICKET_SEASON
        ticket_info = _get_ticket_info(user_data or {}, season)
        ticket_uuid = ticket_info.get("uuid")
        if ticket_uuid:
            await manager.switch_to(MainStates.ticket_confirmation)
            logger.info("Exiting: on_button_clicked (user has ticket)")
            return
        else:
            async with config.lock:
                ticket_uuid = uuid4().hex
                ticket_key = await get_last_key()
                created_at = datetime.utcnow()
                await update_user_data(
                    user_id,
                    {
                        f"tickets.{season}.uuid": ticket_uuid,
                        f"tickets.{season}.key": ticket_key,
                        f"tickets.{season}.created_at": created_at,
                    },
                )
            logger.info("Generated ticket %s for user %s", ticket_uuid, user_id)
            _ensure_ticket_qr(ticket_uuid, ticket_key)
            # questionnaire on
            await manager.switch_to(MainStates.ticket_start)
            # questionnaire off
            # await manager.switch_to(MainStates.ticket_confirmation)
            logger.info("Exiting: on_button_clicked (new ticket created)")
            return

    await manager.switch_to(getattr(MainStates, button.widget_id or ""))
    logger.info("Exiting: on_button_clicked")


main_button_group = Group(
    Button(Format("{donate_button}"), id="donate", on_click=on_button_clicked),
    Button(Format("{ticket_button}"), id="ticket_start", on_click=on_button_clicked),
    Button(Format("{calendar_button}"), id="calendar", on_click=on_button_clicked),
    Button(Format("{support_button}"), id="support", on_click=on_button_clicked),
    width=2,
)


window_start = Window(
    Format("{welcome_text}"),
    main_button_group,
    SwitchTo(Const("Scan QR"), id="scan_qr", state=MainStates.ticket_scan, when="is_admin"),
    state=MainStates.start,
    getter=get_start_data,
    disable_web_page_preview=True,
)
window_donate = Window(
    Format("{donate_text}"),
    main_button_group,
    state=MainStates.donate,
    getter=get_start_data,
    disable_web_page_preview=True,
)

window_calendar = Window(
    Format("{calendar_text}"),
    main_button_group,
    state=MainStates.calendar,
    getter=get_start_data,
    disable_web_page_preview=True,
)

window_support = Window(
    Format("{support_text}"),
    main_button_group,
    state=MainStates.support,
    getter=get_start_data,
    disable_web_page_preview=True,
)

window_ticket_start = Window(
    Format("{ticket_start_text}"),
    Button(Format("{start_button}"), id="ticket_country", on_click=on_button_clicked),
    state=MainStates.ticket_start,
    getter=get_start_data,
)


async def mh_process_country(message: Message, widget: MessageInput, dialog_manager: DialogManager) -> None:
    logger.info("Entering: mh_process_country")
    user_id = message.from_user.id  # type: ignore[union-attr]
    season = config.CURRENT_TICKET_SEASON
    await update_user_data(user_id, {f"tickets.{season}.questionnaire.country": message.text})
    await dialog_manager.switch_to(MainStates.ticket_source)
    logger.info("Exiting: mh_process_country")


window_ticket_country = Window(
    Format("{ticket_country_text}"),
    MessageInput(
        func=mh_process_country,
        content_types=ContentType.TEXT,
    ),
    state=MainStates.ticket_country,
    getter=get_start_data,
)


async def mh_process_source(message: Message, widget: MessageInput, dialog_manager: DialogManager) -> None:
    logger.info("Entering: mh_process_source")
    user_id = message.from_user.id  # type: ignore[union-attr]
    season = config.CURRENT_TICKET_SEASON
    await update_user_data(user_id, {f"tickets.{season}.questionnaire.source": message.text})
    await dialog_manager.switch_to(MainStates.ticket_dates)
    logger.info("Exiting: mh_process_source")


window_ticket_source = Window(
    Format("{ticket_source_text}"),
    MessageInput(
        func=mh_process_source,
        content_types=ContentType.TEXT,
    ),
    state=MainStates.ticket_source,
    getter=get_start_data,
)


async def mh_process_qr(message: Message, widget: MessageInput, dialog_manager: DialogManager) -> None:
    logger.info("Entering: mh_process_qr")
    assert message.from_user is not None
    assert message.bot is not None
    admin_id = message.from_user.id
    # await update_user_data(user_id, {"LastEnterDate": datetime.utcnow()})
    logger.info(f"{message.from_user.id}")
    if message.photo:
        await message.reply("is being recognized")
        await message.bot.download(
            message.photo[-1], destination=os.path.join(DATA_DIR, f"{message.from_user.id}.jpg")
        )

        qr_data = decode_qr_code(os.path.join(DATA_DIR, f"{message.from_user.id}.jpg"))
        # decode(Image.open(f"qr/{message.from_user.id}.jpg"))
        if qr_data:
            logger.info(qr_data)

            user_data = await get_user_data(0, qr_data)
            if user_data:
                user_id = user_data.get("UserID")
                season = _find_ticket_season(user_data, qr_data)
                if season:
                    await update_user_data(user_id, {f"tickets.{season}.last_scanned_at": datetime.utcnow()})
                await message.reply("Успешно ! Можете присылать новый код ! или выйти в главное меню /start ")
                await add_scan_log(admin_id=admin_id, user_id=user_id)

            else:
                await message.reply("Bad QR code =( or user not found")
        else:
            await message.reply("Bad QR code =(")
    logger.info("Exiting: mh_process_qr")


window_qr_scan = Window(
    Const("Сканируйте QR-код"),
    MessageInput(
        func=mh_process_qr,
        content_types=ContentType.PHOTO,
    ),
    state=MainStates.ticket_scan,
    # getter=get_start_data
)


async def on_date_selected(event: ChatEvent, checkbox: ManagedCheckbox, manager: DialogManager):
    logger.info("Entering: on_date_selected")
    manager.dialog_data[checkbox.widget_id] = checkbox.is_checked()
    logger.info("Exiting: on_date_selected")


async def on_dates_confirmed(c: CallbackQuery, button: Button, manager: DialogManager):
    logger.info("Entering: on_dates_confirmed")
    user_id = c.from_user.id
    season = config.CURRENT_TICKET_SEASON
    async with config.lock:
        data = {
            f"tickets.{season}.dates.date_27_11": manager.dialog_data.get("date_27_11", False),
            f"tickets.{season}.dates.date_28_11": manager.dialog_data.get("date_28_11", False),
        }
        await update_user_data(user_id, data)

    await manager.switch_to(MainStates.ticket_confirmation)
    logger.info("Exiting: on_dates_confirmed")


window_ticket_dates = Window(
    Format("{ticket_dates_text}"),
    Group(
        Checkbox(
            checked_text=Format("[✅] {date_27_11}"),
            unchecked_text=Format("[  ] {date_27_11}"),
            id="date_27_11",
            on_state_changed=on_date_selected,
        ),
        Checkbox(
            checked_text=Format("[✅] {date_28_11}"),
            unchecked_text=Format("[  ] {date_28_11}"),
            id="date_28_11",
            on_state_changed=on_date_selected,
        ),
    ),
    Button(Format("{continue_button}"), id="confirm_dates", on_click=on_dates_confirmed),
    state=MainStates.ticket_dates,
    getter=get_start_data,
)

window_ticket_image = Window(
    # DynamicMedia( #DynamicMedia
    #     path="path/to/your/image.jpg"
    # ),
    StaticMedia(
        path=Format(os.path.join(DATA_DIR, "{TicketUUID}.png")), type=ContentType.PHOTO, when="TicketUUID"
    ),
    Format("{show_ticket_text}"),
    Button(Format("{back_button}"), id="start", on_click=on_button_clicked),
    state=MainStates.ticket_confirmation,
    getter=get_start_data,
)

dialog = Dialog(
    window_start,
    window_donate,
    window_calendar,
    window_support,
    window_ticket_start,
    window_ticket_country,
    window_ticket_source,
    window_ticket_dates,
    window_ticket_image,
    window_qr_scan,
)
