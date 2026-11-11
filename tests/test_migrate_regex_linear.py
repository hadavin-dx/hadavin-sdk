"""The serial-column regex must stay linear (SonarCloud: super-linear backtracking) and keep its meaning."""

import pytest

pytest.importorskip("psycopg", reason="store.migrate imports psycopg (the pg extra)")

from hadavin_sdk.store import migrate
from tests.fixtures import timing


def test_serial_regex_finds_serial_columns():
    body = "id BIGSERIAL PRIMARY KEY,\n seq  serial,\n n SMALLSERIAL, x SERIAL4, label TEXT"
    assert migrate._SERIAL.findall(body) == ["id", "seq", "n", "x"]


def test_serial_regex_ignores_non_serial_words():
    assert migrate._SERIAL.findall("id BIGINT, serialized TEXT, SERIALIZABLE x") == []


@pytest.mark.perf  # a wall-clock or CPU-time bound: it runs in the perf step, not the default suite
def test_serial_regex_is_linear_on_hostile_input():
    # Long identifier run with no serial keyword, and a long whitespace run: both used to cost O(n^2).
    for text in ("a" * 60000, "a" + " " * 60000 + "b", ("ab " * 20000)):
        t0 = timing.CLOCK()
        assert migrate._SERIAL.findall(text) == []
        assert timing.CLOCK() - t0 < 1.0
