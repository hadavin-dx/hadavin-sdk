"""Timing rows of the text fold (marker ``perf``: CI runs them in their own step). They are NOT in any mutation test list, because the
runner does not copy ``pyproject.toml`` and the marker would be unregistered there. Ceilings are generous (about 20 times the time
measured on the build machine) and say what the row is about."""

import time

import pytest

from hadavin_sdk import defaults
from hadavin_sdk.guard.textnorm import TextTooLong, has_hidden_channel, identity_key, squeeze

pytestmark = pytest.mark.perf
CAP = defaults.TEXTNORM_MAX_CHARS


def _seconds(fn, *args):
    start = time.perf_counter()
    try:
        fn(*args)
    except TextTooLong:
        pass
    return time.perf_counter() - start


def test_a_million_expanding_characters_are_refused_before_any_work():
    """1,000,000 x U+FDFA expands to 18 million characters; the size rule refuses it from the weight, without building the key."""
    assert _seconds(identity_key, chr(0xFDFA) * 1_000_000) < 2.0


def test_a_text_at_the_cap_of_distinct_kinds_of_character_is_folded_in_linear_time():
    text = ("a" + chr(0x301) + "b" + chr(0x200B) + "c" + chr(0x430) + chr(0xFF21) + " \t") * (
        CAP // 9
    )
    assert len(text) <= CAP
    assert _seconds(identity_key, text) < 5.0
    assert _seconds(squeeze, text) < 5.0
    assert _seconds(has_hidden_channel, text) < 1.0


def test_the_refusal_of_an_oversize_ascii_text_is_immediate():
    assert _seconds(identity_key, "a" * (CAP + 1)) < 0.5
