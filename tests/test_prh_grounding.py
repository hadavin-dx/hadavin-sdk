"""PR H, WP2b: grounding with ignorable characters (promise 5).

An identifier a model typed that holds an ignorable character (zero-width space, variation selector, filler, soft hyphen,
tag character) is refused by `evidence.grounded`, and `evidence.contains` finds a name in an evidence text that holds one
inside the name. Main dropped only the characters of category Cf; the others are new. Tests whose name starts `test_mf_`
fail on main; the Cf rows pass on main. Every character is written as an escape."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from hadavin_sdk.runtime import evidence

CF = {
    "200b": chr(0x200B),
    "200c": chr(0x200C),
    "200d": chr(0x200D),
    "ad": chr(0x00AD),
    "e0041": chr(0xE0041),
}
OTHER = {
    "fe0f": chr(0xFE0F),
    "34f": chr(0x034F),
    "115f": chr(0x115F),
    "1160": chr(0x1160),
    "e0100": chr(0xE0100),
}

# main's NFKC step already changes these two (U+3164 reads U+1160, U+FFA0 reads U+1160), so they are refused on main
NFKC_CHANGED = {"3164": chr(0x3164), "ffa0": chr(0xFFA0)}

CONTRACT = SimpleNamespace(
    input_schema={"type": "object", "properties": {"name": {"type": "string", "identifier": True}}}
)


def _refused(cp: str) -> bool:
    typed = "pod-1" + cp
    # the evidence holds the identifier exactly as typed: only the character itself can make it ungrounded
    return not evidence.grounded(CONTRACT, {"name": typed}, ["pod-1" + cp + " is running"], {})


def _found(cp: str) -> bool:
    return evidence.contains("po" + cp + "d-1 is running", "pod-1")


@pytest.mark.parametrize("cp", list(OTHER.values()), ids=list(OTHER))
def test_mf_grounding_refuses(cp):
    assert _refused(cp)


@pytest.mark.parametrize("cp", list(OTHER.values()), ids=list(OTHER))
def test_mf_contains_finds(cp):
    assert _found(cp)


@pytest.mark.parametrize("cp", list(NFKC_CHANGED.values()), ids=list(NFKC_CHANGED))
def test_grounding_refuses_nfkc_changed(cp):
    assert _refused(cp)


@pytest.mark.parametrize("cp", list(NFKC_CHANGED.values()), ids=list(NFKC_CHANGED))
def test_mf_contains_finds_nfkc_changed(cp):
    assert _found(cp)


@pytest.mark.parametrize("cp", list(CF.values()), ids=list(CF))
def test_grounding_refuses_cf(cp):
    assert _refused(cp)


@pytest.mark.parametrize("cp", list(CF.values()), ids=list(CF))
def test_contains_finds_cf(cp):
    assert _found(cp)


def test_grounding_accepts_a_plain_identifier():
    assert evidence.grounded(CONTRACT, {"name": "pod-1"}, ["pod-1 is running"], {})
    assert not evidence.contains("pod-12 is running", "pod-1")
