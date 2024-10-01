import asyncio
from datetime import datetime

import aiofiles
from motor.motor_asyncio import AsyncIOMotorClient

from config.bot_config import config

client = AsyncIOMotorClient(config.MONGO_URI)
db = client.FEST

users_collection = db.users
config_collection = db.config
logs_collection = db.logs


async def get_user_data(user_id):
    return await users_collection.find_one({"UserID": user_id})


async def update_user_data(user_id, data):
    await users_collection.update_one(
        {"UserID": user_id},
        {"$set": data},
        upsert=True
    )


async def get_last_key() -> str:
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
            return ticket_key
        start_key += 1


async def delete_user_data(user_id: int):
    result = await users_collection.delete_one({"UserID": user_id})


async def add_log(action: str, details: dict = None):
    log_entry = {
        "timestamp": datetime.utcnow(),
        "action": action,
        "details": details or {}
    }
    await logs_collection.insert_one(log_entry)



# Универсальная функция для сохранения данных в CSV файл
async def save_to_csv(filename, data, headers):
    async with aiofiles.open(filename, mode='w', newline='', encoding='utf-8') as file:
        await file.write(','.join(headers) + '\n')

        for item in data:
            row = [str(item.get(header, "N/A")).replace('\n', ' ').replace('\r', '') for header in headers]
            await file.write(','.join(row) + '\n')


async def export_utm_to_csv():
    utm_logs = await logs_collection.find({"action": "utm"}).to_list(length=None)

    utm_data = []
    for log in utm_logs:
        details = log.get("details", {})
        utm_data.append({
            "date": log.get("timestamp", "N/A").strftime("%Y-%m-%d %H:%M:%S") if isinstance(log.get("timestamp"), datetime) else "N/A",
            "user_id": details.get("user_id", "N/A"),
            "utm_data": details.get("utm_data", "N/A")
        })

    await save_to_csv('data/output.csv', utm_data, ["date", "user_id", "utm_data"])
    return utm_data


async def export_tickets_to_csv():
    tickets = await users_collection.find({"TicketDate": {"$exists": True}}).to_list(length=None)

    data = []
    for ticket in tickets:
        data.append({
            "date": ticket.get("TicketDate", "N/A").strftime("%Y-%m-%d %H:%M:%S") if isinstance(ticket.get("TicketDate"), datetime) else "N/A",
            "user_id": ticket.get("UserID", "N/A"),
            "ticket_key": ticket.get("TicketKey", "N/A")
        })

    await save_to_csv('data/output.csv', data, ["date", "user_id", "ticket_key"])
    return data


async def get_user_ids():
    user_ids = await users_collection.distinct("UserID")
    return user_ids



if __name__ == '__main__':
    print(asyncio.run(get_user_ids()))
