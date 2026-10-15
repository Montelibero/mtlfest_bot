"""Unit tests for pure helpers in routers/main_dialog.py (no Telegram, no Mongo).

config.bot_config requires a bot token at import time (raises without one), so
tests stub minimal env vars before importing project modules.
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("TEST_BOT_TOKEN", "ci-stub-token")
os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.bot_config import config  # noqa: E402
from routers.main_dialog import (  # noqa: E402
    _find_ticket_season,
    _find_ticket_season_any,
    _get_ticket_info,
)


class TestGetTicketInfo:
    def test_returns_season_dict(self):
        user_data = {"tickets": {"2026": {"uuid": "abc"}}}
        assert _get_ticket_info(user_data, "2026") == {"uuid": "abc"}

    def test_missing_season_returns_empty(self):
        assert _get_ticket_info({"tickets": {"2025": {}}}, "2026") == {}

    def test_none_user_data(self):
        # Runtime contract: None is tolerated (see `if user_data else None` guards).
        assert _get_ticket_info(None, "2026") == {}  # type: ignore[arg-type]

    def test_tickets_not_dict(self):
        assert _get_ticket_info({"tickets": "garbage"}, "2026") == {}

    def test_season_value_not_dict(self):
        assert _get_ticket_info({"tickets": {"2026": None}}, "2026") == {}


class TestFindTicketSeason:
    """_find_ticket_season must only accept the CURRENT season."""

    def test_finds_current_season(self):
        current = config.CURRENT_TICKET_SEASON
        user_data = {"tickets": {current: {"uuid": "abc"}}}
        assert _find_ticket_season(user_data, "abc") == current

    def test_rejects_old_season(self):
        # 2025 ticket with current season 2026 -> None (old QR must not scan).
        user_data = {"tickets": {"2025": {"uuid": "abc"}}}
        assert _find_ticket_season(user_data, "abc") is None

    def test_uuid_mismatch_returns_none(self):
        user_data = {"tickets": {"2026": {"uuid": "abc"}}}
        assert _find_ticket_season(user_data, "other") is None

    def test_no_tickets(self):
        assert _find_ticket_season({}, "abc") is None
        assert _find_ticket_season(None, "abc") is None  # type: ignore[arg-type]


class TestFindTicketSeasonAny:
    """_find_ticket_season_any scans all seasons - scanner uses it to report old tickets."""

    def test_finds_old_season(self):
        user_data = {"tickets": {"2025": {"uuid": "old"}, "2026": {"uuid": "new"}}}
        assert _find_ticket_season_any(user_data, "old") == "2025"
        assert _find_ticket_season_any(user_data, "new") == "2026"

    def test_unknown_uuid(self):
        assert _find_ticket_season_any({"tickets": {"2025": {"uuid": "old"}}}, "nope") is None

    def test_no_tickets(self):
        assert _find_ticket_season_any({}, "x") is None
        assert _find_ticket_season_any(None, "x") is None  # type: ignore[arg-type]
