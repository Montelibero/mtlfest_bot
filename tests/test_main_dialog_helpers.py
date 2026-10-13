"""Unit tests for pure helpers in routers/main_dialog.py (no Telegram, no Mongo)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from routers.main_dialog import _find_ticket_season, _get_ticket_info


class TestGetTicketInfo:
    def test_returns_season_dict(self):
        user_data = {"tickets": {"2025": {"uuid": "abc"}}}
        assert _get_ticket_info(user_data, "2025") == {"uuid": "abc"}

    def test_missing_season_returns_empty(self):
        assert _get_ticket_info({"tickets": {"2024": {}}}, "2025") == {}

    def test_none_user_data(self):
        # Runtime contract: None is tolerated (see `if user_data else None` guards).
        assert _get_ticket_info(None, "2025") == {}  # type: ignore[arg-type]

    def test_tickets_not_dict(self):
        assert _get_ticket_info({"tickets": "garbage"}, "2025") == {}

    def test_season_value_not_dict(self):
        assert _get_ticket_info({"tickets": {"2025": None}}, "2025") == {}


class TestFindTicketSeason:
    def test_finds_current_season(self):
        user_data = {"tickets": {"2025": {"uuid": "abc"}}}
        assert _find_ticket_season(user_data, "abc") == "2025"

    def test_uuid_mismatch_returns_none(self):
        user_data = {"tickets": {"2025": {"uuid": "abc"}}}
        assert _find_ticket_season(user_data, "other") is None

    def test_no_tickets(self):
        assert _find_ticket_season({}, "abc") is None
        assert _find_ticket_season(None, "abc") is None  # type: ignore[arg-type]
