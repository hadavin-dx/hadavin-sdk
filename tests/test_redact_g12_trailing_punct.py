"""G12 (escalation E18 item G7-F4): prose punctuation that a SECRET value takes in at its end.

The key=value value class keeps a comma that begins no `key=` pair and reads `.`, `)`, `!`, `?`, `:`, `]`, `}` as value characters
(`authorization:` reads `;` too), so `password=hunter22, hunter22` stored `hunter22,` and the every-copy sweep of that value left the
clear copy `hunter22` readable. `_place` registers the value without its trailing punctuation as an entry of its own (as a piece).
The E18 probe as written replaced the 6th character (`4`, not `x`) by U+FF58: its "plain copy" is another value (pinned below).
Every assertion message starts with its id (`G12-n `): the mutants of tests/g12_mutants.py expect it."""

from __future__ import annotations

import importlib
import sys

import pytest

from hadavin_sdk.guard import runmap, textnorm

importlib.import_module("hadavin_sdk.guard.redact")
R = sys.modules["hadavin_sdk.guard.redact"]

PW = "hunter22"  # made up; not secret-shaped (no upper case), so no `_PIECE` entry hides the gap


@pytest.mark.parametrize("mark", [",", ".", ")", "!", "?", ":", "]", "}", ",,", "...,", "),"])
def test_g12_a_trailing_mark_does_not_leave_the_clear_copy(mark):
    r = R.redact(f"password={PW}{mark} {PW}")
    assert PW not in r.text, f"G12-1 {r.text}"
    assert r.mapping == {"<SECRET_1>": PW + mark, "<SECRET_2>": PW}, f"G12-2 {r.mapping}"


def test_g12_the_authorization_value_drops_a_semicolon_too():
    v = "hunter22hunter"
    r = R.redact(f"authorization: {v}; {v}")
    assert r.text == "authorization: <SECRET_1> <SECRET_2>", f"G12-3 {r.text}"


def test_g12_the_copy_in_another_string_of_the_call_is_swept():
    out, mapping = R.redact_many([f"password={PW},", f"later: {PW} again"])
    assert out == ["password=<SECRET_1>", "later: <SECRET_2> again"], f"G12-4 {out}"
    assert mapping == {"<SECRET_1>": PW + ",", "<SECRET_2>": PW}, f"G12-4 {mapping}"


@pytest.mark.parametrize(
    "spelled",
    [
        PW[:2] + "ｎ" + PW[3:],  # full-width n
        PW[:6] + "２" + PW[7:],  # full-width 2
        PW[:2] + "ⓝ" + PW[3:],  # circled n
        PW[:2] + "\u200b" + PW[2:],  # zero-width space inside
        PW[:3] + "́" + PW[3:],  # combining acute
    ],
    ids=["fullwidth-letter", "fullwidth-digit", "circled", "zero-width", "combining"],
)
def test_g12_a_spelled_stored_original_sweeps_its_plain_copy(spelled):
    """The E18 shape built as intended: the stored value is a compatibility spelling of the clear copy."""
    text = f"password={spelled}, {PW}"
    assert PW not in R.redact(text).text, "G12-5 bare redact"
    m = runmap.RunMap()
    out = runmap.redact_text(text, m)
    assert PW not in textnorm.fold(out) and spelled not in out, f"G12-5 {out}"
    assert runmap.redact_text(out, m) == out, f"G12-6 {out}"


def test_g12_the_e18_probe_as_written_holds_a_different_value():
    value = "Zq9xW4mT7pLy"  # made up
    s6 = value[:5] + "ｘ" + value[6:]  # the 6th character is `4`: the fold is Zq9xWxmT7pLy
    assert textnorm.fold(s6) != value, "G12-7 the probe's fold"
    r = R.redact(f"password={s6}, {value}")
    # a value one character away is not a copy: unchanged by G12
    assert r.text == f"password=<SECRET_1> {value}", f"G12-7 {r.text}"


def test_g12_a_three_character_core_is_swept_as_its_control_without_the_comma():
    control = R.redact("password=abc abc").text
    assert control == "password=<SECRET_1> <SECRET_1>", f"G12-8 control {control}"
    assert R.redact("password=abc, abc").text == "password=<SECRET_1> <SECRET_2>", "G12-8 abc"
    # under 3 characters: no core, as `_sweep` never sweeps such a value
    assert R.redact("password=ab, ab").mapping == {"<SECRET_1>": "ab,"}, "G12-8 ab"
    # 3 characters: standalone copies only, as for the control
    assert R.redact("password=abc, xabcx").text == "password=<SECRET_1> xabcx", "G12-8 glued"


def test_g12_a_core_the_map_holds_gets_no_second_placeholder():
    r = R.redact(f"password={PW} x\npassword={PW}, y")
    assert r.mapping == {"<SECRET_1>": PW, "<SECRET_2>": PW + ","}, f"G12-9 {r.mapping}"
    assert r.text == "password=<SECRET_1> x\npassword=<SECRET_2> y", f"G12-9 {r.text}"


def test_g12_a_rolled_back_value_takes_its_core_with_it():
    """A discarded in-place round (``_folded_line``) rolls back what it registered: the core goes with its value, so the number
    handed out again names one value only."""
    r = R._Redactor(None)
    counters = r._open_journal()
    r._place("SECRET", PW + ",", PW + ",")
    assert r.mapping == {"<SECRET_1>": PW + ",", "<SECRET_2>": PW}, f"G12-10 {r.mapping}"
    r._rollback(counters)
    assert r.mapping == {} and r.reverse == {}, f"G12-10 {r.mapping} {r.reverse}"
    assert r._place("SECRET", "zz9other", "zz9other") == "<SECRET_1>", "G12-10 number"
    assert r.sweep(f"x {PW} y") == f"x {PW} y", "G12-10 a ghost entry sweeps the core"


def test_g12_identifier_kinds_are_unchanged():
    tenant = R.redact("user_id=acme01, then acme01").mapping
    assert tenant == {"<TENANT_1>": "acme01"}, f"G12-11 {tenant}"
    host = R.redact("host db01.corp.internal. next db01.corp.internal").mapping
    assert host == {"<HOSTNAME_1>": "db01.corp.internal"}, f"G12-11 {host}"
    # no identifier pattern takes trailing punctuation today; the rule is for the secret kinds only
    r = R._Redactor(None)
    r._place("TENANT", "acme01,", "acme01,")
    assert r.mapping == {"<TENANT_1>": "acme01,"}, f"G12-11 {r.mapping}"


def test_g12_a_g9_union_registers_its_value_only_and_no_core():
    """G9's unions (`derived=False`) register the value only: no written form, no pieces, and no G12 core."""
    r = R._Redactor(None)
    r._place("SECRET", PW + ",", PW + ",", derived=False)
    assert r.mapping == {"<SECRET_1>": PW + ","}, f"G12-12 {r.mapping}"
