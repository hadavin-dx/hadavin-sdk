"""reader.normalise_for_model: the one function that makes send_text. CRLF, BOM and NUL inputs are built at test time, not committed."""

from __future__ import annotations

import hashlib

import pytest

from conftest import MINI
from intake.reader import normalise_for_model as n


def test_crlf_cr_and_bom():
    assert n(b"a\r\nb\r\n") == "a\nb\n"
    assert n(b"a\rb") == "a\nb"
    assert n(b"\xef\xbb\xbfhello") == "hello"
    assert n(b"\xef\xbb\xbf\xef\xbb\xbfhello") == "hello"  # leading BOMs only
    assert n(b"a\xef\xbb\xbfb") == "a" + chr(0xFEFF) + "b"  # an interior BOM is left for the reader to judge


def test_nfc():
    decomposed = "Mu" + chr(0x308) + "ller"
    composed = "M" + chr(0xFC) + "ller"
    assert decomposed != composed  # really the decomposed form
    assert n(decomposed.encode()) == composed
    assert n(composed.encode()) == composed


def test_bad_utf8_raises_for_the_reader_to_flag():
    for raw in (b"\xff\xfe", b"abc\x80", b"\xc3\x28"):
        with pytest.raises(UnicodeDecodeError):
            n(raw)


def test_nul_is_kept_for_the_reader_to_flag():
    assert "\x00" in n(b"ab\x00cd")


def test_empty_and_idempotent_on_the_mini_invoices():
    assert n(b"") == ""
    for p in MINI.glob("*.txt"):
        once = n(p.read_bytes())
        assert once == p.read_text(encoding="utf-8")  # fixtures are already LF, NFC, BOM-free
        assert n(once.encode()) == once


def test_the_gate_hash_is_of_the_normalised_utf8_text_not_the_raw_bytes():
    raw = b"a\r\nb\n"
    assert hashlib.sha256(n(raw).encode()).hexdigest() == hashlib.sha256(b"a\nb\n").hexdigest() != hashlib.sha256(raw).hexdigest()
