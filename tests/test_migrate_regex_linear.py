"""The serial-column regex must stay linear (SonarCloud: super-linear backtracking) and keep its meaning."""

import time

import pytest

pytest.importorskip("psycopg", reason="store.migrate imports psycopg (the pg extra)")

from hadavin_sdk.store import migrate


def test_serial_regex_finds_serial_columns():
    body = "id BIGSERIAL PRIMARY KEY,\n seq  serial,\n n SMALLSERIAL, x SERIAL4, label TEXT"
    assert migrate._SERIAL.findall(body) == ["id", "seq", "n", "x"]


def test_serial_regex_ignores_non_serial_words():
    assert migrate._SERIAL.findall("id BIGINT, serialized TEXT, SERIALIZABLE x") == []


def test_serial_regex_is_linear_on_hostile_input():
    # Long identifier run with no serial keyword, and a long whitespace run: both used to cost O(n^2).
    for text in ("a" * 60000, "a" + " " * 60000 + "b", ("ab " * 20000)):
        t0 = time.monotonic()
        assert migrate._SERIAL.findall(text) == []
        assert time.monotonic() - t0 < 1.0
