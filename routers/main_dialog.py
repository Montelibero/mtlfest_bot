import os

# Absolute path to the data directory
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
from datetime import datetime

from aiogram.enums import ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Window, Dialog, DialogManager
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Group, Checkbox, ManagedCheckbox, SwitchTo
from aiogram_dialog.widgets.media import StaticMedia
from aiogram_dialog.widgets.text import Format, Const
from loguru import logger

from config.bot_config import config
from database.database import update_user_data, get_user_data, get_last_key, add_scan_log
from database.qr_helpers import create_beautiful_code, decode_qr_code


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
    user_id = dialog_manager.event.from_user.id
    print(dialog_manager.middleware_data['aiogd_context'].state)
    if dialog_manager.middleware_data['aiogd_context'].state == MainStates.ticket_confirmation:
        user_data = await get_user_data(user_id)
    else:
        user_data = {}

    lang = data.get('lang', 'en')
    if lang == 'ru':
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
\n\nПодгорица, Черногорияв отеле Kings Park Hotel (https://maps.app.goo.gl/hKYJWZfxodnRRNcn7?g_st=ipc)
\n\nФестиваль ждёт вас с 12 часов. 
\n\n📢 Само открытие фестиваля — в 13:00
\n\nВстречаемся в отеле, знакомимся и начинаются первые лекции.
\n\nВечером после лекций — вечеринка в неформальной обстановке в уютном баре Богарт (https://maps.app.goo.gl/6Ns29oPRzqtRVc598?g_st=ipc)
\n\n📅 28 ноября – второй день.
\n\n🎤 Лекции и панельные дискуссии на английском языке
\n\n🌍 Темы: сообщества, предпринимательство, децентрализация, гражданские инициативы
\n\n🕐 С 12:00 до 19:00
\n\n🎉 Вечером — Afterparty Montelibero Fest, для тех, кто захочет вместе посидеть за одним столом и обсудить, что итнтересного узнали и какие выводы сделали.
\n\n🎟️ Участие
\n\nФестиваль бесплатный, по предварительной регистрации.
\n\nКоличество мест ограничено.
\n\n📢 Следите за обновлениями:
\n\nНовости и анонсы
\n\nпубликуются в Telegram-канале Montelibero Fest, (https://t.me/monteliberofestival) так же на сайте. (https://mtlfest.me/2025/ru)
\n\nЖдём вас! 🤗""",
            "support_text": "По все вопросам фестиваля вы можете написать в бот @mtlfest_support_bot "
                            "там вам ответят волонтеры, так быстро как только смогут.",
            "show_ticket_text": "Это твой бесплатный билет на основное мероприятие 5 октября. Его нужно будет показать на входе с экрана телефона или распечатать. Для участия в мероприятиях 4 и 6 октября требуется дополнительная регистрация, в разделе \"расписание\" в этом боте",
            "donate_button": "Донатить",
            "ticket_button": "Мой билет",
            "calendar_button": "Расписание",
            "support_button": "Поддержка",
            "back_button": "Назад",
            "ticket_start_text": "Я помогу зарегистрироваться на MTL FEST 2025. Нажми Start чтобы продолжить",
            "start_button": "Start",
            "ticket_country_text": "Нам нужно немного информации о тебе, чтобы сделать наши следующие ивенты лучше. "
                                   "В какой стране ты сейчас живешь?",
            "ticket_source_text": "Откуда ты узнал о фестивале?",
            "ticket_dates_text": "Выбери, пожалуйста, в какие дни ты бы хотел посетить мероприятия фестиваля. "
                                 "Это важно, чтобы мы планировали мероприятия с учетом вместимости площадок",
            "date_4_10": "4/10 кинотеатр",
            "date_5_10": "5/10 лекции",
            "date_6_10": "6/10 сити",
            "continue_button": "Продолжить",

            "TicketUUID": user_data.get("TicketUUID", None),
            "is_admin": user_id in config.admins
        }
    else:
        return {
            "welcome_text": "Welcome! I'm the MTL FEST 2025 assistant bot. Please choose an action:",
            "donate_text": "We make the event possible thanks to your donations.\n"
                           "Please help use any of possible ways: \n"
                           "<b>EURMTL | USDM | MTL| SATSMTL | XLM </b>\n"
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
\nPodgorica, Montenegro
\n\n      Gathering from 12 noon
\n\n📢 The festival itself opens at 1 p.m.
\n\n✨ Welcome session, introductions and first lectures
\n\n💬 Informal communication and evening networking
\n\nIn the evening after the lectures — a party in an informal setting at the cosy Bogart bar
\n\n📅 28 November — Second Festival Day
\n\n🎤 Lectures and panel discussions in English
\n\n🌍 Topics: communities, entrepreneurship, decentralisation, civic initiatives
\n\n🕐 From 12:00 to 21:00
\n\n🎉 In the evening — Montelibero Fest Afterparty, for those who want to sit down together and discuss what they have learned and what conclusions they have drawn.
\n\n🎟️ Participation
\n\nThe festival is free, but advance registration is required.
\n\nThe number of places is limited.
\n\n📢 Stay tuned for updates:
\n\nNews and announcements are published on the Montelibero Fest Telegram channel. """
                            "out via @mtlfest_support_bot. "
                            "Our volunteers will get back to you as soon as possible.",
            "show_ticket_text": "This is your free ticket to the main event on October, 5. You will need to show it at the gates for entrance on your mobile or printed. If you would like to attend other days of the festival please go to the website mtlfest.me/en and book them separately. Thank you",
            "donate_button": "Donate",
            "ticket_button": "My Ticket",
            "calendar_button": "Schedule",
            "support_button": "Support",
            "back_button": "Back",
            "ticket_start_text": "I'm here to help you register for MTL FEST 2024. Press Start to begin.",
            "start_button": "Start",
            "ticket_country_text": "We'd love to know a bit more about you to improve our future events. "
                                   "In which country are you currently residing?",
            "ticket_source_text": "How did you hear about the festival?",
            "ticket_dates_text": "Please select the days you'd like to attend the festival events. "
                                 "This helps us plan according to venue capacity.",
            "date_4_10": "October 4th - Cinema",
            "date_5_10": "October 5th - Lectures",
            "date_6_10": "October 6th - City Tour",
            "continue_button": "Continue",
            "TicketUUID": user_data.get("TicketUUID", None),
            "is_admin": user_id in config.admins
        }
    logger.info("Exiting: get_start_data")


async def on_button_clicked(c: CallbackQuery, button: Button, manager: DialogManager):
    logger.info("Entering: on_button_clicked")
    if button.widget_id == "ticket_start":
        user_id = c.from_user.id
        user_data = await get_user_data(user_id)
        if user_data and user_data.get("TicketUUID", None):
            await manager.switch_to(MainStates.ticket_confirmation)
            logger.info("Exiting: on_button_clicked (user has ticket)")
            return
        else:
            async with config.lock:
                data = {"TicketDate": datetime.utcnow(),
                        "TicketUUID": uuid.uuid4().hex,
                        "TicketKey": await get_last_key()
                        }
                await update_user_data(user_id, data)
            file_path = os.path.join(DATA_DIR, f'{data["TicketUUID"]}.png')
            logger.info(f"Creating QR code at: {file_path}")
            create_beautiful_code(file_path, data["TicketUUID"], "MTLFEST" + data["TicketKey"])
            await manager.switch_to(MainStates.ticket_confirmation)
            logger.info("Exiting: on_button_clicked (new ticket created)")
            return

    await manager.switch_to(getattr(MainStates, button.widget_id))
    logger.info("Exiting: on_button_clicked")


main_button_group = Group(
    Button(Format("{donate_button}"), id="donate", on_click=on_button_clicked),
    Button(Format("{ticket_button}"), id="ticket_start", on_click=on_button_clicked),
    Button(Format("{calendar_button}"), id="calendar", on_click=on_button_clicked),
    Button(Format("{support_button}"), id="support", on_click=on_button_clicked),
    width=2)


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
    getter=get_start_data
)


async def mh_process_country(message: Message, widget: MessageInput, dialog_manager: DialogManager) -> None:
    logger.info("Entering: mh_process_country")
    user_id = message.from_user.id
    await update_user_data(user_id, {"Country": message.text})
    await dialog_manager.switch_to(MainStates.ticket_source)
    logger.info("Exiting: mh_process_country")


window_ticket_country = Window(
    Format("{ticket_country_text}"),
    MessageInput(
        func=mh_process_country,
        content_types=ContentType.TEXT,
    ),
    state=MainStates.ticket_country,
    getter=get_start_data
)


async def mh_process_source(message: Message, widget: MessageInput, dialog_manager: DialogManager) -> None:
    logger.info("Entering: mh_process_source")
    user_id = message.from_user.id
    await update_user_data(user_id, {"Source": message.text})
    await dialog_manager.switch_to(MainStates.ticket_dates)
    logger.info("Exiting: mh_process_source")


window_ticket_source = Window(
    Format("{ticket_source_text}"),
    MessageInput(
        func=mh_process_source,
        content_types=ContentType.TEXT,
    ),
    state=MainStates.ticket_source,
    getter=get_start_data
)

async def mh_process_qr(message: Message, widget: MessageInput, dialog_manager: DialogManager) -> None:
    logger.info("Entering: mh_process_qr")
    admin_id = message.from_user.id
    #await update_user_data(user_id, {"LastEnterDate": datetime.utcnow()})
    logger.info(f'{message.from_user.id}')
    if message.photo:
        await message.reply('is being recognized')
        await message.bot.download(message.photo[-1], destination=os.path.join(DATA_DIR, f'{message.from_user.id}.jpg'))

        qr_data = decode_qr_code(os.path.join(DATA_DIR, f'{message.from_user.id}.jpg'))
        # decode(Image.open(f"qr/{message.from_user.id}.jpg"))
        if qr_data:
            logger.info(qr_data)

            user_data = await get_user_data(0, qr_data)
            if user_data:
                user_id = user_data.get("UserID")
                await update_user_data(user_id, {"LastEnterDate": datetime.utcnow()})
                await message.reply(f'Успешно ! Можете присылать новый код ! или выйти в главное меню /start ')
                await add_scan_log(admin_id=admin_id, user_id=user_id)

            else:
                await message.reply('Bad QR code =( or user not found')
        else:
            await message.reply('Bad QR code =(')
    logger.info("Exiting: mh_process_qr")



window_qr_scan = Window(
    Const("Сканируйте QR-код"),
    MessageInput(
        func=mh_process_qr,
        content_types=ContentType.PHOTO,
    ),
    state=MainStates.ticket_scan,
    #getter=get_start_data
)


async def on_date_selected(c: CallbackQuery, checkbox: ManagedCheckbox, manager: DialogManager):
    logger.info("Entering: on_date_selected")
    manager.dialog_data[checkbox.widget_id] = checkbox.is_checked()
    logger.info("Exiting: on_date_selected")


async def on_dates_confirmed(c: CallbackQuery, button: Button, manager: DialogManager):
    logger.info("Entering: on_dates_confirmed")
    user_id = c.from_user.id
    async with config.lock:
        data = {"date_4_10": manager.dialog_data.get("date_4_10", False),
                "date_5_10": manager.dialog_data.get("date_5_10", False),
                "date_6_10": manager.dialog_data.get("date_6_10", False),
                #        "TicketDate": datetime.utcnow(),
                #        "TicketUUID": uuid.uuid4().hex,
                #        "TicketKey": await get_last_key()
                }
        await update_user_data(user_id, data)

    # create_beautiful_code(f'./data/{data["TicketUUID"]}.png', data["TicketUUID"], "MTLFEST" + data["TicketKey"])

    await manager.switch_to(MainStates.ticket_confirmation)
    logger.info("Exiting: on_dates_confirmed")


window_ticket_dates = Window(
    Format("{ticket_dates_text}"),
    Group(
        Checkbox(
            checked_text=Format("[✅] {date_4_10}"),
            unchecked_text=Format("[  ] {date_4_10}"),
            id="date_4_10",
            on_state_changed=on_date_selected
        ),
        Checkbox(
            checked_text=Format("[✅] {date_5_10}"),
            unchecked_text=Format("[  ] {date_5_10}"),
            id="date_5_10",
            on_state_changed=on_date_selected
        ),
        Checkbox(
            checked_text=Format("[✅] {date_6_10}"),
            unchecked_text=Format("[  ] {date_6_10}"),
            id="date_6_10",
            on_state_changed=on_date_selected
        ),
    ),
    Button(Format("{continue_button}"), id="confirm_dates", on_click=on_dates_confirmed),
    state=MainStates.ticket_dates,
    getter=get_start_data
)

window_ticket_image = Window(
    # DynamicMedia( #DynamicMedia
    #     path="path/to/your/image.jpg"
    # ),
    StaticMedia(
        path=Format(os.path.join(DATA_DIR, '{TicketUUID}.png')),
        type=ContentType.PHOTO
    ),
    Format("{show_ticket_text}"),
    Button(Format("{back_button}"), id="start", on_click=on_button_clicked),
    state=MainStates.ticket_confirmation,
    getter=get_start_data
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
    window_qr_scan
)