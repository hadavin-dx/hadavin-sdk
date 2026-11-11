"""Review 4 of PR #42: a cut that lands inside a secret leaves no whole form for the scrub to find, so the front of the
secret stayed next to the `[truncated]` marker. `prepare_output` now removes it. The tests cut a text exactly inside
the secret, in every spelling the scrub undoes, with `max_bytes` equal to the cap so nothing else shortens the output."""

from __future__ import annotations

import pytest

from hadavin_sdk import defaults
from hadavin_sdk import tools as tools_mod
from hadavin_sdk.config import EvidenceSettings
from tests.fixtures import timing

CAP = defaults.MAX_REDACT_CHARS
WINDOW = CAP - len(tools_mod.TRUNCATED)
# `_cut` falls back 256 bytes when the last 256 bytes hold no whitespace: that is where the text is really cut.
CUT_AT = WINDOW - tools_mod.TAIL_WINDOW
SECRET = "Zk3#" + "Pq7vLm2x"  # a fake, built from parts


def _plain(s: str) -> str:
    return s


def _entity(s: str) -> str:
    return "".join(f"&#{ord(c)};" for c in s)


def _json_escape(s: str) -> str:
    return "".join(f"{chr(92)}u{ord(c):04x}" for c in s)


def _percent(s: str) -> str:
    return "".join(f"%{b:02X}" for b in s.encode())


SHAPES = {"plain": _plain, "entity": _entity, "json": _json_escape, "percent": _percent}


def _raw_cut_inside(shape, kept: int, extra: str = "") -> str:
    """A text whose cut point falls after `kept` characters of the secret (plus `extra`, an incomplete escape)."""
    spell = SHAPES[shape]
    head = spell(SECRET[:kept]) + extra
    rest = spell(SECRET[kept:])
    pad = "." * (CUT_AT - len(head))
    return pad + head + rest + "." * 2000


def _tail(out: str) -> str:
    assert out.endswith(tools_mod.TRUNCATED), "the text was not cut: the test does not test the cut"
    return out[: -len(tools_mod.TRUNCATED)][-200:]


@pytest.mark.parametrize("shape", list(SHAPES))
@pytest.mark.parametrize("kept", [3, 5, 11])
def test_no_front_of_the_secret_is_left_next_to_the_cut_marker(shape, kept):
    out = tools_mod.prepare_output(_raw_cut_inside(shape, kept), {}, CAP, [SECRET])
    tail = _tail(out)
    # the secret in each spelling the scrub undoes: its first three characters must not be there
    for spell in SHAPES.values():
        assert spell(SECRET[:3]) not in tail
    assert SECRET[:3] not in tail
    for form in tools_mod._secret_forms(SECRET):
        for n in range(3, len(form)):
            assert not tail.endswith(form[:n]), (form, n)


@pytest.mark.parametrize("shape", ["entity", "json", "percent"])
def test_a_cut_inside_an_escape_does_not_leave_the_front_either(shape):
    """The cut lands after a whole character and a part of the next one's escape."""
    spell = SHAPES[shape]
    extra = spell(SECRET[5])[:3]
    out = tools_mod.prepare_output(_raw_cut_inside(shape, 5, extra), {}, CAP, [SECRET])
    tail = _tail(out)
    assert spell(SECRET[:3]) not in tail


def test_the_front_is_removed_when_the_cut_inside_the_loop_splits_a_later_secret():
    """`_fit` after the first secret's replace cuts at the cap and can split a later secret that is not replaced yet."""
    other = "Hy8@" + "Rt4nWs6d"
    first = "Zx9Qw" + "+"
    copies = (CAP - 273 - 400) // 18  # after the replace each copy is 17 characters and a space
    filler = "." * (CAP - 273 - 18 * copies)  # no whitespace for 256 characters before the cut
    # the cut falls 268 characters before the cap: five characters into `other`
    raw = (first + " ") * copies + filler + other + "." * 300
    out = tools_mod.prepare_output(raw, {}, CAP, [first, other])
    assert out.endswith(tools_mod.TRUNCATED)
    assert other[:3] not in out
    assert out.count("<SECRET_REDACTED>") > 1000


def test_the_ordinary_cut_is_not_shortened_without_a_secret_in_it():
    out = tools_mod.prepare_output("word " * 80_000, {}, CAP, [SECRET])
    assert out.endswith(("word" + tools_mod.TRUNCATED, "word " + tools_mod.TRUNCATED))
    # the cut itself, and the margin (`defaults.CUT_MARGIN`) dropped from the end of a result cut at the cap
    assert len(out) > WINDOW - defaults.CUT_MARGIN - 300


def test_even_one_or_two_characters_of_a_secret_before_the_marker_are_removed():
    forms = sorted(tools_mod._secret_forms(SECRET))
    assert (
        tools_mod._strip_fragment("abc Zk" + tools_mod.TRUNCATED, forms)
        == "abc " + tools_mod.TRUNCATED
    )
    assert (
        tools_mod._strip_fragment("abc Z" + tools_mod.TRUNCATED, forms)
        == "abc " + tools_mod.TRUNCATED
    )


def test_a_trailing_stretch_that_starts_no_form_is_kept():
    forms = sorted(tools_mod._secret_forms(SECRET))
    assert (
        tools_mod._strip_fragment("abc ok" + tools_mod.TRUNCATED, forms)
        == "abc ok" + tools_mod.TRUNCATED
    )


def test_text_without_a_cut_is_never_touched():
    text = "xx Zk3#Pq end"
    assert tools_mod._strip_fragment(text, sorted(tools_mod._secret_forms(SECRET))) == text


# --- many handed-out secrets: the cost stays bounded --------------------------------------------------------------------


@pytest.mark.perf
def test_fifty_handed_out_secrets_behind_an_encoding_layer_stay_within_a_bound():
    """Each replace behind a layer re-runs the decode, so the cost grows with the secrets; a 20 KB result with 50
    secrets (one percent-encoded copy of each) is the shape that exposes it."""
    secrets = [f"Sec{i:03d}" + "Kq7#Zx" for i in range(50)]
    raw = " ".join(_percent(s) for s in secrets) * 20 + " " + "y" * 5000
    t0 = timing.CLOCK()
    out = tools_mod.prepare_output(raw, {}, 200_000, secrets)
    took = timing.CLOCK() - t0
    assert not any(s in out for s in secrets)
    assert took < 30, (
        took
    )  # measured 0.4 s on the laptop; 30 s is the failure line, not the expectation


# --- the manifest cap ----------------------------------------------------------------------------------------------------


def test_a_tool_output_cap_above_the_redactor_cap_is_refused():
    base = {
        "name": "t",
        "function": "m:f",
        "description": "d",
        "input_schema": {},
        "side_effect": "none",
    }
    with pytest.raises(ValueError):
        tools_mod.ToolSpec(**base, max_output_bytes=CAP + 1)
    with pytest.raises(ValueError):
        EvidenceSettings(legacy_max_output_bytes=CAP + 1)
    assert tools_mod.ToolSpec(**base, max_output_bytes=CAP).max_output_bytes == CAP
