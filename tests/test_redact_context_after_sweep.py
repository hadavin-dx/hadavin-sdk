"""G7 (ORDER 012, escalation E3): a pattern that needs a placeholder the SWEEP writes is run again after the sweep.

The gap, confirmed by a run on main: line 1 `BSB: <bank code>`, line 2 `paid <same bank code>/<account>`. The
pattern pass masks the code on line 1; the sweep then writes its placeholder on line 2; the account pattern, which
needs that placeholder before the digits, had already run. One pass left the account number readable; a second
pass masked it.

The patterns of the table whose match can depend on a placeholder already in the text (`redact._CONTEXT_PATTERNS`),
each with a test here:
- BANKACCT, the account straight after its code: `<BANKCODE_n>` is a literal part of its regex.
- BANKACCT, the account after an account keyword: its regex names no placeholder, but its match counts only with
  bank context (`_bank_context`), and one form of that context is a `<BANKCODE_n>` within 100 characters.
One more pattern names a placeholder shape in its regex, the cookie header (`Cookie: <KIND_n>` followed by a space
or the end is NOT a cookie value). It is a negative guard: a placeholder written by the sweep can only stop that
pattern from matching, and the value it would have matched is the placeholder itself. It is not run again
(`test_the_table_has_no_other_pattern_that_names_a_placeholder` pins that these are all there are).

Every digit string here is made up and built from parts.
"""

from __future__ import annotations

import importlib
import sys
import time

import pytest

from hadavin_sdk.guard import runmap

importlib.import_module("hadavin_sdk.guard.redact")
R = sys.modules["hadavin_sdk.guard.redact"]  # the package re-exports a function of the same name

BSB = "062" + "-" + "000"
BSB_2 = "033" + "-" + "111"
ACCOUNT = "1234" + "5678"
ACCOUNT_2 = "8765" + "4321"
FAR = "x " * 80  # 160 characters: wider than the 100-character bank window

DIRECT = f"BSB: {BSB}\npaid {BSB}/{ACCOUNT}"
KEYWORD = f"BSB: {BSB}\n{FAR}\nref {BSB} acct {ACCOUNT}"


def _old_one_pass(text: str) -> str:
    """The path `redact()` took before G7: the pattern pass, then one sweep."""
    r = R._Redactor(None)
    return r.sweep(r.find(text))


# --- the gap, masked in ONE pass ---------------------------------------------------------------------------------


def test_the_account_straight_after_a_swept_bank_code_is_masked_in_one_pass():
    result = R.redact(DIRECT)
    assert result.text == "BSB: <BANKCODE_1>\npaid <BANKCODE_1>/<BANKACCT_1>"
    assert result.mapping == {"<BANKCODE_1>": BSB, "<BANKACCT_1>": ACCOUNT}
    assert ACCOUNT not in result.text


def test_the_same_shape_through_runmap_redact_text_is_masked_in_one_pass():
    mapping = runmap.RunMap()
    out = runmap.redact_text(DIRECT, mapping)
    assert out == "BSB: <BANKCODE_1>\npaid <BANKCODE_1>/<BANKACCT_1>"
    assert dict(mapping) == {"<BANKCODE_1>": BSB, "<BANKACCT_1>": ACCOUNT}
    assert runmap.is_masked(out, mapping) is True


def test_mirror_the_account_after_a_keyword_whose_only_bank_context_is_a_swept_code():
    """The keyword pattern: `acct <digits>` with no bank WORD within the window, only the code's swept copy."""
    result = R.redact(KEYWORD)
    assert result.text == f"BSB: <BANKCODE_1>\n{FAR}\nref <BANKCODE_1> acct <BANKACCT_1>"
    assert result.mapping == {"<BANKCODE_1>": BSB, "<BANKACCT_1>": ACCOUNT}


def test_the_old_path_left_both_shapes_readable():
    """What one pass gave before G7, kept as a record (the pattern pass and the sweep are unchanged)."""
    assert _old_one_pass(DIRECT) == f"BSB: <BANKCODE_1>\npaid <BANKCODE_1>/{ACCOUNT}"
    assert _old_one_pass(KEYWORD).endswith(f"ref <BANKCODE_1> acct {ACCOUNT}")


def test_a_newly_found_account_is_swept_from_the_rest_of_the_text():
    """The account found by the second look is a value like any other: its other standalone copies are masked."""
    text = f"refund {ACCOUNT} failed\nBSB: {BSB}\npaid {BSB}/{ACCOUNT}"
    result = R.redact(text)
    assert result.text == (
        "refund <BANKACCT_1> failed\nBSB: <BANKCODE_1>\npaid <BANKCODE_1>/<BANKACCT_1>"
    )
    assert ACCOUNT not in result.text


def test_two_codes_and_two_accounts():
    """(Written `code, account`: with a space between them the two read as one phone number, before G7 as now.)"""
    text = f"BSB: {BSB}\nBSB: {BSB_2}\npaid {BSB}/{ACCOUNT}\npaid {BSB_2}, {ACCOUNT_2}"
    result = R.redact(text)
    assert result.text == (
        "BSB: <BANKCODE_1>\nBSB: <BANKCODE_2>\n"
        "paid <BANKCODE_1>/<BANKACCT_1>\npaid <BANKCODE_2>, <BANKACCT_2>"
    )
    assert result.kinds == ["BANKCODE", "BANKACCT"]


def test_redact_many_masks_the_account_when_the_code_is_in_another_string():
    """`redact_many` sweeps each string after finding in all of them: the same gap, the same second look. The
    account found in one string is swept from the others too."""
    outs, mapping = R.redact_many([f"BSB: {BSB}", f"paid {BSB}/{ACCOUNT}", f"refund {ACCOUNT}"])
    assert outs == ["BSB: <BANKCODE_1>", "paid <BANKCODE_1>/<BANKACCT_1>", "refund <BANKACCT_1>"]
    assert mapping == {"<BANKCODE_1>": BSB, "<BANKACCT_1>": ACCOUNT}


def test_a_run_map_that_already_holds_the_code_gives_the_same_result():
    """Second text of a run: the code is known from the first text and only the sweep writes it here."""
    mapping = runmap.RunMap()
    assert runmap.redact_text(f"BSB: {BSB}", mapping) == "BSB: <BANKCODE_1>"
    out = runmap.redact_text(f"paid {BSB}/{ACCOUNT}", mapping)
    assert out == "paid <BANKCODE_1>/<BANKACCT_1>"
    assert dict(mapping) == {"<BANKCODE_1>": BSB, "<BANKACCT_1>": ACCOUNT}


def test_redact_untrusted_masks_the_shape_in_one_pass():
    mapping = runmap.RunMap()
    out = runmap.redact_untrusted(DIRECT, mapping)
    assert out == "BSB: <BANKCODE_1>\npaid <BANKCODE_1>/<BANKACCT_1>"


# --- idempotence -------------------------------------------------------------------------------------------------

SHAPES = {
    "direct": DIRECT,
    "keyword": KEYWORD,
    "swept-elsewhere": f"refund {ACCOUNT} failed\nBSB: {BSB}\npaid {BSB}/{ACCOUNT}",
    "two-codes": f"BSB: {BSB}\nBSB: {BSB_2}\npaid {BSB}/{ACCOUNT}\npaid {BSB_2}, {ACCOUNT_2}",
    "sort-code": f"sort code {'12' + '-34-' + '56'}\nsent {'12' + '-34-' + '56'}, {ACCOUNT}",
    "no-bank-at-all": f"order {ACCOUNT} shipped",
}


@pytest.mark.parametrize("name", sorted(SHAPES))
def test_a_second_redact_pass_changes_nothing(name):
    first = R.redact(SHAPES[name])
    second = R.redact(first.text, mapping=first.mapping)
    assert second.text == first.text
    assert second.mapping == first.mapping


@pytest.mark.parametrize("name", sorted(SHAPES))
def test_a_second_redact_text_pass_changes_nothing_and_is_masked_agrees(name):
    mapping = runmap.RunMap()
    once = runmap.redact_text(SHAPES[name], mapping)
    held = dict(mapping)
    assert runmap.is_masked(once, mapping) is True
    assert runmap.redact_text(once, mapping) == once
    assert dict(mapping) == held


@pytest.mark.parametrize("name", sorted(SHAPES))
def test_one_pass_now_equals_two_passes_of_the_old_path(name):
    """Nothing more is masked than two passes masked before: the second look does the second pass's work only
    for the context patterns."""
    r = R._Redactor(None)
    once = r.sweep(r.find(SHAPES[name]))
    r2 = R._Redactor(r.mapping)
    twice = r2.sweep(r2.find(once))
    now = R.redact(SHAPES[name])
    assert now.text == twice
    assert now.mapping == r2.mapping


# --- must keep: the same digits WITHOUT bank context -------------------------------------------------------------

MUST_KEEP = [
    f"order {ACCOUNT} shipped",
    f"paid {ACCOUNT}",
    f"{FAR} acct {ACCOUNT}",  # an account keyword and no bank word or code anywhere
    f"ticket {BSB} and {ACCOUNT}",  # the code's digits with no bank keyword: not a code, so no context
    f"BSB: {BSB}\n{FAR}{FAR}\npaid {ACCOUNT}",  # a code, but its placeholder is nowhere near the digits
    f"BSB: {BSB}\n{FAR}{FAR}\nacct {ACCOUNT}",  # an account keyword more than the window from the code
    f"BSB: {BSB}\npaid {BSB} for 3 items",  # a swept code with no account-shaped digits after it
    f"BSB: {BSB}\npaid {BSB}/2026-11-20",  # a date after a swept code is never an account
]


@pytest.mark.parametrize("text", MUST_KEEP)
def test_digits_without_bank_context_are_masked_no_more_than_before(text):
    now = R.redact(text)
    r = R._Redactor(None)
    assert now.text == r.sweep(r.find(text))  # exactly the old one-pass result
    assert now.mapping == r.mapping
    assert "BANKACCT" not in now.kinds


def test_a_text_with_no_bank_code_placeholder_never_takes_the_second_look(monkeypatch):
    calls = []
    monkeypatch.setattr(
        R._Redactor, "_find_context", lambda self, text: calls.append(text) or text, raising=True
    )
    R.redact(f"order {ACCOUNT} shipped, password={'hun' + 'ter' + '9'}")
    assert calls == []


# --- the table, the bound ----------------------------------------------------------------------------------------


def test_the_table_has_no_other_pattern_that_names_a_placeholder():
    """A new pattern that names a placeholder in its regex must be looked at: it may need the second look."""
    naming = [
        (label, p)
        for label, p in R.PATTERNS
        if "_\\d+>" in p.pattern or "BANKCODE" in p.pattern or "<[A-Z]" in p.pattern
    ]
    assert [label for label, _ in naming] == ["BANKACCT", "SECRET"]
    assert naming[0][1].pattern.startswith("<BANKCODE_")
    assert "(?!<[A-Z][A-Z0-9]*_\\d+>(?:\\s|$))" in naming[1][1].pattern  # the cookie header's negative guard
    context = list(R._CONTEXT_PATTERNS)
    assert [label for label, _ in context] == ["BANKACCT", "BANKACCT"]
    assert naming[0] in context
    assert all(entry in R.PATTERNS for entry in context)
    assert context == [entry for entry in R.PATTERNS if entry[0] == "BANKACCT"]
    assert R._CONTEXT_MARK == "<BANKCODE_"
    assert "<BANKCODE_" in R._BANK_CONTEXT.pattern  # the keyword pattern's context names the same mark


def test_the_round_bound_is_a_small_constant():
    assert R._CONTEXT_ROUNDS == 4


def test_at_the_bound_the_redactor_raises_and_returns_no_text(monkeypatch):
    """Fail closed: with the bound set to 0 the plain shape cannot settle, so `redact` raises instead of returning a
    text with an account it knows of; through `runmap` that is a RedactionError (nothing is sent), the caller's
    map is not written, and the message holds no value."""
    monkeypatch.setattr(R, "_CONTEXT_ROUNDS", 0)
    with pytest.raises(R.ContextNotSettled) as raised:
        R.redact(DIRECT)
    assert ACCOUNT not in str(raised.value) and BSB not in str(raised.value)
    mapping = runmap.RunMap()
    with pytest.raises(runmap.RedactionError) as wrapped:
        runmap.redact_text(DIRECT, mapping)
    assert str(wrapped.value) == "ContextNotSettled"
    assert dict(mapping) == {}
    with pytest.raises(R.ContextNotSettled):
        R.redact_many([f"BSB: {BSB}", f"paid {BSB}/{ACCOUNT}"])
    # a text that needs no second look is not affected by the bound
    assert R.redact(f"order {ACCOUNT} shipped").text == f"order {ACCOUNT} shipped"


def test_one_round_settles_the_plain_shapes(monkeypatch):
    """The bound of 4 is slack: every shape here settles in one round (a second look, then one check)."""
    monkeypatch.setattr(R, "_CONTEXT_ROUNDS", 1)
    for text in SHAPES.values():
        assert R.redact(text).text == _two_old_passes(text)


def _two_old_passes(text: str) -> str:
    r = R._Redactor(None)
    once = r.sweep(r.find(text))
    r2 = R._Redactor(r.mapping)
    return r2.sweep(r2.find(once))


def test_public_signatures_are_unchanged():
    import inspect

    assert str(inspect.signature(R.redact)) == (
        "(text: 'str', *, mapping: 'dict[str, str] | None' = None, near: 'tuple[str, ...]' = (), "
        "_sweep_copies: 'bool' = True, _cache: 'dict | None' = None) -> 'RedactionResult'"
    )
    assert str(inspect.signature(R.redact_many)) == (
        "(items: 'list[str]', mapping: 'dict[str, str] | None' = None, *, near: 'tuple[str, ...]' = ()) "
        "-> 'tuple[list[str], dict[str, str]]'"
    )


def test_find_only_mode_is_left_alone():
    """`_sweep_copies=False` only finds: no sweep, so no second look either."""
    result = R.redact(DIRECT, _sweep_copies=False)
    assert result.text == f"BSB: <BANKCODE_1>\npaid {BSB}/{ACCOUNT}"


# --- timing ------------------------------------------------------------------------------------------------------


def _bank_text(size: int) -> str:
    """About `size` characters: 40 distinct bank codes named once each, then lines that pay a code and an account
    (every line a different account), so the sweep writes a code placeholder on every line and the second look
    has an account to find on every line."""
    codes = [f"{100 + i:03d}-{200 + i:03d}" for i in range(40)]
    head = "".join(f"BSB: {code}\n" for code in codes)
    lines, n, length = [], 0, len(head)
    while length < size:
        line = f"paid {codes[n % 40]}/{10_000_000 + n} for order {n}\n"
        lines.append(line)
        length += len(line)
        n += 1
    return (head + "".join(lines))[:size]


def _seconds(fn, text: str) -> float:
    best = None
    for _ in range(3):
        start = time.process_time()
        fn(text)
        took = time.process_time() - start
        best = took if best is None else min(best, took)
    return best


@pytest.mark.perf  # a CPU-time bound: it runs in the perf step, not the default suite
def test_T1_the_second_look_stays_within_a_fixed_ceiling_on_100000_characters_of_bank_lines():
    text = _bank_text(100_000)
    assert len(text) == 100_000
    out = R.redact(text)
    assert "<BANKACCT_1>" in out.text and out.text.count("<BANKACCT_") > 2000
    old = _seconds(_old_one_pass, text)
    new = _seconds(R.redact, text)
    print(f"\nG7 timing 100,000 chars: old one pass {old:.3f} s, redact() now {new:.3f} s")
    assert new < 20.0  # the fixed ceiling, generous: measured 0.27 s (old one pass 0.21 s)
    # two old passes are the work this replaces; the second look must not cost more than a few of them
    assert new < 6 * max(old, 0.05)


@pytest.mark.perf
def test_T2_the_second_look_is_linear_in_the_text_size():
    """4x the text, at most 12x the time (the repo's rule for a linear pass: 3x per size ratio); the big text is
    under the redaction cap. Every line carries a NEW account, so the map grows with the text: the worst case
    for the second sweep."""
    small, big = _bank_text(60_000), _bank_text(240_000)
    t_small = _seconds(R.redact, small)
    t_big = _seconds(R.redact, big)
    print(f"\nG7 timing: 60,000 chars {t_small:.3f} s, 240,000 chars {t_big:.3f} s")
    assert t_big <= 12 * max(t_small, 0.01)


@pytest.mark.perf
def test_T3_a_text_of_bank_code_placeholders_and_no_account_costs_one_cheap_look():
    """A planted text: a code placeholder written 20,000 times with nothing after it. Nothing changes, so the
    second look is two pattern passes and no sweep."""
    text = f"BSB: {BSB}\n" + f"paid {BSB} ok\n" * 20_000
    old = _seconds(_old_one_pass, text)
    new = _seconds(R.redact, text)
    print(f"\nG7 timing {len(text):,} chars, no account: old {old:.3f} s, now {new:.3f} s")
    assert new < 20.0
    assert new < 3 * max(old, 0.05)
