"""G7 (ORDERS 012 and 013, escalations E3 and E5): ONE more pattern pass after the sweep.

A pattern's result can change once placeholders stand in the text, and the sweep writes placeholders after every
pattern ran. Two shapes found by runs on main, both masked only by a SECOND pass before G7:
- E3: line 1 `BSB: <bank code>`, line 2 `paid <same bank code>/<account>`. The account pattern needs the code's
  placeholder before the digits; on line 2 only the sweep writes it. The account stayed readable.
- E5: line 1 `password=V`, line 2 `Bearer V+xy` with the token under BEARER's 12 characters. Swept to
  `Bearer <SECRET_1>xy`, which is 12 characters or more: only a second pass masked the tail. The same for BASIC
  (8 characters) and `authorization:` (8 characters).
The fix is for the class: `redact()` and `redact_many()` run the whole pattern table once more over the swept text
and sweep once more what that finds (`_Redactor.settle`). Never a loop: two pattern passes and two sweeps at most.
A text the first pass and its sweep left unchanged is not scanned again.
The property over the repo's corpora is in tests/test_redact_idempotent_property.py.

Every digit string and credential here is made up and built from parts.
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


# --- E5: a short token that only the sweep makes long enough ------------------------------------------------------

V = (
    "hun" + "ter" + "9"
)  # 7 characters: with a 2-character tail the token is under every minimum length below
E5 = {
    "bearer": (f"password={V}\nBearer {V}xy", "password=<SECRET_1>\nBearer <BEARER_1>", "BEARER"),
    "basic": (
        f"password={V[:5]}\nBasic {V[:5]}ab",
        "password=<SECRET_1>\nBasic <BASIC_1>",
        "BASIC",
    ),
    "authorization": (
        f"password={V[:5]}\nauthorization: {V[:5]}ab",
        "password=<SECRET_1>\nauthorization: <SECRET_2>",
        "SECRET",
    ),
}


@pytest.mark.parametrize("name", sorted(E5))
def test_e5_a_token_tail_beside_a_swept_secret_is_masked_in_one_pass(name):
    text, expected, kind = E5[name]
    result = R.redact(text)
    assert result.text == expected
    assert kind in result.kinds
    tail = text[-2:]
    assert not result.text.endswith(tail)
    # the whole token is one value in the map, stored restored
    assert text.rsplit(" ", 1)[1] in result.mapping.values()
    # what one pass gave before G7: the tail in clear after the swept placeholder
    assert _old_one_pass(text).endswith("<SECRET_1>" + tail)


@pytest.mark.parametrize("name", sorted(E5))
def test_e5_through_redact_text_one_pass_is_a_fixed_point(name):
    text, expected, _ = E5[name]
    mapping = runmap.RunMap()
    once = runmap.redact_text(text, mapping)
    assert once == expected
    held = dict(mapping)
    assert runmap.is_masked(once, mapping) is True
    assert runmap.redact_text(once, mapping) == once and dict(mapping) == held


def test_e5_must_keep_a_short_word_after_bearer_with_no_known_secret_in_it():
    """Under the minimum length and no swept value inside: kept, before as now."""
    for text in (
        f"Bearer {V}xy",
        "Basic abc12",
        "the bearer of news",
        f"password={V}\nBearer other",
    ):
        now = R.redact(text)
        assert now.text == _old_one_pass(text), text


# --- the design: what runs how many times --------------------------------------------------------------------------


def _counted(monkeypatch):
    calls = {"find": 0, "sweep": 0}
    find, sweep = R._Redactor.find, R._Redactor.sweep

    def counted_find(self, text):
        calls["find"] += 1
        return find(self, text)

    def counted_sweep(self, out):
        calls["sweep"] += 1
        return sweep(self, out)

    monkeypatch.setattr(R._Redactor, "find", counted_find)
    monkeypatch.setattr(R._Redactor, "sweep", counted_sweep)
    return calls


def test_a_text_with_nothing_to_mask_is_scanned_once(monkeypatch):
    calls = _counted(monkeypatch)
    R.redact(f"order {ACCOUNT} shipped, nothing else here")
    assert calls == {"find": 1, "sweep": 1}


def test_a_text_with_a_value_gets_exactly_one_more_pattern_pass_and_no_second_sweep(monkeypatch):
    calls = _counted(monkeypatch)
    R.redact(f"password={V} then nothing")
    assert calls == {"find": 2, "sweep": 1}  # the second pass found nothing new: no second sweep


def test_never_more_than_two_pattern_passes_and_two_sweeps(monkeypatch):
    calls = _counted(monkeypatch)
    for text in [*SHAPES.values(), *(e[0] for e in E5.values())]:
        calls["find"] = calls["sweep"] = 0
        R.redact(text)
        assert calls["find"] <= 2 and calls["sweep"] <= 2, text
    calls["find"] = calls["sweep"] = 0
    R.redact(DIRECT)
    assert calls == {"find": 2, "sweep": 2}  # the second pass found the account: one more sweep


def test_redact_many_scans_again_only_the_strings_that_changed(monkeypatch):
    calls = _counted(monkeypatch)
    R.redact_many(["nothing here", f"password={V}", "nor here"])
    assert calls == {"find": 4, "sweep": 3}


def test_the_patterns_that_name_a_placeholder_are_still_these_two():
    """Kept as a record of step 1 of ORDER 012 (the whole table runs again now, so a new one needs no list)."""
    naming = [
        label
        for label, p in R.PATTERNS
        if "_\\d+>" in p.pattern or "BANKCODE" in p.pattern or "<[A-Z]" in p.pattern
    ]
    assert naming == ["BANKACCT", "SECRET"]


def _two_old_passes(text: str) -> str:
    r = R._Redactor(None)
    once = r.sweep(r.find(text))
    r2 = R._Redactor(r.mapping)
    return r2.sweep(r2.find(once))


def test_public_signatures_are_unchanged():
    import inspect

    assert str(inspect.signature(R.redact)) == (
        "(text: 'str', *, mapping: 'dict[str, str] | None' = None, near: 'tuple[str, ...]' = (), "
        "_sweep_copies: 'bool' = True, _cache: 'dict | None' = None, _deadline: 'float | None' = None) "
        "-> 'RedactionResult'"
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
    assert new < 20.0  # the fixed ceiling, generous: measured 0.48 s (old one pass 0.21 s)
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
