"""MongoDB collection schemas used by the bot.

Collections
-----------
users
    Telegram profile-centric document keyed by ``UserID``. Structure is a flat dict; typical shape::

        {
            "UserID": int,             # Telegram ID (primary key)
            "Lang": str,               # 'ru' | 'en'
            "StartDate": datetime,     # first /start usage
            "utm": str,                # optional marketing tag
            "TicketUUID": str,         # hex ticket identifier
            "TicketDate": datetime,    # ticket creation timestamp
            "TicketKey": str,          # zero-padded numeric code
            "Country": str,            # questionnaire answer
            "Source": str,             # questionnaire answer
            "date_4_10": bool,
            "date_5_10": bool,
            "date_6_10": bool,
            "LastEnterDate": datetime  # last QR scan
        }

    Fields are added lazily via ``update_user_data``, so older records may miss keys.
config

    Key-value collection for operational state. Known keys: ``LastTicketKey`` (tracks the
    last numeric ticket suffix), ``Admins`` (array of privileged user IDs) and ``ScanLog``
    (array of scan audit entries with ``admin_id``, ``user_id``, ``scanned_at``).
logs
    Event log with documents shaped as ``{"timestamp": datetime, "action": str,
    "details": dict}``. Used for UTM tracking and other append-only audit records.
"""

import asyncio
from datetime import datetime

import aiofiles
from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger

from config.bot_config import config

client = AsyncIOMotorClient(config.MONGO_URI)
db = client.FEST

users_collection = db.users
config_collection = db.config
logs_collection = db.logs


async def get_user_data(user_id, ticket_key=None):
    logger.info(f"Entering: get_user_data(user_id={user_id}, ticket_key={ticket_key})")
    if ticket_key:
        result = await users_collection.find_one({"TicketUUID": ticket_key})
    else:
        result = await users_collection.find_one({"UserID": user_id})
    logger.info(f"Exiting: get_user_data")
    return result


async def update_user_data(user_id, data):
    logger.info(f"Entering: update_user_data(user_id={user_id}, data={data})")
    await users_collection.update_one(
        {"UserID": user_id},
        {"$set": data},
        upsert=True
    )
    logger.info(f"Exiting: update_user_data")


async def get_last_key() -> str:
    logger.info(f"Entering: get_last_key")
    last_key = await config_collection.find_one({"Key": "LastTicketKey"})
    if last_key is None:
        start_key = 11
    else:
        start_key = last_key.get("Value", 11)

    while True:
        ticket_key = f"{start_key:03d}"
        existing_user = await users_collection.find_one({"TicketKey": ticket_key})
        if existing_user is None:
            # Обновляем LastTicketKey перед возвратом
            await config_collection.update_one(
                {"Key": "LastTicketKey"},
                {"$set": {"Value": start_key}},
                upsert=True
            )
            logger.info(f"Exiting: get_last_key with key {ticket_key}")
            return ticket_key
        start_key += 1


async def delete_user_data(user_id: int):
    logger.info(f"Entering: delete_user_data(user_id={user_id})")
    await users_collection.delete_one({"UserID": user_id})
    logger.info(f"Exiting: delete_user_data")


async def add_log(action: str, details: dict = None):
    logger.info(f"Entering: add_log(action={action}, details={details})")
    log_entry = {
        "timestamp": datetime.utcnow(),
        "action": action,
        "details": details or {}
    }
    await logs_collection.insert_one(log_entry)
    logger.info(f"Exiting: add_log")


# Универсальная функция для сохранения данных в CSV файл
async def save_to_csv(filename, data, headers):
    logger.info(f"Entering: save_to_csv(filename={filename})")
    async with aiofiles.open(filename, mode='w', newline='', encoding='utf-8') as file:
        await file.write(','.join(headers) + '\n')

        for item in data:
            row = [str(item.get(header, "N/A")).replace('\n', ' ').replace('\r', '') for header in headers]
            await file.write(','.join(row) + '\n')
    logger.info(f"Exiting: save_to_csv")


async def export_utm_to_csv():
    logger.info(f"Entering: export_utm_to_csv")
    utm_logs = await logs_collection.find({"action": "utm"}).to_list(length=None)

    utm_data = []
    for log in utm_logs:
        details = log.get("details", {})
        utm_data.append({
            "date": log.get("timestamp", "N/A").strftime("%Y-%m-%d %H:%M:%S") if isinstance(log.get("timestamp"),
                                                                                            datetime) else "N/A",
            "user_id": details.get("user_id", "N/A"),
            "utm_data": details.get("utm_data", "N/A")
        })

    await save_to_csv('data/output.csv', utm_data, ["date", "user_id", "utm_data"])
    logger.info(f"Exiting: export_utm_to_csv")
    return utm_data


async def export_tickets_to_csv():
    logger.info(f"Entering: export_tickets_to_csv")
    tickets = await users_collection.find({"TicketDate": {"$exists": True}}).to_list(length=None)

    data = []
    for ticket in tickets:
        data.append({
            "date": ticket.get("TicketDate", "N/A").strftime("%Y-%m-%d %H:%M:%S") if isinstance(
                ticket.get("TicketDate"), datetime) else "N/A",
            "user_id": ticket.get("UserID", "N/A"),
            "ticket_key": ticket.get("TicketKey", "N/A")
        })

    await save_to_csv('data/output.csv', data, ["date", "user_id", "ticket_key"])
    logger.info(f"Exiting: export_tickets_to_csv")
    return data


async def get_user_ids(lang=None):
    logger.info(f"Entering: get_user_ids(lang={lang})")
    query = {}
    if lang:
        if lang in ["ru", "en"]:
            query = {"Lang": lang}
    user_ids = await users_collection.distinct("UserID", query)
    logger.info(f"Exiting: get_user_ids")
    return user_ids

async def add_admin_id(admin_id: int):
    logger.info(f"Entering: add_admin_id(admin_id={admin_id})")
    """Добавляет новый admin_id в массив Admins в коллекции config"""
    await config_collection.update_one(
        {"Key": "Admins"},
        {"$addToSet": {"Value": admin_id}},
        upsert=True
    )
    logger.info(f"Exiting: add_admin_id")


async def get_admins_list():
    logger.info(f"Entering: get_admins_list")
    """Получает весь список admin_id из массива Admins в коллекции config"""
    config_entry = await config_collection.find_one({"Key": "Admins"})
    if config_entry and "Value" in config_entry:
        logger.info(f"Exiting: get_admins_list")
        return config_entry["Value"]
    logger.info(f"Exiting: get_admins_list (no admins found)")
    return []


async def add_scan_log(admin_id: int, user_id: int):
    logger.info(f"Entering: add_scan_log(admin_id={admin_id}, user_id={user_id})")
    """Добавляет запись в массив ScanLog в коллекции config
    со значениями: ID пользователя, ID билета и текущей датой"""
    log_entry = {
        "admin_id": admin_id,
        "user_id": user_id,
        "scanned_at": datetime.utcnow()
    }

    await config_collection.update_one(
        {"Key": "ScanLog"},
        {"$push": {"Value": log_entry}},
        upsert=True
    )
    logger.info(f"Exiting: add_scan_log")


if __name__ == '__main__':
    # print(asyncio.run(get_user_data(0, "ab280e7b8d3e4e0ea3f5351f6408336e")))
    _ = asyncio.run(get_user_ids('en'))
    print(len(_), _)
