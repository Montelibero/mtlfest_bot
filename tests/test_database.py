"""Integration tests against a throwaway MongoDB (docker run on a local port).

Skipped automatically when the container is not reachable, so `pytest -q`
stays green on machines without docker.
"""

import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

MONGO_TEST_URI = "mongodb://localhost:27017"


def _mongo_available() -> bool:
    try:
        import pymongo

        pymongo.MongoClient(MONGO_TEST_URI, serverSelectionTimeoutMS=1500).admin.command("ping")
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _mongo_available(), reason="local mongodb on :27017 not available")


@pytest.fixture()
def test_db(monkeypatch):
    """Point the database module at a throwaway DB on the local mongo.

    motor binds its executor to the event loop at client creation time, so the
    client is recreated per-test with the loop pytest-asyncio provides.
    """
    monkeypatch.setenv("MONGO_URI", MONGO_TEST_URI)

    import config.bot_config as bot_config

    bot_config.config.MONGO_URI = MONGO_TEST_URI
    import database.database as database

    database.client = database.AsyncIOMotorClient(MONGO_TEST_URI)
    db_name = f"FEST_TEST_{uuid.uuid4().hex[:8]}"
    database.db = database.client[db_name]
    database.users_collection = database.db.users
    database.config_collection = database.db.config
    database.logs_collection = database.db.logs
    yield database
    database.client.close()


class TestKeyIssuance:
    """get_last_key: zero-padded keys, no collisions with issued tickets.

    Each issuance starts from the stored counter, so the caller is expected to
    register the ticket right after (as on_button_clicked does). These tests
    mirror that: issue -> occupy -> issue.
    """

    async def test_first_key_is_011(self, test_db):
        key = await test_db.get_last_key()
        assert key == "011"

    async def test_occupied_keys_are_skipped(self, test_db):
        first = await test_db.get_last_key()
        assert first == "011"
        # Caller registers the ticket under this key (production flow).
        await test_db.users_collection.insert_one(
            {"UserID": 1, "tickets": {"2025": {"key": first, "uuid": "x"}}}
        )
        second = await test_db.get_last_key()
        assert second == "012"

    async def test_gap_in_keys_is_skipped(self, test_db):
        # 011 taken by a user, but counter says 10 -> must skip to 012.
        await test_db.users_collection.insert_one(
            {"UserID": 1, "tickets": {"2025": {"key": "011", "uuid": "x"}}}
        )
        key = await test_db.get_last_key()
        assert key == "012"

    async def test_counter_persists(self, test_db):
        await test_db.get_last_key()
        doc = await test_db.config_collection.find_one({"Key": "LastTicketKey_2025"})
        assert doc["Value"] == 11


class TestUserData:
    async def test_upsert_and_read(self, test_db):
        await test_db.update_user_data(42, {"Lang": "ru"})
        user = await test_db.get_user_data(42)
        assert user["UserID"] == 42
        assert user["Lang"] == "ru"

    async def test_nested_ticket_update(self, test_db):
        await test_db.update_user_data(42, {"tickets.2025.uuid": "abc"})
        user = await test_db.get_user_data(42)
        assert user["tickets"]["2025"]["uuid"] == "abc"

    async def test_find_by_ticket_uuid(self, test_db):
        await test_db.update_user_data(42, {"tickets.2025.uuid": "abc"})
        user = await test_db.get_user_data(None, "abc")
        assert user["UserID"] == 42

    async def test_delete(self, test_db):
        await test_db.update_user_data(42, {"Lang": "ru"})
        await test_db.delete_user_data(42)
        assert await test_db.get_user_data(42) is None
