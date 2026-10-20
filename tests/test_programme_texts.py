"""Text checks for the 2026 programme and ticket messages (RU/EN).

Strings are extracted from the AST of `get_start_data`, so the tests need no bot
token, Mongo connection or Telegram client.
"""

import ast
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import cast

import pytest
from aiogram_dialog.api.protocols import DialogManager
from aiogram_dialog.widgets.text import Format

MAIN_DIALOG = Path(__file__).resolve().parent.parent / "routers" / "main_dialog.py"
MAP_URL = "https://maps.app.goo.gl/q4ZJ8HM864vLig9J8"


def _collection_texts() -> dict[str, dict[str, str]]:
    tree = ast.parse(MAIN_DIALOG.read_text(encoding="utf-8"))
    branches: dict[str, dict[str, str]] = {}
    for node in ast.walk(tree):
        if not (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "get_start_data"):
            continue
        for sub in ast.walk(node):
            if not isinstance(sub, ast.Dict):
                continue
            values: dict[str, str] = {}
            for key, value in zip(sub.keys, sub.values, strict=True):
                if (
                    isinstance(key, ast.Constant)
                    and isinstance(key.value, str)
                    and isinstance(value, ast.Constant)
                    and isinstance(value.value, str)
                ):
                    values[key.value] = value.value
            calendar = values.get("calendar_text")
            if calendar:
                branches["ru" if "Программа" in calendar else "en"] = values
    return branches


TEXTS = _collection_texts()


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str | None, str]] = []
        self.unbalanced: list[str] = []
        self.open_tags: list[str] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._text = []
        self.open_tags.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href is not None:
            self.links.append((self._href, "".join(self._text).strip()))
            self._href = None
        if self.open_tags and self.open_tags[-1] == tag:
            self.open_tags.pop()
        else:
            self.unbalanced.append(tag)

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)


class _FakeDialogManager:
    def is_preview(self) -> bool:
        return False


def test_both_languages_found() -> None:
    assert set(TEXTS) == {"ru", "en"}


@pytest.mark.parametrize("lang", ["ru", "en"])
def test_no_stale_festival_names(lang: str) -> None:
    for key, text in TEXTS[lang].items():
        assert "Monteliber.Zaedno" not in text, key
        assert not re.search(r"Monteliber\s+Fest", text), key


@pytest.mark.parametrize("lang", ["ru", "en"])
def test_ticket_and_schedule_texts_name_the_festival(lang: str) -> None:
    for key in ("calendar_text", "show_ticket_text", "ticket_start_text"):
        assert "Montelibero Fest" in TEXTS[lang][key], key


@pytest.mark.parametrize(
    ("lang", "weekdays"),
    [
        ("ru", ("23 октября — пятница", "24 октября — суббота", "25 октября — воскресенье")),
        ("en", ("23 October — Friday", "24 October — Saturday", "25 October — Sunday")),
    ],
)
def test_programme_weekdays(lang: str, weekdays: tuple[str, str, str]) -> None:
    for weekday in weekdays:
        assert weekday in TEXTS[lang]["calendar_text"], weekday


@pytest.mark.parametrize(
    ("lang", "breakfast"),
    [("ru", "☕️ 10:00–12:00 — MTL завтрак"), ("en", "☕️ 10:00–12:00 — MTL breakfast")],
)
def test_breakfast_venue_and_link(lang: str, breakfast: str) -> None:
    text = TEXTS[lang]["calendar_text"]
    assert breakfast in text
    assert f'<a href="{MAP_URL}">Cafe Pascucci</a>' in text


@pytest.mark.parametrize("lang", ["ru", "en"])
def test_calendar_html_is_well_formed_and_link_is_clickable(lang: str) -> None:
    parser = _LinkParser()
    parser.feed(TEXTS[lang]["calendar_text"])
    parser.close()
    assert parser.unbalanced == []
    assert parser.open_tags == []
    assert (MAP_URL, "Cafe Pascucci") in parser.links


@pytest.mark.parametrize("lang", ["ru", "en"])
async def test_calendar_window_renders_html_unchanged(lang: str) -> None:
    manager = cast(DialogManager, _FakeDialogManager())
    rendered = await Format("{calendar_text}").render_text(TEXTS[lang], manager)
    assert rendered == TEXTS[lang]["calendar_text"]
    assert f'<a href="{MAP_URL}">Cafe Pascucci</a>' in rendered
