"""Tests for database.qr_helpers: QR create -> decode roundtrip.

These exercise the exact pipeline used in production: create_beautiful_code
writes a PNG with logo text, decode_qr_code reads it back (cv2 first, pyzbar
fallback).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.qr_helpers import (
    create_beautiful_code,
    decode_color,
    decode_qr_code,
    decode_qr_code_cv,
    decode_qr_code_pyzbar,
)


class TestDecodeColor:
    def test_decodes_hex_pairs(self):
        assert decode_color("5A89B9") == (0x5A, 0x89, 0xB9)
        assert decode_color("ffffff") == (255, 255, 255)

    def test_invalid_hex_raises(self):
        with pytest.raises(ValueError):
            decode_color("zzzzzz")


class TestQRRoundtrip:
    def test_qr_with_logo_key_decodes(self, tmp_path):
        """Production path: create_beautiful_code with a key label."""
        uuid_hex = "aabbccdd11223344556677889900aabb"
        path = tmp_path / "qr2.png"
        create_beautiful_code(str(path), uuid_hex, "MTLFEST011")
        assert decode_qr_code_cv(str(path)) == uuid_hex
        assert decode_qr_code_pyzbar(str(path)) == uuid_hex

    def test_beautiful_code_with_key_roundtrip(self, tmp_path):
        """Production shape: uuid hex + 'MTLFEST' + zero-padded key."""
        uuid_hex = "852f893a77a54f41876677b3cd5298c0"
        payload = "MTLFEST011"
        path = tmp_path / "ticket.png"
        create_beautiful_code(str(path), uuid_hex, payload)
        decoded = decode_qr_code(str(path))
        assert decoded == uuid_hex

    def test_decode_missing_file_cv2(self, tmp_path):
        assert decode_qr_code_cv(str(tmp_path / "nope.png")) is None

    def test_decode_missing_file_pyzbar(self, tmp_path):
        assert decode_qr_code_pyzbar(str(tmp_path / "nope.png")) is None

    def test_decode_image_without_qr(self, tmp_path):
        from PIL import Image

        blank = Image.new("RGB", (200, 200), "white")
        path = tmp_path / "blank.png"
        blank.save(path)
        assert decode_qr_code(str(path)) is None
