"""G7 (ORDERS 012 and 013, escalations E3 and E5; rebuilt as a capped fixed-point loop in fix rounds 2 and 3): the table runs again
after the sweep.

A pattern's result can change once placeholders stand in the text, and the sweep writes placeholders after every pattern ran.
Two shapes found by runs on main, both masked only by a LATER pattern pass before G7:
- E3: line 1 `BSB: <bank code>`, line 2 `paid <same bank code>/<account>`. The account pattern needs the code's
  placeholder before the digits; on line 2 only the sweep writes it. The account stayed readable.
- E5: line 1 `password=V`, line 2 `Bearer V+xy` with the token under BEARER's 12 characters. Swept to
  `Bearer <SECRET_1>xy`, which is 12 characters or more: only a later pass masked the tail. The same for BASIC
  (8 characters) and `authorization:` (8 characters).
The fix is for the class: `redact()` and `redact_many()` run `_Redactor.settle`, which runs the whole table again over the strings that
changed, round after round, until a round changes no text, at most `_SETTLE_ROUNDS` (4) rounds, a RedactionError past the cap (the cap and
the loop are in tests/test_redact_settle_loop.py). The tests here are the one- and two-round shapes, the unchanged-result checks and
the guards on what the design relies on (the list of patterns that read a placeholder, the purity of the pattern decision, the placeholder
shape). A text the first pass and its sweep left unchanged is not scanned again. The property over the repo's corpora is in
tests/test_redact_idempotent_property.py.

Every digit string and credential here is made up and built from parts. The `print` lines of the perf tests (shown with `-s`) are the
measured numbers the evidence file quotes; no assertion reads them.
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
SID = "abcdef" + "123456"
MAIL = "bob" + "@" + "example" + ".com"
IPV4 = "10." + "1.2.3"
SSN = "123" + "-" + "45" + "-" + "6789"
FAR = "x " * 80  # 160 characters: wider than the 100-character bank window

DIRECT = f"BSB: {BSB}\npaid {BSB}/{ACCOUNT}"
KEYWORD = f"BSB: {BSB}\n{FAR}\nref {BSB} acct {ACCOUNT}"


def _old_one_pass(text: str) -> str:
    """The path `redact()` took before G7: the pattern pass, then one sweep."""
    r = R._Redactor(None)
    return r.sweep(r.find(text))


# --- the gap, masked in ONE call ---------------------------------------------------------------------------------


def test_the_account_straight_after_a_swept_bank_code_is_masked_in_one_call():
    result = R.redact(DIRECT)
    assert result.text == "BSB: <BANKCODE_1>\npaid <BANKCODE_1>/<BANKACCT_1>"
    assert result.mapping == {"<BANKCODE_1>": BSB, "<BANKACCT_1>": ACCOUNT}
    assert ACCOUNT not in result.text


def test_the_same_shape_through_runmap_redact_text_is_masked_in_one_call():
    mapping = runmap.RunMap()
    out = runmap.redact_text(DIRECT, mapping)
    assert out == "BSB: <BANKCODE_1>\npaid <BANKCODE_1>/<BANKACCT_1>"
    assert dict(mapping) == {"<BANKCODE_1>": BSB, "<BANKACCT_1>": ACCOUNT}
    held = dict(mapping)
    assert runmap.redact_text(out, mapping) == out and dict(mapping) == held  # a fixed point


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
    """The account found in round 1 is a value like any other: its other standalone copies are masked."""
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
    """`redact_many` sweeps each string after finding in all of them: the same gap, the same settle rounds. The
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


def test_redact_untrusted_masks_the_shape_in_one_call():
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
def test_a_second_redact_text_pass_changes_nothing(name):
    mapping = runmap.RunMap()
    once = runmap.redact_text(SHAPES[name], mapping)
    held = dict(mapping)
    assert runmap.redact_text(once, mapping) == once
    assert dict(mapping) == held


@pytest.mark.parametrize("name", sorted(SHAPES))
def test_one_call_now_equals_two_calls_of_the_old_path(name):
    """Nothing more is masked than two calls of the old path masked (find and sweep, then find and sweep over the result)."""
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
def test_e5_a_token_tail_beside_a_swept_secret_is_masked_in_one_call(name):
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
def test_e5_through_redact_text_one_call_is_a_fixed_point(name):
    text, expected, _ = E5[name]
    mapping = runmap.RunMap()
    once = runmap.redact_text(text, mapping)
    assert once == expected
    held = dict(mapping)
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

    def counted_sweep(self, out, deadline=None):
        calls["sweep"] += 1
        return sweep(self, out, deadline)

    monkeypatch.setattr(R._Redactor, "find", counted_find)
    monkeypatch.setattr(R._Redactor, "sweep", counted_sweep)
    return calls


def test_a_text_with_nothing_to_mask_is_scanned_once(monkeypatch):
    calls = _counted(monkeypatch)
    R.redact(f"order {ACCOUNT} shipped, nothing else here")
    assert calls == {"find": 1, "sweep": 1}


def test_a_text_with_a_value_gets_one_confirming_pattern_pass_and_no_second_sweep(monkeypatch):
    calls = _counted(monkeypatch)
    R.redact(f"password={V} then nothing")
    assert calls == {
        "find": 2,
        "sweep": 1,
    }  # round 1 found nothing and changed nothing: it ends the loop, no second sweep


def test_the_direct_shape_is_three_pattern_passes_and_two_sweeps(monkeypatch):
    """Pass 1 and its sweep; round 1 finds the account (the map grew: sweep); round 2 confirms (nothing changed: no sweep).
    The shapes of this file need at most `1 + rounds` passes, `rounds` well under the cap."""
    calls = _counted(monkeypatch)
    for text in [*SHAPES.values(), *(e[0] for e in E5.values())]:
        calls["find"] = calls["sweep"] = 0
        R.redact(text)
        assert 1 <= calls["find"] <= 1 + (R._SETTLE_ROUNDS - 1), text
        assert 1 <= calls["sweep"] <= 1 + (R._SETTLE_ROUNDS - 1), text
    calls["find"] = calls["sweep"] = 0
    R.redact(DIRECT)
    assert calls == {"find": 3, "sweep": 2}


def test_redact_many_scans_again_only_the_strings_the_first_pass_or_sweep_changed(monkeypatch):
    calls = _counted(monkeypatch)
    R.redact_many(["nothing here", f"password={V}", "nor here"])
    assert calls == {"find": 4, "sweep": 3}


def test_public_signatures_are_unchanged():
    import inspect

    assert str(inspect.signature(R.redact)) == (
        "(text: 'str', *, mapping: 'dict[str, str] | None' = None, near: 'tuple[str, ...]' = (), "
        "_sweep_copies: 'bool' = True, _cache: 'dict | None' = None, _deadline: 'float | None' = None) "
        "-> 'RedactionResult'"
    )
    assert str(inspect.signature(R.redact_many)) == (
        "(items: 'list[str]', mapping: 'dict[str, str] | None' = None, *, near: 'tuple[str, ...]' = (), "
        "_deadline: 'float | None' = None) -> 'tuple[list[str], dict[str, str]]'"
    )


def test_find_only_mode_is_left_alone():
    """`_sweep_copies=False` only finds: no sweep, so no settle loop either."""
    result = R.redact(DIRECT, _sweep_copies=False)
    assert result.text == f"BSB: <BANKCODE_1>\npaid {BSB}/{ACCOUNT}"


# --- timing ------------------------------------------------------------------------------------------------------


def _bank_text(size: int) -> str:
    """About `size` characters: 40 distinct bank codes named once each, then lines that pay a code and an account
    (every line a different account), so the sweep writes a code placeholder on every line and round 1
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
def test_T1_the_settle_rounds_stay_within_a_fixed_ceiling_on_100000_characters_of_bank_lines():
    text = _bank_text(100_000)
    assert len(text) == 100_000
    out = R.redact(text)
    assert "<BANKACCT_1>" in out.text and out.text.count("<BANKACCT_") > 2000
    old = _seconds(_old_one_pass, text)
    new = _seconds(R.redact, text)
    print(f"\nG7 timing 100,000 chars: old one pass {old:.3f} s, redact() now {new:.3f} s")
    assert (
        new < 20.0
    )  # the fixed ceiling, generous (measured: ticket and evidence G7-1.md, round 3)
    # a round is a pass and a sweep of what changed: the rounds must not cost more than a few old passes
    assert new < 8 * max(old, 0.05)


@pytest.mark.perf
def test_T2_the_settle_rounds_are_linear_in_the_text_size():
    """4x the text, at most 12x the time (the repo's rule for a linear pass: 3x per size ratio); the big text is
    under the redaction cap. Every line carries a NEW account, so the map grows with the text: the worst case
    for the sweep of round 1."""
    small, big = _bank_text(60_000), _bank_text(240_000)
    t_small = _seconds(R.redact, small)
    t_big = _seconds(R.redact, big)
    print(f"\nG7 timing: 60,000 chars {t_small:.3f} s, 240,000 chars {t_big:.3f} s")
    assert t_big <= 12 * max(t_small, 0.01)


@pytest.mark.perf
def test_T3_a_text_of_bank_code_placeholders_and_no_account_costs_one_cheap_round():
    """A planted text: a code placeholder written 20,000 times with nothing after it. Nothing changes, so the
    rounds are one confirming pattern pass and no second sweep."""
    text = f"BSB: {BSB}\n" + f"paid {BSB} ok\n" * 20_000
    old = _seconds(_old_one_pass, text)
    new = _seconds(R.redact, text)
    print(f"\nG7 timing {len(text):,} chars, no account: old {old:.3f} s, now {new:.3f} s")
    assert new < 20.0
    assert new < 3 * max(old, 0.05)


# --- what the design relies on (round 3 N2, M7: replaces the test that pinned the list of two patterns) --------------------------------

# Patterns whose regex SOURCE reads a placeholder shape. BANKACCT: `<BANKCODE_n>` straight before the account (the keyword form reads
# it through `_bank_context`). SECRET: the cookie form's negative guard (`Cookie: <SECRET_1>` stays as it is).
_READERS = {"BANKACCT", "SECRET"}
_GUARD_ONLY = {
    "SECRET"
}  # reads a placeholder only to LEAVE one alone: a fold-only hit never depends on it


def test_every_pattern_whose_source_names_a_placeholder_shape_is_a_context_label():
    """`_CONTEXT_LABELS` takes a full round in the fold scan whatever the scan found. A pattern whose result depends on a placeholder
    must be listed; a new one that is not fails here. The loop of `settle` does not rely on this list (it runs the whole table),
    the fold scan does. THE LIMIT of this check (round 3 nit 4): it sees only a pattern whose regex SOURCE names a placeholder
    (`_\\d+>` or `<[A-Z`). A value class that merely ADMITS `<` and `>` (BEARER, BASIC, authorization, cookies, flags) is invisible to
    it, and that is why `settle` runs the whole table again instead of a list."""
    import re

    readers = {label for label, p in R.PATTERNS if re.search(r"_\\d\+>|<\[A-Z", p.pattern)}
    assert readers == _READERS, (
        "a pattern reads a placeholder shape this list does not know: decide, then list it"
    )
    assert readers - _GUARD_ONLY <= R._CONTEXT_LABELS
    assert {
        "BANKACCT",
        "BANKCODE",
    } == R._CONTEXT_LABELS  # the producer of the context is listed too
    # BANKACCT's keyword form reads the context through the function, not through its regex source
    assert R._BANK_CONTEXT.search("<BANKCODE_12>") is not None


def test_the_pattern_decision_does_not_read_the_map():
    """`settle` relies on the pattern PASS being a function of the text and the batch flag, not of the map: `_decide` (the choice of
    what is a value) ignores `mapping`, `reverse`, `counters`, `alias` and the spelled forms. Only `_mask_ex` reads the map, to choose the
    placeholder. A source check and a behavioural one: the same decisions with an empty and with a full map."""
    import inspect
    import re

    src = inspect.getsource(R._Redactor._decide)
    # every attribute of the redactor that `_decide` names, not a list of forbidden ones (round 3 nit 5): only the batch flag. Its LIMIT:
    # a source check sees this function's own text, not what a module-level helper it calls reads; the behavioural check below, the same
    # decisions with an empty and a full map, covers that side.
    assert set(re.findall(r"self\.(\w+)", src)) <= {"bank_near"}, (
        "_decide reads redactor state: the settle loop assumes a pass is a function of the text and the batch flag"
    )
    texts = [
        DIRECT,
        KEYWORD,
        *SHAPES.values(),
        *(e[0] for e in E5.values()),
        f"Bearer {V}xy",
        f"password={V}",
    ]
    texts += [
        "Bearer <SECRET_1>xy and Basic <SECRET_2>ab",
        f"password=<SECRET_1>xy; Cookie: <SECRET_3>; sid={SID}",
        f"Cookie: a=<SECRET_1>; sid={SID}",
        f"mail {MAIL} from {IPV4} at {SSN}",
        f"paid <BANKCODE_1>/{ACCOUNT} and <BANKCODE_1> {ACCOUNT_2}",
    ]
    full = {f"<SECRET_{n}>": f"k{n:04d}abc" for n in range(1, 40)} | {"<BANKCODE_1>": BSB}
    decided = 0
    for text in texts:
        for label, pattern in R.PATTERNS:
            for m in pattern.finditer(text):
                empty, loaded = R._Redactor(None), R._Redactor(dict(full))
                empty.bank_near = loaded.bank_near = True
                assert empty._decide(m, label) == loaded._decide(m, label), (label, text[:40])
                decided += 1
    assert decided >= 25  # the loop looked at real matches


def test_the_placeholder_shape_is_what_the_redactor_issues_and_what_the_patterns_read():
    """`_PLACEHOLDER` (the split of the sweep and the strip of `_mask_ex`), `<BANKCODE_n>` in the patterns and `kind_of` agree with what
    `_place` writes, for every label and a 5-digit number."""
    for label in R._LABELS:
        r = R._Redactor(None)
        r.counters[label] = 12344
        placeholder = r._place(label, "v" * 8, "v" * 8)
        assert placeholder == f"<{label}_12345>"
        assert R._PLACEHOLDER.fullmatch(placeholder), placeholder
        assert R.kind_of(placeholder) == label
    assert R._PLACEHOLDER.fullmatch("<BANKCODE_1>") and R._PLACEHOLDER.fullmatch("<BANKCODE_99999>")
    assert not R._PLACEHOLDER.fullmatch("<bankcode_1>") and not R._PLACEHOLDER.fullmatch(
        "<BANKCODE_>"
    )
    assert R._BANK_CONTEXT.search("x <BANKCODE_1> y") and R._BANK_CONTEXT.search(
        "x <BANKCODE_99999> y"
    )


@pytest.mark.parametrize(
    "text",
    [
        "password=\u2039EMAIL_1\u203a host",  # the value is the one escaped token; `host` stands outside it
        "password=<EMAIL_1> <IPV4_1>",  # token runs: a space ...
        "password=<EMAIL_1>\t<IPV4_1>",  # ... a tab ...
        "password=<EMAIL_1>;<IPV4_1>",  # ... `;` ...
        "password=<EMAIL_1>,<IPV4_1>",  # ... `,`
        "password=<SEC",  # a cut-off opening
        "password=<SECRET_",
        "password=<EMAIL_1> <SEC",
    ],
)
def test_a_secret_value_made_only_of_own_label_tokens_is_left_unmasked_a_stated_limit(text):
    """Drift report, E9: the `_OWN_OUTPUT` rule (in `_decide`) leaves a SECRET value that is nothing but the redactor's own tokens (genuine or
    escaped, separated by space, tab, `;` or `,`, with an optional cut-off opening) as typed, and makes no map entry. A real credential
    spelled like that is therefore NOT masked: a limit stated in the comment above `_OWN_OUTPUT`, pinned here so a change is looked at."""
    result = R.redact(text)
    assert result.text == text and result.mapping == {}
