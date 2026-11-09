"""Keyed labels: grammar, no collisions on odd text, never raises (class: label forged or collided by text)."""

from __future__ import annotations

import itertools
import re

import pytest

from hadavin_sdk.audit import labelkey as lk
from tests.stop_state_helpers import KEY

RLO = chr(0x202E)


def test_label_shape_and_stability():
    a = lk.mask_principal("user:a", KEY, "k1")
    assert lk.is_label(a) and a.startswith("id:k1:") and len(a.split(":")[2]) == 32
    assert a == lk.mask_principal("user:a", KEY, "k1")
    assert a != lk.mask_principal("user:b", KEY, "k1")
    assert a != lk.mask_principal("user:a", KEY + b"x", "k1")


@pytest.mark.parametrize(
    "bad",
    [
        "id:k1:" + "a" * 32 + "\n",
        "id:k1:" + "A" * 32,
        "id:k1:" + "a" * 31,
        "id::" + "a" * 32,
        "id:k 1:" + "a" * 32,
        "id:k1:" + "a" * 33,
        "id:k1:" + "١" * 32,
        None,
        5,
        b"id:k1:" + b"a" * 32,
    ],
)
def test_is_label_rejects(bad):
    assert not lk.is_label(bad)


def test_trailing_newline_key_id_rejected():
    assert lk.valid_key_id("k1") and not lk.valid_key_id("k1\n") and not lk.valid_key_id("")
    assert not lk.valid_key_id("x" * 33) and not lk.valid_key_id(None)


def test_lone_surrogates_do_not_collide():
    assert lk.mask_principal("\ud800", KEY, "k1") != lk.mask_principal("\udfff", KEY, "k1")


def test_bidi_and_empty_and_nonstring_never_raise():
    assert lk.mask_principal("", KEY, "k1") == lk.mask_principal(lk.UNIDENTIFIED, KEY, "k1")
    for odd in (RLO + "admin", None, 3, b"x", ["a"]):
        assert lk.is_label(lk.mask_principal(odd, KEY, "k1"))
    assert lk.mask_principal(RLO + "admin", KEY, "k1") != lk.mask_principal("admin", KEY, "k1")


def _texts():
    pool = ["a", ":", "\n", RLO, chr(0xD800), chr(0xDFFF), chr(0x661), "\x00", "id", "k1"]
    yield ""
    for n in (1, 2, 3):
        for combo in itertools.product(pool, repeat=n):
            yield "".join(combo)


def test_exhaustive_distinct_text_distinct_label_and_grammar():
    seen: dict[str, str] = {}
    for t in _texts():
        lab = lk.mask_principal(t, KEY, "k1")
        assert lk.is_label(lab)
        assert seen.setdefault(lab, t or lk.UNIDENTIFIED) == (t or lk.UNIDENTIFIED)
        assert lk.is_label(t) == (
            re.fullmatch(r"id:[A-Za-z0-9_-]{1,32}:[0-9a-f]{32}", t) is not None
        )  # independent literal


def test_the_python_and_the_sql_label_grammar_are_the_same_text():
    """One grammar in three places (labelkey, the functions in migrate, migration 0007): they must not drift."""
    from pathlib import Path

    from hadavin_sdk.store import migrate

    sql_form = migrate._LABEL_RE.strip("'")
    assert sql_form == "^" + lk.LABEL_PATTERN + "$" or sql_form == lk.LABEL_PATTERN
    text = (Path(migrate.__file__).parent / "migrations" / "0007_kill_switch_guard.sql").read_text()
    assert sql_form.lstrip("^").rstrip("$") in text.replace("^", "").replace("$'", "'")
