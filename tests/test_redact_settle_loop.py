"""G7 fix rounds 2 and 3 (ORDER 020 MJ-B, review findings dz-1 .. dz-4, cb-M2 .. M4, round 3 M1 .. M5): the capped fixed-point loop of `_Redactor.settle`.

After the first sweep the whole pattern table runs again over the strings that changed. A ROUND is the table over the strings of
`todo`, then a sweep (of every string when the map grew, else of the strings the table changed); `todo` of the next round is the
UNION of the strings the table changed and the strings the sweep changed. The loop ends on the first round that changes no
text: a fixed point of "table, then sweep". The acceptance rule, exactly: settled when some round within `_SETTLE_ROUNDS` (4)
changes no text, so a chain whose last change is made in round 3 is accepted and one that still changes a text in round 4 is
REFUSED (RedactionError("NotSettled"), nothing shown). The cap is a fail-closed margin over the measured depth, not a derived
bound. Every round and every sweep of it has the call's deadline from the same CPU clock as `REDACT_BUDGET_S` (InputTooLarge,
never a skipped pass). A compound secret found late is also swept by its placeholder-spelled form (`<SECRET_1>xy`), so its
other copies keep no tail; that scan is linear in the text.

What is here: the chains that used to leave a value readable (and the fail-before lines in evidence/G7-1.md), the cap at its real
value (a pass that changes its text for exactly 3, 4 and 5 rounds, and the real chain of three), the deadline, the cheap cases
that pay nothing, the pattern nits (AZURESAS `sig=`, `"auth":`), the documented boundary class, a generator of 4 to 8 lines with
a pre-seeded run map compared with a reference fixed-point loop, the depth distribution, and perf tests at the size cap. Every
credential is made up and built from parts.
"""

from __future__ import annotations

import importlib
import random
import re
import sys
import time
import tracemalloc
import types
import uuid
from collections import Counter

import pytest

from hadavin_sdk import defaults
from hadavin_sdk.guard import runmap

importlib.import_module("hadavin_sdk.guard.redact")
R = sys.modules["hadavin_sdk.guard.redact"]

BSB = "062" + "-" + "000"
ACCOUNT = "1234" + "5678"
V = "abcd" + "9x"
CHAIN3 = f"password={V}\nBSB: {BSB}{V}\npaid {BSB}/{ACCOUNT}"


# --- dz-1 / MJ-B: the chain of three is masked in ONE call ---------------------------------------------------------


def test_chain_of_three_through_redact_leaves_no_account():
    result = R.redact(CHAIN3)
    assert ACCOUNT not in result.text and V not in result.text and BSB not in result.text
    assert result.text.endswith("paid <BANKCODE_1>/<BANKACCT_1>")
    assert set(result.mapping.values()) == {V, BSB, ACCOUNT}


def test_chain_of_three_through_redact_text_is_a_fixed_point():
    mapping = runmap.RunMap()
    once = runmap.redact_text(CHAIN3, mapping)
    assert ACCOUNT not in once and V not in once
    held = dict(mapping)
    assert runmap.redact_text(once, mapping) == once and dict(mapping) == held


def test_chain_of_three_through_redact_many_across_strings():
    out, mapping = R.redact_many([f"password={V}", f"BSB: {BSB}{V}", f"paid {BSB}/{ACCOUNT}"])
    assert not any(ACCOUNT in t or V in t for t in out)
    assert out[2] == "paid <BANKCODE_1>/<BANKACCT_1>"
    assert ACCOUNT in mapping.values()


def _rounds_spy(monkeypatch):
    """Counts the rounds `settle` starts (it checks the deadline once at the start of each). Calls through."""
    rounds = {"n": 0}
    check = R._Redactor._check_deadline

    def spy(self):
        rounds["n"] += 1
        return check(self)

    monkeypatch.setattr(R._Redactor, "_check_deadline", spy)
    return rounds


def _hop_chain(monkeypatch, final: int):
    """A pass that changes its text for exactly the rounds the cap is about: `hop0` -> `hop1` -> ... -> `hop<final>` one step per
    call of `find`, nothing else touched. The cap itself is NOT patched (`_SETTLE_ROUNDS` stays 4). It stands in for a real chain
    of that depth: no natural chain deeper than 3 rounds was found (see the depth test below), and the loop's arithmetic is what
    these tests pin. Pass 1 makes `hop1`; round r then makes `hop<r+1>`; the first round that changes nothing ends it."""
    real = R._Redactor.find

    def find(self, text):
        m = re.fullmatch(r"hop(\d+)", text)
        if m and int(m.group(1)) < final:
            return f"hop{int(m.group(1)) + 1}"
        return real(self, text)

    monkeypatch.setattr(R._Redactor, "find", find)


@pytest.mark.parametrize("final", [1, 2, 3, 4])
def test_a_chain_that_changes_for_up_to_three_rounds_and_one_that_needs_four_are_settled_with_the_real_cap(
    monkeypatch, final
):
    assert R._SETTLE_ROUNDS == 4  # the real cap, never patched here
    _hop_chain(monkeypatch, final)
    rounds = _rounds_spy(monkeypatch)
    result = R.redact("hop0")
    assert result.text == f"hop{final}"
    assert (
        rounds["n"] == final
    )  # `final - 1` rounds that change, one that confirms: 4 rounds for the last case
    assert runmap.redact_text("hop0", runmap.RunMap()) == f"hop{final}"
    assert R.redact_many(["hop0", "other"])[0] == [f"hop{final}", "other"]


def test_a_chain_that_still_changes_in_round_four_is_refused_with_the_real_cap_never_half_masked(
    monkeypatch,
):
    """Round 4 changes `hop4` to `hop5` and no round reads that: the cap is a fail-closed margin, so the call is refused."""
    assert R._SETTLE_ROUNDS == 4
    _hop_chain(monkeypatch, 5)
    with pytest.raises(runmap.RedactionError) as err:
        R.redact("hop0")
    assert str(err.value) == "NotSettled"
    with pytest.raises(runmap.RedactionError):
        R.redact_many(["hop0", "other"])
    with pytest.raises(runmap.RedactionError) as err:
        runmap.redact_text("hop0", runmap.RunMap())
    assert (
        str(err.value) == "NotSettled"
    )  # redact_text re-raises the error as it is (fix round 3, N8)
    assert not isinstance(err.value, runmap.InputTooLarge)


def test_settle_is_a_real_fixed_point_a_rewrite_through_a_known_value_is_read_again(monkeypatch):
    """Round 3 M1: a pass that changes its text WITHOUT growing the map (a rewrite through a value the map already holds) ended
    the old loop unread (`len(mapping) == known`). Now the loop ends only on a round that changes no text."""
    _hop_chain(monkeypatch, 3)
    out = R.redact("hop0").text
    r = R._Redactor(None)
    assert r.find(out) == out  # what settle returned is a fixed point of the pattern pass


def test_the_todo_of_a_round_is_the_union_of_what_the_pass_and_the_sweep_changed(monkeypatch):
    """Before round 3, `todo` from round 2 on held only the strings the SWEEP changed: a string the pass changed in round 1 and
    the sweep left alone was never read again. `hop-a0` is rewritten twice by the pass (pass 1, round 1) and no sweep touches it;
    the chain of three beside it keeps the loop running into round 2, where the string must be read once more."""
    seen: list[str] = []
    real = R._Redactor.find

    def find(self, text):
        seen.append(text)
        if text in ("hop-a0", "hop-a1"):
            return "hop-a" + str(int(text[-1]) + 1)
        return real(self, text)

    monkeypatch.setattr(R._Redactor, "find", find)
    lines = ["hop-a0", f"password={V}", f"BSB: {BSB}{V}", f"paid {BSB}/{ACCOUNT}"]
    out, _ = R.redact_many(lines)
    assert out[0] == "hop-a2" and out[3] == "paid <BANKCODE_1>/<BANKACCT_1>"
    assert seen.count("hop-a2") == 1  # read in round 2 (and found unchanged), not dropped


def test_a_real_chain_of_three_is_three_rounds_two_that_change_and_one_that_confirms(
    monkeypatch,
):
    rounds = _rounds_spy(monkeypatch)
    R.redact(CHAIN3)
    assert rounds["n"] == 3 and R._SETTLE_ROUNDS - rounds["n"] >= 1  # at least one round of margin


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


def test_the_chain_of_three_is_four_pattern_passes_over_the_one_text_that_changed(monkeypatch):
    calls = _counted(monkeypatch)
    R.redact(CHAIN3)
    # pass 1; round 1 (code found); round 2 (account found); round 3 confirms (the text the last round changed)
    assert calls["find"] == 4 and calls["sweep"] == 3


def test_text_that_needs_no_more_passes_pays_nothing_extra(monkeypatch):
    calls = _counted(monkeypatch)
    R.redact("order shipped, nothing else here")
    assert calls == {"find": 1, "sweep": 1}
    calls.update(find=0, sweep=0)
    R.redact("password=" + V + " then nothing")
    assert calls == {"find": 2, "sweep": 1}  # the second pass found nothing new: no second sweep


# --- dz-2 / cb-M4: the tail of a compound secret in the other copies -----------------------------------------------

SHORT = "ab" + "9x"


@pytest.mark.parametrize(
    "lead, tail",
    [
        ("Bearer ", "qrs" + "tuvw"),  # 7 characters: the most BEARER can need
        ("Bearer ", "qr"),
        ("Basic ", "qrs"),
        ("authorization: ", "qrs"),
        ("sig=", "qrstuvwxy" + "za"),  # AZURESAS needs 16 characters: 4 + 11 = 15 raw
        ('{"auth":"', "qrs"),  # `"auth":"..."` needs 8
    ],
)
@pytest.mark.parametrize("copies", ["other-line", "all-lines"])
def test_a_tail_is_not_left_in_another_copy_of_the_compound_value(lead, tail, copies):
    close = '"}' if lead.startswith("{") else ""
    text = f"password={SHORT}\n{lead}{SHORT}{tail}{close}\nnote {SHORT}{tail}vw end"
    if copies == "all-lines":
        text += f"\nagain {SHORT}{tail}"
    mapping = runmap.RunMap()
    out = runmap.redact_text(text, mapping)
    free = "\x00".join(R._PLACEHOLDER.split(out)[0::2])
    assert tail not in free, out
    assert SHORT not in free
    assert any(v == SHORT + tail for v in mapping.values()), "the compound value is one entry"


def test_the_tail_leak_through_redact_many_across_strings():
    out, _ = R.redact_many(
        [f"password={SHORT}", f"Bearer {SHORT}qrstu", f"note {SHORT}qrstuvw end"]
    )
    assert not any("qrst" in t for t in out)
    assert out[2] == "note <BEARER_1>vw end"


def test_the_spelled_form_is_not_a_second_placeholder_and_restores_to_the_original():
    text = f"password={SHORT}\nBearer {SHORT}qrstu\nnote {SHORT}qrstu end"
    result = R.redact(text)
    assert result.text == "password=<SECRET_1>\nBearer <BEARER_1>\nnote <BEARER_1> end"
    assert result.restore("<BEARER_1>") == SHORT + "qrstu"


def test_a_rolled_back_compound_entry_leaves_no_ghost_spelling():
    r = R._Redactor({"<SECRET_1>": SHORT})
    counters = r._open_journal()
    placeholder = r._place("BEARER", SHORT + "qrstu", "<SECRET_1>qrstu")
    r._rollback(counters)
    assert placeholder not in r.mapping
    assert (
        r.sweep("x <SECRET_1>qrstu y") == "x <SECRET_1>qrstu y"
    )  # nothing writes a placeholder that is gone


def test_a_number_reissued_after_a_rollback_does_not_revive_the_ghost_spelling():
    """Round 3 M3/M4: the rolled-back `<BEARER_1>` (value SHORT+qrstu) is handed out again for ANOTHER value. The ghost
    `<SECRET_1>qrstu` must not turn into `<BEARER_1>`, which would restore to the wrong value."""
    r = R._Redactor({"<SECRET_1>": SHORT})
    counters = r._open_journal()
    first = r._place("BEARER", SHORT + "qrstu", "<SECRET_1>qrstu")
    r._rollback(counters)
    other = "zzzz" + "yyyy"
    again = r._place("BEARER", other, other)
    assert again == first == "<BEARER_1>" and r.mapping[again] == other  # the number was reissued
    swept = r.sweep("x <SECRET_1>qrstu y")
    assert swept == "x <SECRET_1>qrstu y"  # not `x <BEARER_1> y`
    # and a registration that is NOT rolled back still works after it
    r2 = R._Redactor({"<SECRET_1>": SHORT})
    p2 = r2._place("BEARER", SHORT + "qrstu", "<SECRET_1>qrstu")
    assert r2.sweep("x <SECRET_1>qrstu y") == f"x {p2} y"


def test_the_same_value_reissued_after_a_rollback_is_swept_by_its_new_placeholder():
    r = R._Redactor({"<SECRET_1>": SHORT})
    counters = r._open_journal()
    r._place("BEARER", SHORT + "qrstu", "<SECRET_1>qrstu")
    r._rollback(counters)
    again = r._place("BEARER", SHORT + "qrstu", "<SECRET_1>qrstu")
    assert r.sweep("x <SECRET_1>qrstu y") == f"x {again} y"


# --- round 3 M4 and round 4 M-A: the spelled-form scan is bounded -------------------------------------------------------


def _uuid_values(count: int) -> list[str]:
    rng = random.Random(4242)  # noqa: S311 - a seeded test generator, not a secret
    return [str(uuid.UUID(int=rng.getrandbits(128))) for _ in range(count)]


def _best_cpu(fn, repeat: int = 3) -> float:
    best = None
    for _ in range(repeat):
        start = time.thread_time()
        fn()
        took = time.thread_time() - start
        best = took if best is None else min(best, took)
    return best


def test_5000_compound_secrets_at_the_size_cap_the_trie_walk_is_not_dict_misses(monkeypatch):
    """5,000 `password=<uuid>.k_i` lines (about 250,000 characters, under the 262,144 cap) make 5,000 spelled forms keyed on `<UUID_n>`.
    Round 3's test swept only the text `find` left (`password=<SECRET_m>`), so it measured 5,000 dict MISSES and never walked the trie
    (round 3 review, nit 2). Here the text also holds, 5,000 times, the placeholder the forms are keyed on followed by the form's tail
    (`copy <UUID_n>.k_i`: a copy the first sweep had already cut), so every token walks its trie and every one is replaced. Measured as a
    RATIO to the same sweep with no spelled form, so a slow machine does not matter. The old loop searched every form in the whole text (5,000 x
    250,000 characters per sweep); this walk costs tokens x (one offset) x (the form's length)."""
    values = _uuid_values(5000)
    text = "\n".join(f"password={v}.k_{i % 10}" for i, v in enumerate(values))
    assert 240_000 < len(text) <= defaults.MAX_REDACT_CHARS
    r = R._Redactor(None)
    out = r.find(text)
    assert len(r.mapping) == 10_000  # a UUID and a compound secret per line
    copies = "\n".join(f"copy {r.reverse[v]}.k_{i % 10}" for i, v in enumerate(values))
    probe = out + "\n" + copies
    swept = r.sweep(probe)  # builds the finders once, as the first sweep of a call does
    assert swept.count("copy <SECRET_") == 5000, "every copy walks its trie and is replaced whole"
    monkeypatch.setattr(
        r, "_overlaps", lambda *a: []
    )  # G9: both runs time the scan alone (the read-back has its own test)
    with_forms = _best_cpu(lambda: r.sweep(probe))
    held, r._spelled = r._spelled, {}
    without = _best_cpu(lambda: r.sweep(probe))
    r._spelled = held
    assert with_forms < 4 * without + 0.005, (with_forms, without)
    assert without > 0.015, without  # big enough for the slack to mean something


# --- round 5 design M1: an honest log is MASKED, a hostile one is bounded (the work is counted; no cap per offset or per form) -----------


JWT = (
    "eyJ" + "hbGciOiJIUzI1NiJ9" + "." + "eyJzdWIiOiJ1c2VyMSJ9" + "." + "c2lnbmF0dXJlMTIzNDU2Nzg5"
)  # a made-up JWT


def _cookie_log(lines: int, *, same_prefix: bool = False) -> str:
    """One session (the SAME `<JWT_1>` throughout), a Cookie header per request, each preceded by other cookies: the run of unrelated text
    before the token has a different length on every line (`same_prefix` makes it one length: the control of the ratio test)."""
    rows = [f"GET /start token={JWT}"]
    for k in range(lines):
        pad = "x" * (150 if same_prefix else k)
        rows.append(f"Cookie: _ga=GA1.2{pad}; theme=dark; sid={JWT}")
    return "\n".join(rows)


def _signed_log(lines: int) -> tuple[str, str]:
    """(text, the UUID): `password=<UUID>.<sig_n>` on every line, one UUID, a different suffix each: a compound value per line under one token."""
    value = _uuid_values(1)[0]
    return "\n".join(f"password={value}.sig{n}" for n in range(lines)), value


def test_an_honest_cookie_log_with_a_different_prefix_length_on_every_line_is_masked_not_refused():
    """Round 4 design M1, scenario A. Each distinct prefix length used to be a new OFFSET under `<JWT_1>`: the 33rd was refused
    (`SpelledFormsTooMany`) and the whole document with it. Now the prefixes are one reversed trie and no count is capped."""
    text = _cookie_log(300)
    assert len({len(line) for line in text.splitlines()[1:]}) == 300  # 300 distinct prefix lengths
    out = runmap.redact_text(text, runmap.RunMap())
    assert JWT not in out and "theme=dark" not in out and "GA1.2" not in out, out
    assert R.redact(text).text.count("Cookie:") == 300
    assert JWT not in R.redact_many([text])[0][0]


def test_an_honest_signed_id_log_with_a_different_suffix_on_every_line_is_masked_not_refused():
    """Round 4 design M1, scenario B: 300 lines `password=<UUID_1>.<sig_n>`: 300 forms under one first token (the cap was 256)."""
    text, value = _signed_log(300)
    out = runmap.redact_text(text, runmap.RunMap())
    assert value not in out and "sig17" not in out and "sig299" not in out, out
    assert out.count("password=<") == 300


def _swept_cpu(probe: str, registered: str) -> float:
    r = R._Redactor(None)
    r.find(registered)
    r.sweep("")  # builds the rules once
    r._overlaps = (
        lambda *a: []
    )  # G9: the scan alone, in both runs of the ratio (the read-back: test_g9_the_read_back_costs_...)
    return _best_cpu(lambda: r.sweep(probe))


def _copies_of(log: str) -> str:
    """The cookie lines of `log` as the first sweep leaves other copies: `Cookie: <prefix>; sid=<JWT_1>`."""
    return "\n".join(line.replace(JWT, "<JWT_1>") for line in log.splitlines()[1:])


def test_the_scan_does_not_depend_on_how_many_distinct_prefix_lengths_are_registered():
    """The cost of a token is the prefix that really matches before it, not the number of offsets registered under it: the copies of 300
    DIFFERENT prefix lengths cost about what the copies of ONE length cost. The honest case is repeated to about 230,000 characters (some
    40 ms of CPU, 4 times the copies of the 300 lines) and the slack is 5 ms, so a regression of about 5 times is over the bound (round 5 had
    the 57,000-character case, 7 ms, and a slack of 0.05 s that hid it). A scan that walks every offset for every token (round 4's) is far
    slower on the first and fails the ratio (a mutant of the scan, recorded in evidence G7-1.md)."""
    many, one = _cookie_log(300), _cookie_log(300, same_prefix=True)
    with_many = _swept_cpu("\n".join([_copies_of(many)] * 4), many)
    with_one = _swept_cpu("\n".join([_copies_of(one)] * 4), one)
    assert with_one > 0.015, (
        with_one
    )  # the control is big enough for the slack below to mean something
    assert with_many < 4 * with_one + 0.005, (with_many, with_one)


def _hostile_forms(count: int, tail: int = 1) -> str:
    """`count` lines `password=a^k<SECRET_1>Z^tail`, k = 1..count: each is a compound secret whose written form holds the SAME first token at
    another offset, with a suffix of `tail` characters (round 3 design review, M-A)."""
    return "\n".join(f"password={'a' * k}<SECRET_1>{'Z' * tail}" for k in range(1, count + 1))


def test_hostile_forms_with_500_distinct_prefix_lengths_are_scanned_in_linear_time():
    """500 forms with 500 offsets under one token (125 KB), then 130 KB of `a^500<SECRET_1>` that matches none of them to the end. The scan
    of round 4 walked every offset for every token (about 3e7 steps); now it is one backward walk per token. The ratio is against the same
    sweep with no forms registered (measured numbers: evidence G7-1.md); a quadratic scan is far over it."""
    r = R._Redactor({"<SECRET_1>": SHORT})
    r.find(_hostile_forms(500))
    text = ("a" * 500 + "<SECRET_1>") * (130_000 // 510)
    assert len(text) > 129_000
    r.sweep("")
    with_forms = _best_cpu(lambda: r.sweep(text))
    held, r._spelled = r._spelled, {}
    without = _best_cpu(lambda: r.sweep(text))
    r._spelled = held
    assert with_forms < 2.0, with_forms  # absolute guard: seconds, not milliseconds
    assert with_forms < 4 * without + 0.01, (with_forms, without)  # measured 1.1 times


def _grid_forms(prefixes: int, suffixes: int) -> str:
    """`prefixes` x `suffixes` lines `password=a^k<SECRET_1>Z^m` (k = 1..prefixes, m = 1..suffixes): every pair is a different written form under ONE
    token, so every terminal of the suffix trie holds `prefixes` entries."""
    return "\n".join(
        f"password={'a' * k}<SECRET_1>{'Z' * m}"
        for k in range(1, prefixes + 1)
        for m in range(1, suffixes + 1)
    )


def _deep_hostile() -> tuple[str, str]:
    """(forms, probe): 70 x 40 = 2,800 forms (about 220,000 characters, inside the input cap), then a probe of the size cap whose every token
    matches all 70 prefixes and 40 suffix characters: every token walks 110 steps and meets 40 terminals of 70 entries (about 6e6 units in all)."""
    block = "a" * 70 + "<SECRET_1>" + "Z" * 40 + "\n"
    return _grid_forms(70, 40), block * (defaults.MAX_REDACT_CHARS // len(block))


def test_the_work_of_the_scan_is_bounded_a_hostile_text_is_refused_not_walked_to_the_end(
    monkeypatch,
):
    """The total work of a scan (steps of both walks, and tokens) is counted and refused past `defaults.SPELLED_MAX_WORK`
    (InputTooLarge("SpelledWorkTooMuch")). The deep text needs 6.3 million units (counted: evidence g7r6_units.py): refused at the real limit, and scanned to the end when the limit
    is raised (so the refusal is the count, not a property of the text)."""
    from hadavin_sdk.guard.runmap import InputTooLarge

    forms, probe = _deep_hostile()
    r = R._Redactor({"<SECRET_1>": SHORT})
    r.find(forms)
    r.sweep("")
    start = time.thread_time()
    with pytest.raises(InputTooLarge, match="SpelledWorkTooMuch"):
        r.sweep(probe)
    assert time.thread_time() - start < 3.0
    monkeypatch.setattr(defaults, "SPELLED_MAX_WORK", 10**9)
    assert r.sweep(probe)


def test_the_honest_logs_need_a_small_part_of_the_work_limit(monkeypatch):
    """The limit is CHOSEN (not derived) with a margin over the honest shapes measured: the honest logs at the size cap (cookie copies of 300 prefix
    lengths, signed ids with 300 suffixes) need under a tenth of it (6 percent and 2 percent measured, evidence G7-1.md): they scan to the end
    with the limit cut to a tenth."""
    cookie_probe = "\n".join(
        f"Cookie: _ga=GA1.2{'x' * (k % 300)}; theme=dark; sid=<JWT_1>" for k in range(1700)
    )
    signed_probe = "\n".join(f"copy <UUID_1>.sig{k % 300}" for k in range(8000))
    monkeypatch.setattr(defaults, "SPELLED_MAX_WORK", defaults.SPELLED_MAX_WORK // 10)
    for registered, probe, token in (
        (_cookie_log(300), cookie_probe, "<JWT_1>"),
        (_signed_log(300)[0], signed_probe, "<UUID_1>"),
    ):
        probe = probe[: defaults.MAX_REDACT_CHARS]
        r = R._Redactor(None)
        r.find(registered)
        r.sweep("")
        swept = r._spelled_sweep(probe, None)  # does not raise
        assert token not in swept[: len(swept) - 400], "the copies were really walked and replaced"


def test_the_spelled_walk_checks_the_deadline_inside_a_walk(monkeypatch):
    """The limit is not the only bound: with it raised the same deep text would cost about 0.9 s (6.3 million units at 0.15 us), and a deadline 0.05 s away stops it
    (InputTooLarge) well before that. The walk counts its own steps, not only the tokens."""
    from hadavin_sdk.guard.runmap import InputTooLarge

    monkeypatch.setattr(defaults, "SPELLED_MAX_WORK", 10**9)
    forms, probe = _deep_hostile()
    r = R._Redactor({"<SECRET_1>": SHORT})
    r.find(forms)
    r.sweep("")
    start = time.thread_time()
    with pytest.raises(InputTooLarge):
        r.sweep(probe, start + 0.05)
    assert time.thread_time() - start < 1.5


def test_the_spelled_scan_checks_the_deadline_for_a_token_that_has_no_form():
    """Before round 4 the check sat after `if by_offset is None: continue`: a text of tokens with no form was never checked."""
    from hadavin_sdk.guard.runmap import InputTooLarge

    r = R._Redactor({"<SECRET_1>": SHORT})
    r._place("BEARER", SHORT + "qrstu", "<SECRET_1>qrstu")
    text = "<EMAIL_9> " * 3000
    assert r._spelled_sweep(text, time.thread_time() + 600.0) == text
    with pytest.raises(InputTooLarge):
        r._spelled_sweep(text, time.thread_time() - 1.0)


def test_the_token_check_cadence_counts_tokens_with_no_form_too(monkeypatch):
    """Round 4 nit N4: the test above sees only the FIRST token's check. A stepping clock (one reading per call) counts the checks of
    3,000 tokens that hold no form: the first token, then every `_SPELL_CHECK_EVERY` (1,024) units = 3 readings. A mutant that counts only
    the tokens that have a form reads once."""
    r = R._Redactor({"<SECRET_1>": SHORT})
    r._place("BEARER", SHORT + "qrstu", "<SECRET_1>qrstu")
    readings = _stepping_clock(monkeypatch)
    text = "<EMAIL_9> " * 3000
    assert r._spelled_sweep(text, 1e9) == text
    assert readings["n"] == 3, readings


def test_the_walk_over_the_whole_text_reads_the_clock_in_proportion_to_the_work(monkeypatch):
    """The steps of a walk are counted too: the deep hostile text (6.3 million units) reads the clock thousands of times, not once per token."""
    monkeypatch.setattr(defaults, "SPELLED_MAX_WORK", 10**9)
    forms, probe = _deep_hostile()
    r = R._Redactor({"<SECRET_1>": SHORT})
    r.find(forms)
    r.sweep("")
    readings = _stepping_clock(monkeypatch)
    r._spelled_sweep(probe, 1e12)
    assert readings["n"] > 3000, readings


def test_many_registrations_under_one_first_token_are_not_refused_and_each_is_swept():
    """No count is capped any more: 2,000 forms under one token (the cap was 256) register, and each copy is swept whole."""
    r = R._Redactor({"<SECRET_1>": SHORT})
    placeholders = [
        r._place("BEARER", f"{SHORT}tail{n}", f"<SECRET_1>tail{n}") for n in range(2000)
    ]
    swept = r._spelled_sweep(" ".join(f"x <SECRET_1>tail{n}" for n in range(2000)), None)
    assert swept == " ".join(f"x {p}" for p in placeholders)


# --- round 5 design M2: an overlap of two forms is registered whole, nothing of it stays readable -----------------------------------


def test_the_overlap_rule_is_leftmost_then_longest_and_an_overlap_is_one_entry_of_its_own():
    """Round 3 design M-B: the first matching offset used to win, so with F1 `<SECRET_1>ab` (offset 0) and F2 `xyz<SECRET_1>` (offset 3) the text
    `xyz<SECRET_1>ab` lost F2 and `xyz` stayed readable. Round 4 took F2 and skipped F1, which left `ab` readable (round 4 design M2: with a
    long tail, a long tail). Now the run of overlapping candidates is ONE span, registered on the spot as a compound value of its own
    (`xyz` + V + `ab`) and replaced by its placeholder."""
    r = R._Redactor({"<SECRET_1>": SHORT})
    f1 = r._place("BEARER", SHORT + "ab", "<SECRET_1>ab")
    f2 = r._place("BEARER", "xyz" + SHORT, "xyz<SECRET_1>")
    union = r._spelled_sweep("xyz<SECRET_1>ab", None)
    assert union not in (f1, f2), union
    assert R._PLACEHOLDER.fullmatch(union), union  # the whole span is one placeholder
    assert (
        r.mapping[union] == "xyz" + SHORT + "ab"
    )  # registered as a compound value of its own, its kind the first form's
    assert r._spelled_sweep("a <SECRET_1>ab b", None) == f"a {f1} b"  # no overlap: as before
    assert r._spelled_sweep("xyz<SECRET_1> xyz<SECRET_1>", None) == f"{f2} {f2}"
    assert (
        r._spelled_sweep("xyz<SECRET_1>ab and again xyz<SECRET_1>ab", None)
        == f"{union} and again {union}"
    )  # the same entry
    longer = r._place("BEARER", SHORT + "abcd", "<SECRET_1>abcd")
    assert r._spelled_sweep("<SECRET_1>abcd", None) == longer  # at one start the longest form
    assert r._spelled_sweep("<SECRET_1>abce", None) == f"{f1}ce"


def test_an_overlap_with_a_long_tail_leaves_nothing_readable():
    """Round 4 design M2: F1 `<SECRET_1>` + 20 characters, F2 `xyz<SECRET_1>`: the text `xyz<SECRET_1>` + the 20 characters is masked whole."""
    tail = "qrstuvwxyz" + "abcdefghij"
    r = R._Redactor({"<SECRET_1>": SHORT})
    r._place("BEARER", SHORT + tail, "<SECRET_1>" + tail)
    r._place("BEARER", "xyz" + SHORT, "xyz<SECRET_1>")
    out = r._spelled_sweep(f"see xyz<SECRET_1>{tail} end", None)
    assert out.startswith("see <") and out.endswith("> end"), out
    assert tail not in out and "xyz" not in out
    assert r.mapping[out[4:-4]] == "xyz" + SHORT + tail


def test_a_longer_form_over_the_same_run_is_one_span():
    """F1 `<S>ab`, F2 `xyz<S>`, F3 `<S>abcdef`: the candidates F2 and F3 overlap and F1 is covered by F3: ONE entry for the whole run."""
    r = R._Redactor({"<SECRET_1>": SHORT})
    r._place("BEARER", SHORT + "ab", "<SECRET_1>ab")
    r._place("BEARER", "xyz" + SHORT, "xyz<SECRET_1>")
    r._place("BEARER", SHORT + "abcdef", "<SECRET_1>abcdef")
    out = r._spelled_sweep("xyz<SECRET_1>abcdef", None)
    assert R._PLACEHOLDER.fullmatch(out) and r.mapping[out] == "xyz" + SHORT + "abcdef"


def test_the_overlap_through_the_whole_call_masks_every_copy_and_restores_it():
    """Through `redact_text` and `redact` (settle rounds, the run map): two `Bearer` lines are matched only after the first sweep wrote `<SECRET_1>`
    (`Bearer <SECRET_1>ab` and `Bearer xyz<SECRET_1>`, 12 characters or more with the token), so F1 and F2 are registered in the SAME round and
    the copy `xyz<SECRET_1>ab` overlaps both. Before round 5 it became `<BEARER_2>ab`: the tail `ab` of a value the map holds, readable."""
    text = f"password={SHORT}\nBearer {SHORT}ab\nBearer xyz{SHORT}\nsee xyz{SHORT}ab end\nagain xyz{SHORT}ab"
    mapping = runmap.RunMap()
    out = runmap.redact_text(text, mapping)
    assert out.endswith("see <BEARER_3> end\nagain <BEARER_3>"), out
    assert mapping["<BEARER_3>"] == "xyz" + SHORT + "ab"
    result = R.redact(text)
    assert result.text == out and result.restore(result.text) == text


def test_a_rolled_back_form_is_deleted_not_left_as_a_ghost():
    """Round 3 design N1: `_rollback` deletes the `_spelled` entry (the journal holds the placeholder). The contrived reissue that revived a
    ghost: the placeholders of the rolled-back line are handed out again, `<SECRET_1>` to ANOTHER value and `<BEARER_1>` to the value
    `V+qrstu` with no spelled form; the ghost `<SECRET_1>qrstu` would then have been swept to `<BEARER_1>`, a value that is not
    `other+qrstu`."""
    r = R._Redactor(None)
    counters = r._open_journal()
    r._place("SECRET", SHORT, SHORT)
    r._place("BEARER", SHORT + "qrstu", "<SECRET_1>qrstu")
    assert r._spelled
    r._rollback(counters)
    assert r._spelled == {} and r._spelled_at == {}  # nothing left of it
    other = "zzzz" + "yyyy"
    r._place("SECRET", other, other)
    r._place("BEARER", SHORT + "qrstu", SHORT + "qrstu")  # the same value again, no spelled form
    assert r.mapping == {"<SECRET_1>": other, "<BEARER_1>": SHORT + "qrstu"}
    assert r.sweep("x <SECRET_1>qrstu y") == "x <SECRET_1>qrstu y"  # not `x <BEARER_1> y`


def test_the_spelled_scan_is_the_same_result_as_before_on_a_cut_copy():
    """A copy the first sweep already cut: the compound's other copy is swept whole, many forms, one text."""
    text = "\n".join(
        f"password={SHORT}{n}\nBearer {SHORT}{n}qrst\nnote {SHORT}{n}qrst end" for n in range(30)
    )
    result = R.redact(text)
    assert "qrst" not in "\x00".join(R._PLACEHOLDER.split(result.text)[0::2])


# --- dz-3 / cb-M2: the deadline of the extra rounds ------------------------------------------------------------------


def test_a_spent_deadline_refuses_the_second_pass_never_skips_it():
    from hadavin_sdk.guard.runmap import InputTooLarge

    spent = time.thread_time() - 1.0
    with pytest.raises(InputTooLarge):
        R.redact(f"password={V} then nothing", _deadline=spent)
    with pytest.raises(InputTooLarge):
        R.redact_many([f"password={V}", "other"], _deadline=spent)
    # a text that needs no second pass is not refused by the check of the extra rounds; the first sweep (which carries the call's deadline since
    # round 4) has no value to look for in an empty map, so it has no work to bound and reads no clock
    assert R.redact("nothing to see", _deadline=spent).text == "nothing to see"


def test_a_deadline_in_the_future_changes_nothing():
    future = time.thread_time() + 600.0
    assert R.redact(CHAIN3, _deadline=future).text == R.redact(CHAIN3).text
    assert R.redact_many([CHAIN3], _deadline=future)[0] == R.redact_many([CHAIN3])[0]


def test_sweep_takes_an_optional_deadline_checked_inside_the_value_loop():
    from hadavin_sdk.guard.runmap import InputTooLarge

    values = {f"<TENANT_{n}>": f"val{n:04d}" for n in range(1, 300)}
    text = " ".join(values.values()) * 40
    r = R._Redactor(values)
    expected = R._Redactor(values).sweep(text)
    assert r.sweep(text, None) == expected  # None: as before
    assert r.sweep(text, time.thread_time() + 600.0) == expected
    with pytest.raises(InputTooLarge):
        r.sweep(text, time.thread_time() - 1.0)  # a spent deadline stops the sweep


def _stepping_clock(monkeypatch) -> dict[str, int]:
    """`time.thread_time` as seen by the redactor: one second more at every reading. Returns the reading counter."""
    readings = {"n": 0}

    def clock() -> float:
        readings["n"] += 1
        return float(readings["n"])

    # the module attribute, as `tests/test_runmap_enforce_map.py` patches `runmap.time`: `time.thread_time` itself stays real for everything else
    monkeypatch.setattr(R, "time", types.SimpleNamespace(thread_time=clock))
    return readings


def test_the_deadline_trips_inside_the_value_loop_not_at_the_segment_check(monkeypatch):
    """Round 3 M6: the text is ONE segment, so a spent deadline trips at the segment check first and the old test could not tell the
    two apart. A stepping clock (one second per reading) with a deadline of 2.5 passes the build check (reading 1) and the segment check
    (reading 2) and trips at reading 3: the first check of the value loop."""
    from hadavin_sdk.guard.runmap import InputTooLarge

    values = {f"<TENANT_{n}>": f"val{n:04d}" for n in range(1, 300)}  # under 512: one build check
    text = " ".join(values.values())
    r = R._Redactor(values)
    readings = _stepping_clock(monkeypatch)
    with pytest.raises(InputTooLarge):
        r.sweep(text, 2.5)
    assert readings["n"] == 3


def test_the_deadline_trips_at_the_segment_check_of_a_segment_with_no_known_value(monkeypatch):
    """Round 3 nit 1: the test above pins the value-loop check only. Here the free segment holds no value at all, so the value loop has
    no check to run: a deadline of 1.5 (reading 1 is the build check, passed) trips at reading 2, the segment check, and without that
    check the sweep would return."""
    from hadavin_sdk.guard.runmap import InputTooLarge

    values = {f"<TENANT_{n}>": f"val{n:04d}" for n in range(1, 300)}
    r = R._Redactor(values)
    readings = _stepping_clock(monkeypatch)
    with pytest.raises(InputTooLarge):
        r.sweep("nothing known in this text at all", 1.5)
    assert readings["n"] == 2


def test_the_deadline_is_checked_in_build(monkeypatch):
    """`_build` of a map that grew is not free (a rule per stored value); a text that is only a placeholder has no free segment, so
    only the build can trip. The first readings of a spent deadline raise there."""
    from hadavin_sdk.guard.runmap import InputTooLarge

    values = {f"<TENANT_{n}>": f"val{n:04d}" for n in range(1, 1500)}
    r = R._Redactor(values)
    with pytest.raises(InputTooLarge):
        r.sweep("<TENANT_1>", time.thread_time() - 1.0)


def test_settle_passes_the_calls_deadline_to_its_sweeps(monkeypatch):
    """Round 3 M5: `settle` passes the call's deadline into its sweeps, so a sweep over a large text stops inside, not after
    (that a sweep given a deadline stops inside is the two tests above)."""
    calls = {"deadlines": []}
    sweep = R._Redactor.sweep

    def spy(self, out, deadline=None):
        calls["deadlines"].append(deadline)
        return sweep(self, out, deadline)

    monkeypatch.setattr(R._Redactor, "sweep", spy)
    future = time.thread_time() + 600.0
    R.redact(CHAIN3, _deadline=future)
    # the first sweep carries the call's deadline too (round 4, design M-A); so does every sweep of a round
    assert all(d == future for d in calls["deadlines"])
    assert len(calls["deadlines"]) >= 3
    calls["deadlines"].clear()
    R.redact_many([CHAIN3, "other"], _deadline=future)
    assert calls["deadlines"] and all(d == future for d in calls["deadlines"])


def test_settle_refuses_before_a_round_when_the_deadline_is_spent_and_never_calls_find(
    monkeypatch,
):
    """Round 3 codebase M1: the check at the top of each round was not pinned by any test that raises (the spent-deadline test above raises
    inside the first sweep). A direct call: a built map, a spent deadline, a stub `find` that records its calls. `settle` must raise
    InputTooLarge and never call `find`."""
    from hadavin_sdk.guard.runmap import InputTooLarge

    r = R._Redactor({"<TENANT_1>": "val0001"})
    r.sweep(
        "built"
    )  # builds the rules (a build falls back to the call's own deadline, so none is set yet)
    assert r._built_for == len(r.mapping)
    r._deadline = time.thread_time() - 1.0  # now spent
    calls: list[str] = []
    monkeypatch.setattr(R._Redactor, "find", lambda self, text: calls.append(text) or text)
    with pytest.raises(InputTooLarge):
        r.settle(["original"], ["swept"])  # the swept text differs: round 1 is due
    assert calls == []
    # and a deadline in the future runs the round
    r2 = R._Redactor({"<TENANT_1>": "val0001"}, None, time.thread_time() + 600.0)
    assert r2.settle(["original"], ["swept"]) == ["swept"]
    assert calls == ["swept"]


def test_redact_many_reads_a_string_again_when_a_later_fold_scan_finds_the_bank_word():
    """Round 3 codebase M5: `_fold_scan` sets `bank_near` while a LATER string is read (a full-width bank word seen only in its folded view), and an
    account in an EARLIER string, read before that, was never read again (it was unchanged, so not in `todo`). The same two strings in the other
    order masked it. Now every string is read again when the flag flipped (in the first pass and in a round)."""
    fullwidth = "\uff22\uff33\uff22"  # BSB
    account = "1234" + "5678"
    early, late = f"acct {account} paid", f"{fullwidth} 062-000 ok"
    for items in ([early, late], [late, early]):
        out, mapping = R.redact_many(items)
        assert not any(account in t for t in out), items
        assert account in mapping.values()


def test_a_flip_of_bank_near_during_a_round_puts_every_string_back_in_todo(monkeypatch):
    """The same rule inside `settle`: a string read in a round flips the flag, so the strings that no round changed are read again."""
    r = R._Redactor(None)
    calls: list[str] = []
    real = R._Redactor.find

    def find(self, text):
        calls.append(text)
        if text == "flip2":
            self.bank_near = True
            return "flipped"
        return real(self, text)

    monkeypatch.setattr(R._Redactor, "find", find)
    assert r.settle(["x", "y", "flip"], ["x2", "y2", "flip2"]) == ["x2", "y2", "flipped"]
    assert (
        calls.count("x2") == 2 and calls.count("y2") == 2
    )  # read in round 1, and again in round 2 after the flip


# --- round 5 design M3: a flip does not run a second unchecked pass over every string; the segment check is pinned ---------------------


def _flip_items() -> list[str]:
    """Item 1 holds a bank word only in a folded view (full-width BSB): `bank_near` flips while it is read. Item 0 is re-read, 1, 2 and 3 are not."""
    fullwidth = "\uff22\uff33\uff22"
    return ["acct " + ACCOUNT + " paid", f"{fullwidth} 062-000 ok", "tail one", "tail two"]


def test_redact_many_checks_the_deadline_between_the_two_reads_when_bank_near_flips(monkeypatch):
    """Round 4 design M3: on a flip the first `find` pass over EVERY string ran a second time, both unchecked, before the first deadline
    check. Now the strings read before the flip are re-read one by one after a check. The check is made to refuse here (the fold scan of the
    full-width string reads the clock itself, so a really spent deadline would stop inside it): no string is read a second time."""
    from hadavin_sdk.guard.runmap import InputTooLarge

    items = _flip_items()
    calls: list[str] = []
    real = R._Redactor.find

    def find(self, text):
        calls.append(text)
        return real(self, text)

    def refuse(self):
        raise InputTooLarge("InputTooLarge")

    monkeypatch.setattr(R._Redactor, "find", find)
    monkeypatch.setattr(R._Redactor, "_check_deadline", refuse)
    with pytest.raises(InputTooLarge):
        R.redact_many(items, _deadline=time.thread_time() + 600.0)
    assert calls == items, "each string was read once; the re-read was refused by the check"


def test_redact_many_re_reads_only_the_strings_read_before_the_flip(monkeypatch):
    """Items 0 and 1 hold the bank context as a full-width BSB in item 1: item 0 is read again, item 1 (read with the flag set) is not."""
    items = _flip_items()
    calls: list[str] = []
    real = R._Redactor.find

    def find(self, text):
        calls.append(text)
        return real(self, text)

    monkeypatch.setattr(R._Redactor, "find", find)
    out, mapping = R.redact_many(items)
    assert [calls.count(i) for i in items] == [
        2,
        1,
        1,
        1,
    ]  # not [2, 2, 1, 1] (string 1 itself was read with the flag set)
    assert (
        ACCOUNT in mapping.values() and ACCOUNT not in out[0]
    )  # the early string still got the bank context


def test_the_segment_check_reads_the_clock_at_the_first_free_segment_then_every_32nd(monkeypatch):
    """Round 4 design nit 1: `i % 64 == 0` and an empty first segment skipped before it: a text that STARTS with a placeholder, or has fewer
    than 32 free segments after a leading one, read no clock in the segment loop. Pinned with a stepping clock: the readings are
    ceil(free segments / 32), with or without a leading placeholder."""
    values = {f"<TENANT_{n}>": f"val{n:04d}" for n in range(1, 300)}
    r = R._Redactor(values)
    r.sweep("")  # builds the rules before the clock is replaced
    readings = _stepping_clock(monkeypatch)
    for free in (1, 31, 32, 33, 64, 65):
        for lead in ("", "<EMAIL_9> "):
            readings["n"] = 0
            text = lead + " <EMAIL_9> ".join(["w"] * free)
            assert r.sweep(text, 1e9) == text
            assert readings["n"] == -(-free // 32), (free, lead, readings)


def test_a_text_that_starts_with_a_placeholder_trips_the_segment_check(monkeypatch):
    from hadavin_sdk.guard.runmap import InputTooLarge

    r = R._Redactor({f"<TENANT_{n}>": f"val{n:04d}" for n in range(1, 300)})
    r.sweep("")
    readings = _stepping_clock(monkeypatch)
    with pytest.raises(InputTooLarge):
        r.sweep("<EMAIL_9> nothing known here", 0.5)  # the first reading is past the deadline
    assert readings["n"] == 1


def test_redact_with_a_pre_seeded_map_a_clean_text_and_a_spent_deadline_is_refused_not_returned():
    """Round 4 codebase answer 3, the direct test that was missing: a spent deadline cannot return an unmasked text. The map holds a value, the
    text is clean (or is a placeholder only, or holds the value), `redact` and `redact_many` refuse; the same calls with a deadline in the
    future return the masked text."""
    from hadavin_sdk.guard.runmap import InputTooLarge

    seeded = {"<SECRET_1>": SHORT}
    spent, future = time.thread_time() - 1.0, time.thread_time() + 600.0
    for text in ("nothing to see here", "<SECRET_1>", f"the value {SHORT} is here"):
        with pytest.raises(InputTooLarge):
            R.redact(text, mapping=dict(seeded), _deadline=spent)
        with pytest.raises(InputTooLarge):
            R.redact_many([text], dict(seeded), _deadline=spent)
        assert R.redact(text, mapping=dict(seeded), _deadline=future).text == text.replace(
            SHORT, "<SECRET_1>"
        )


# --- cb nits: patterns the chain tests did not name -----------------------------------------------------------------


def test_azuresas_sig_found_only_after_the_first_sweep():
    short = "hun" + "ter" + "99"
    out = runmap.redact_text(
        f"password={short}\nGET /x?sig={short}abcdef", mapping := runmap.RunMap()
    )
    assert short not in out and "abcdef" not in out
    assert "<AZURESAS_1>" in out and short + "abcdef" in mapping.values()


def test_json_auth_found_only_after_the_first_sweep():
    short = "hun" + "t9"
    out = runmap.redact_text(
        f'password={short}\n{{"auth":"{short}ab"}}', mapping := runmap.RunMap()
    )
    assert short not in out and "ab" not in out.replace("<", "").replace(">", "").replace(
        "auth", ""
    )
    assert short + "ab" in mapping.values()


def test_boundary_class_is_over_masked_fail_safe_and_pinned():
    """Documented (ticket G7, "Limits that remain"): a boundary pattern (SSN, PHONE, EMAIL, IBAN, UUID, IPV4, APIKEY) can
    match where the first pass saw a word character and the sweep then left a placeholder: more is masked than one fresh call
    on the same text would mask. Fail safe; pinned so a change is looked at."""
    word = "hun" + "ter"
    ssn = "123" + "-" + "45" + "-" + "6789"
    out = runmap.redact_text(f"password={word}\nref {word}{ssn}", mapping := runmap.RunMap())
    assert out == "password=<SECRET_1>\nref <SECRET_1><SSN_1>"
    assert ssn in mapping.values()
    fresh = runmap.redact_text(f"ref {word}{ssn}", runmap.RunMap())
    assert (
        "<SSN_1>" not in fresh
    )  # a fresh call would not mask it: the over-masking is real and documented


# --- dz-4 / cb-M3 / round 3 M1 + M2: a generator of 4 to 8 lines, with a pre-seeded run map, against a reference loop ------

_RARE = "qxzjkvw"
BSB_2 = "033" + "-" + "111"


def _token(rng: random.Random, low: int, high: int, firsts: list[str]) -> str:
    """A tail of `low` to `high` rare letters. Its first letter is taken from `firsts`, so no tail of one input is the start of
    another (V + tail 1 would then sit inside V + tail 2: a compound inside a compound, a different and stated limit)."""
    return firsts.pop() + "".join(rng.choice(_RARE) for _ in range(rng.randint(low, high) - 1))


def _lines(rng: random.Random) -> tuple[list[str], dict[str, str], list[str]]:
    """(lines, a run map to start from, tails that must not stay readable). 4 to 8 lines; the first value is always declared by a
    key=V line. Half of the inputs start from a map that already holds some of the values (the pass then rewrites through a
    value the map knows: a reverse hit, no map growth)."""
    value = "".join(rng.choice("abcdefghmnprstu") for _ in range(3)) + rng.choice("0123456789")
    lines, tails = [f"password={value}"], []
    firsts = rng.sample(_RARE, len(_RARE))
    pool = [
        "bank-glued",
        "bank-glued-2",
        "bank-code",
        "account-after-code",
        "account-keyword",
        "code-2-then-account",
        "bearer",
        "basic",
        "authorization",
        "sig",
        "auth",
        "copy",
        "copy",
        "second-key",
    ]
    compound_tail = ""
    for _ in range(rng.randint(3, 7)):
        kind = rng.choice(pool)
        if kind == "bank-glued":
            lines.append(f"BSB: {BSB}{value}")
        elif kind == "bank-glued-2":
            lines.append(f"BSB: {BSB_2}{value}")
        elif kind == "bank-code":
            lines.append(f"BSB: {BSB}")
        elif kind == "account-after-code":
            lines.append(f"paid {BSB}/{ACCOUNT}")
        elif kind == "account-keyword":
            lines.append(f"ref {BSB} acct {ACCOUNT}")
        elif kind == "code-2-then-account":
            lines.append(f"paid {BSB_2}/{ACCOUNT}")
        elif kind == "bearer":
            tail = _token(rng, 2, 7, firsts)
            tails.append(tail)
            compound_tail = compound_tail or tail
            lines.append(f"Bearer {value}{tail}")
        elif kind in ("basic", "authorization"):
            tail = _token(rng, 2, 3, firsts)
            tails.append(tail)
            lines.append(f"{'Basic ' if kind == 'basic' else 'authorization: '}{value}{tail}")
        elif kind == "sig":
            tail = _token(rng, 6, 11, firsts)
            tails.append(tail)
            lines.append(f"GET /x?sig={value}{tail}")
        elif kind == "auth":
            tail = _token(rng, 2, 3, firsts)
            tails.append(tail)
            lines.append(f'{{"auth":"{value}{tail}"}}')
        elif kind == "copy":
            more = "".join(rng.choice("ghl") for _ in range(rng.randint(0, 4)))
            lines.append(f"note {value}{compound_tail}{more} end")
        else:
            tail = _token(rng, 5, 8, firsts)
            tails.append(tail)
            lines.append(f"token={value}{tail}")
    rng.shuffle(lines)
    seed: dict[str, str] = {}
    if rng.random() < 0.5:
        for placeholder, known in rng.sample(
            [("<BANKCODE_1>", BSB), ("<SECRET_1>", value), ("<BANKACCT_1>", ACCOUNT)],
            rng.randint(1, 3),
        ):
            seed[placeholder] = known
    return lines, seed, tails


def _reference(
    lines: list[str], seed: dict[str, str], cap: int = 10, batch: bool = True
) -> tuple[list[str], dict[str, str], int]:
    """A fixed point built from the redactor's pieces and nothing of `settle`: find every string, sweep every string, then
    find and sweep EVERY string again until neither the texts nor the map change. Returns (texts, map, the number of the
    last pattern pass that still changed something). It shares `find` and `sweep` with the code under test (what it does
    not share is the loop and its choice of strings); with `batch` the bank context of the batch is set as `redact_many` sets it
    (`redact` of one text has no such context beyond the 100-character window)."""
    r = R._Redactor(dict(seed))
    r.bank_near = batch and any(R._has_bank_word(R.strip_ansi(t)) for t in lines)
    texts = [r.find(t) for t in lines]
    texts = [r.sweep(t) for t in texts]
    last = 1
    for n in range(2, cap + 1):
        before_map = dict(r.mapping)
        nxt = [r.sweep(r.find(t)) for t in texts]
        if nxt == texts and r.mapping == before_map:
            return texts, r.mapping, last
        texts, last = nxt, n
    raise AssertionError("the reference loop did not settle within its own cap")


def free_text(out: str) -> str:
    return "\x00".join(R._PLACEHOLDER.split(out)[0::2])


def raw_leaks(out: str, mapping: dict[str, str], tails: list[str]) -> list[str]:
    """Placeholder names (never values) whose original, by ANY 4-character piece of it, still stands outside a placeholder,
    plus "tail" for a compound tail. Written with no reference to the production sweep or its rules."""
    free, found = free_text(out), []
    for placeholder, original in mapping.items():
        if R.kind_of(placeholder) not in R.SECRET_KINDS:
            continue
        if any(original[i : i + 4] in free for i in range(len(original) - 3)):
            found.append(placeholder)
    found += ["tail"] * sum(1 for tail in tails if tail in free)
    return found


GENERATED = 2000
# The most rounds `settle` ran on any generated composition. The depth distribution is NOT repeated here: it is recorded by the test below
# (`record_property`, junit xml) and recorded, from a real run, in handover/core-c/evidence/G7-1.md ("G7 fix round 4", raw tail). Pinned: a change that makes a
# chain deeper is looked at.
MAX_ROUNDS_SEEN = 3


def test_generated_compositions_match_the_reference_loop_and_leave_no_raw_copy(
    monkeypatch, record_property
):
    rounds = _rounds_spy(monkeypatch)
    rng = random.Random(20261121)  # noqa: S311 - a seeded test generator, not a secret
    needed_third = needed_fourth = refused = most_rounds = 0
    rounds_hist: Counter[int] = Counter()
    last_hist: Counter[int] = Counter()
    for n in range(GENERATED):
        lines, seed, tails = _lines(rng)
        ref_texts, ref_map, last = _reference(lines, seed)
        needed_third += last >= 3
        needed_fourth += last >= 4
        last_hist[last] += 1
        label = f"input {n} (seed 20261121), {len(lines)} lines, {len(seed)} seeded"
        # redact_many: the lines as separate strings, from the seeded map
        rounds["n"] = 0
        try:
            out, mapping = R.redact_many(lines, dict(seed))
        except runmap.RedactionError:
            refused += 1
            raise AssertionError(f"{label}: refused by redact_many") from None
        most_rounds = max(most_rounds, rounds["n"])
        rounds_hist[rounds["n"]] += 1
        assert out == ref_texts, f"{label}: redact_many differs from the reference loop"
        assert set(mapping.values()) == set(ref_map.values()), label
        assert not raw_leaks("\n".join(out), mapping, tails), f"{label}: raw copy (redact_many)"
        # settle ended on a fixed point: another pass and sweep over its output change nothing
        again = R._Redactor(dict(mapping))
        again.bank_near = any(R._has_bank_word(R.strip_ansi(t)) for t in lines)
        assert [again.sweep(again.find(t)) for t in out] == out and again.mapping == mapping, label
        # redact_text: the lines as one text, one run map, and a second call changes nothing
        run = runmap.RunMap()
        run.update(seed)
        try:
            once = runmap.redact_text("\n".join(lines), run)
        except runmap.RedactionError:
            refused += 1
            raise AssertionError(f"{label}: refused by redact_text") from None
        joined_ref, _, _ = _reference(
            ["\n".join(lines)], seed, batch=False
        )  # one string: the labels follow the text order
        assert once == joined_ref[0], f"{label}: redact_text differs from the reference loop"
        assert not raw_leaks(once, dict(run), tails), f"{label}: raw copy (redact_text)"
        held = dict(run)
        assert runmap.redact_text(once, run) == once and dict(run) == held, (
            f"{label}: not a fixed point"
        )
    # The distribution that handover/core-c/evidence/G7-1.md quotes: recorded as test properties (`--junitxml`), never printed by a non-perf test.
    record_property("rounds_run", str(dict(sorted(rounds_hist.items()))))
    record_property("reference_last_changed", str(dict(sorted(last_hist.items()))))
    record_property("third_pass_or_more", str(needed_third))
    record_property("fourth_pass_or_more", str(needed_fourth))
    record_property("refused", str(refused))
    assert refused == 0
    assert needed_third > 0 and needed_fourth > 0  # the generator reaches the depth the cap is for
    assert most_rounds == MAX_ROUNDS_SEEN  # the pinned maximum ...
    assert (
        R._SETTLE_ROUNDS - most_rounds >= 1
    )  # ... with at least one round of headroom under the real cap


def test_the_raw_leak_checker_sees_a_tail_and_a_piece_of_a_secret():
    short = "ab" + "9x"  # made up, built from parts
    mapping = {"<SECRET_1>": short, "<BEARER_1>": short + "qrstu", "<IPV4_1>": "10." + "1.2.3"}
    assert raw_leaks("x <SECRET_1>qrstu y", mapping, ["qrstu"]) == ["<BEARER_1>", "tail"]
    assert raw_leaks("x <BEARER_1> y", mapping, ["qrstu"]) == []
    assert (
        raw_leaks("at " + "10." + "1.2.3", mapping, []) == []
    )  # not a secret kind: not this checker's business
    assert raw_leaks(f"a {short} b", mapping, []) == ["<SECRET_1>", "<BEARER_1>"]


# --- dz-3 / round 3 M5: the size cap with the hostile keyword repeated ------------------------------------------------------


def _hostile_text(keyword: str) -> str:
    """`keyword` repeated up to the size cap (a pattern start every few characters, almost none a value) and, planted at the
    end, the deepest chain found (CHAIN3: a secret, a code glued to it, an account after the code: 3 rounds; a natural chain of
    4 rounds was not found, see the depth test), a compound tail, and a backslash so that `redact_untrusted` scans the views."""
    planted = f"password={V}\nBearer {V}qrstu\nnote {V}qrstuvw\nBSB: {BSB}{V}\npaid {BSB}/{ACCOUNT}\nx\\ty\n"
    body = (keyword + " ") * ((defaults.MAX_REDACT_CHARS - len(planted)) // (len(keyword) + 1))
    text = (body + planted)[: defaults.MAX_REDACT_CHARS]
    assert len(text) <= defaults.MAX_REDACT_CHARS
    return text


@pytest.mark.perf
@pytest.mark.parametrize("keyword", ["password=", "curl -u "])
@pytest.mark.parametrize("budget", [None, 0.5, "scaled"])
def test_T4_a_text_at_the_cap_with_a_deep_chain_is_redacted_or_refused_within_budget_plus_one_unit(
    monkeypatch, keyword, budget
):
    """The claim (defaults.py, "THE BOUND"): the budget is checked between the units of work, so a call that crosses it is refused
    (`InputTooLarge`, nothing shown) after at most the budget plus what the check cannot reach: the pattern pass in progress (pass 1 over the
    whole text, or the pass of a round) and the one `str.replace` or finder pass of a sweep. The unit is measured here on this machine (one `find`
    and one `sweep` of the same text) and the bound ASSERTED is the budget + twice the unit + 0.5 s, looser than the claim, in every case.
    Three budgets. The real one (`None`): the text is REFUSED or REDACTED, whichever this machine's speed gives (the `curl -u ` shape
    costs 4.5 to 5.3 s of the 6 s budget on the test machine, so a runner 14 to 25 percent slower refuses it, defaults.py: that is the
    designed fail-closed outcome, not a failure; a redacted text must hold no V, code or account). 0.5 s: it must be REFUSED (the refusal path
    is what is measured). `scaled`: the budget is 1.5 times what an unbudgeted run of this text just took on this machine, so the text must be
    REDACTED, on any machine. `thread_time` is CPU time of the calling thread: a caller needs its own wall-clock guard."""
    mode = budget
    text = _hostile_text(keyword)
    probe = R._Redactor(None)
    start = time.thread_time()
    found = probe.find(text)
    probe.sweep(found)
    unit = time.thread_time() - start  # one pattern pass and one sweep over the whole text
    if mode == "scaled":
        monkeypatch.setattr(defaults, "REDACT_BUDGET_S", 1e6)
        start = time.thread_time()
        runmap.redact_untrusted(text, runmap.RunMap())
        budget = 1.5 * (time.thread_time() - start)
    if budget is not None:
        monkeypatch.setattr(defaults, "REDACT_BUDGET_S", budget)
    allowed = defaults.REDACT_BUDGET_S
    start = time.thread_time()
    try:
        out = runmap.redact_untrusted(text, runmap.RunMap())
        refused = False
    except runmap.InputTooLarge:
        refused = True
    took = time.thread_time() - start
    print(
        f"\nG7 hostile {keyword!r} at the cap, budget {allowed:.2f} s: {took:.2f} s, "
        f"{'REFUSED (InputTooLarge)' if refused else 'redacted'}; one pass + sweep {unit:.2f} s"
    )
    if mode == 0.5:
        assert refused, "a budget of 0.5 s must refuse (the refusal path is what is measured)"
    if mode == "scaled":
        assert not refused, "a budget of 1.5 times the measured run must cover the same text"
    if not refused:
        assert V not in out and ACCOUNT not in out and BSB not in out
    assert took <= allowed + 2 * unit + 0.5


# --- G7 fix round 6 (G7 result review 5): M-A (P x S), M-B/M-C (overlaps), M-D (bank_near in `redact`), M-E (growth trigger) ----------------


def _jar_log(lines: int, suffix_chars: int) -> tuple[str, str]:
    """(registered text, probe of copies). A growing cookie jar: the Cookie header of line k holds k cookies of 4 characters, the NEWEST FIRST,
    so the prefix of line k ends with the prefix of line k-1 (one more registered prefix matches on every line), and every line ends with the
    same signed suffix of `suffix_chars` characters after the session token. The probe is the lines as the first sweep leaves other copies."""
    sig = ("sig" + "AbCdEfGh") * (suffix_chars // 11 + 1)
    rows = [
        "Cookie: "
        + ";".join(f"a{(k - j) % 10}=1" for j in range(k))
        + f"; sid={JWT}~{sig[:suffix_chars]}"
        for k in range(1, lines + 1)
    ]
    text = "\n".join(rows)
    return text, text.replace(JWT, "<JWT_1>")


def test_a_growing_cookie_jar_with_a_long_signed_suffix_is_masked_not_refused(monkeypatch):
    """Round 5 design M-A: the suffix walk ran once per matched prefix form (P x S). 275 lines (a registered log of about 236,000 characters, inside the
    size cap) of a jar that grows by one cookie per line, every line ending in the same signed suffix of 128 characters, then copies up to the cap.
    Units of work (evidence g7r6_units.py, G7-1.md): round 5's scan 3,606,794 for a 219,999-character probe (90 percent of the real limit; about 4.3
    million, over it, for the stretched 262,144-character probe used here: TYPED, scaled), refused as SpelledWorkTooMuch (an honest log lost); now
    254,629 and 301,360 (a walk of the prefix and ONE walk of the suffix per token). The limit is cut to a tenth (400,000) in this test: the new scan
    passes with a margin of 1.3, the round 5 scan fails by a factor of 10. The copies are scanned to the end and replaced."""
    text, probe = _jar_log(275, 128)
    assert len(text) <= defaults.MAX_REDACT_CHARS
    probe = (probe + "\n" + probe)[: defaults.MAX_REDACT_CHARS]
    monkeypatch.setattr(defaults, "SPELLED_MAX_WORK", defaults.SPELLED_MAX_WORK // 10)
    r = R._Redactor(None)
    r.find(text)
    assert len(r._spelled_at) == 275
    r.sweep("")
    swept = r._spelled_sweep(probe, None)  # does not raise
    assert "<JWT_1>" not in swept[: len(swept) - 1000], "the copies were really walked and replaced"
    assert swept.count("Cookie: <SECRET_") >= 300


def test_the_jar_log_goes_through_a_whole_call_masked(monkeypatch):
    """The same shape through `redact_many` (the registered log in one string, the copies in the next, one namespace)."""
    text, probe = _jar_log(120, 128)
    out, _ = R.redact_many([text, probe.replace("Cookie: ", "echo ")])
    assert JWT not in "\n".join(out) and "sigAbCdEfGh" not in "\n".join(out)
    assert "a1=1" not in "\n".join(out)


def test_the_work_of_a_token_is_matched_prefix_plus_suffix_not_their_product():
    """The units of one scan, counted by cutting `SPELLED_MAX_WORK` (the scan refuses past it, read every 1,024 units): the jar's work grows with
    P + S per token. 200 lines of 64 and of 256 suffix characters differ by about the suffix walked once per token (not once per matched prefix:
    that is 4 times the lines' work again)."""
    work = {}
    for suffix in (64, 256):
        text, probe = _jar_log(200, suffix)
        r = R._Redactor(None)
        r.find(text)
        r.sweep("")
        lo, hi = 0, 10**8
        while hi - lo > 2048:
            mid = (lo + hi) // 2
            defaults_limit = mid
            old = defaults.SPELLED_MAX_WORK
            defaults.SPELLED_MAX_WORK = defaults_limit
            try:
                r._spelled_sweep(probe, None)
                hi = mid
            except runmap.InputTooLarge:
                lo = mid
            finally:
                defaults.SPELLED_MAX_WORK = old
        work[suffix] = hi
    # P x S would make the 256-character suffix cost 4 times the 64-character one; P + S makes it cost 1.3 to 2 times
    assert work[256] < 2.5 * work[64], work


def _registered_forms(r) -> int:
    return len(r._spelled_at)


def test_registrations_and_rollbacks_leave_no_node_behind():
    """Round 6: the registry is two tries; a rolled-back form deletes its path in both, the prefix id and the token entry, whatever the order. The
    dead branches of `_spell` and `_unspell` (a form with no token, a path that is not there) were removed: a registration is made whole, so a
    rollback of every registration leaves `_spelled` and `_spelled_at` empty."""
    rng = random.Random(606)  # noqa: S311 - a seeded test generator
    r = R._Redactor({"<SECRET_1>": SHORT, "<SECRET_2>": "zz" + "q7"})
    counters = r._open_journal()
    made = []
    for _ in range(60):
        token = rng.choice(["<SECRET_1>", "<SECRET_2>"])
        pre, suf = (
            "".join(rng.choice("abc") for _ in range(rng.randint(0, 4))),
            "".join(rng.choice("xyz") for _ in range(rng.randint(0, 4))),
        )
        original = f"{pre}{token}{suf}"
        full = original.replace("<SECRET_1>", SHORT).replace("<SECRET_2>", "zzq7")
        if len(full) >= 5 and original != full:
            made.append(r._place("BEARER", full, original))
    assert _registered_forms(r) > 20 and r._spelled
    r._rollback(counters)
    assert r._spelled == {} and r._spelled_at == {}, (r._spelled, r._spelled_at)


def test_the_same_written_form_registered_twice_is_one_form_owned_by_the_second_placeholder():
    """The same (prefix, suffix) under one token registered again (only a reissue of numbers after a rollback can do it, with a different value:
    contrived here) keeps ONE form, the later placeholder's; the earlier one has no form of its own any more, and a rollback of the later one
    removes the form and every node (the earlier placeholder's copies are then not swept to it: the same as round 5, harmless because the
    earlier registration is the one a reissue replaced)."""
    r = R._Redactor({"<SECRET_1>": SHORT})
    first = r._place("BEARER", SHORT + "qrstu", "<SECRET_1>qrstu")
    counters = r._open_journal()
    second = r._place("BEARER", SHORT + "qrstu!", "<SECRET_1>qrstu")
    assert second != first and list(r._spelled_at) == [second]
    assert r._spelled_sweep("x <SECRET_1>qrstu y", None) == f"x {second} y"
    r._rollback(counters)
    assert r._spelled == {} and r._spelled_at == {}
    assert r._spelled_sweep("x <SECRET_1>qrstu y", None) == "x <SECRET_1>qrstu y"


def test_an_entry_whose_placeholder_no_longer_maps_to_its_value_is_ignored_when_read():
    """Defence in depth kept on purpose (round 6 nit: the comment called it a safety net): a form whose placeholder was dropped from the map is
    not applied. Reached here by editing the map directly."""
    r = R._Redactor({"<SECRET_1>": SHORT})
    placeholder = r._place("BEARER", SHORT + "qrstu", "<SECRET_1>qrstu")
    assert r._spelled_sweep("x <SECRET_1>qrstu y", None) == f"x {placeholder} y"
    del r.mapping[placeholder]
    assert r._spelled_sweep("x <SECRET_1>qrstu y", None) == "x <SECRET_1>qrstu y"


def test_a_registration_always_has_a_token_when_the_value_differs_from_its_text():
    """The unreachable `first is None` branch of `_spell` is gone: `_place` registers only when the written form differs from the restored value
    and holds a placeholder (`_PLACEHOLDER.sub` changed it, so a match exists). Checked over generated written forms: whenever the restore changes
    a text, a token is found in it; a text with no token is never registered."""
    rng = random.Random(607)  # noqa: S311 - a seeded test generator
    mapping = {"<SECRET_1>": SHORT}
    for _ in range(500):
        parts = [
            rng.choice(["abc", "<SECRET_1>", "<SECRET_9>", "<", ">", "x"])
            for _ in range(rng.randint(1, 5))
        ]
        original = "".join(parts)
        full = R._PLACEHOLDER.sub(lambda p: mapping.get(p.group(1), p.group(1)), original)
        if full != original:
            assert R._PLACEHOLDER.search(original) is not None
        r = R._Redactor(mapping)
        r._place("BEARER", full, original)
        assert bool(r._spelled_at) == (full != original and len(full) >= 4)


# --- M-B (a), closed by G9 (tests in the G9 block): two compound values that overlap as RAW text -------------------------------------------------------------------------------


# --- M-D: `bank_near` flipping inside `find` of ONE string ------------------------------------------------------------------------------


def _fullwidth(word: str) -> str:
    return "".join(chr(ord(c) + 0xFEE0) for c in word)


def _hidden_bank_word_texts():
    hidden = "rou\u200bting number"
    for acct in ("account", _fullwidth("account"), "acc\u200bount", "acco\u0301unt"):
        for first_is_account in (True, False):
            lines = [f"{acct}: {ACCOUNT}", f"filler {hidden}"]
            yield "\n".join(lines if first_is_account else lines[::-1]) + "\n"


def test_an_account_beside_a_bank_word_only_a_folded_view_shows_is_masked_in_every_order():
    """Round 5 design M-D, NOT REPRODUCED: the account keyword visible only in one view and the bank word visible only in another (line order both
    ways, four spellings of the keyword). Reason: the dry hits of `_fold_scan` do not depend on `bank_near`, and the fold scan sets the flag before any
    line is masked and before the direct patterns of the same `find` run. The cases are pinned; the second read of `redact` (next test) is the
    safety net."""
    for text in _hidden_bank_word_texts():
        assert ACCOUNT not in R.redact(text).text, text
        assert ACCOUNT not in R.redact_many([text])[0][0], text
        assert ACCOUNT not in runmap.redact_text(text, runmap.RunMap()), text


def test_redact_reads_the_text_once_even_when_the_flag_flips_during_the_read(monkeypatch):
    """Round 7 (design nit): round 6 read the text a second time after a flip of `bank_near` (a safety net that also counted `actions` twice).
    The flag is set before any decision of the same `find` (next test), so the one read already had the context: ONE read, flip or not."""
    reads = []
    real = R._Redactor.find

    def counting(self, text):
        reads.append(text)
        return real(self, text)

    monkeypatch.setattr(R._Redactor, "find", counting)
    flips = f"{_fullwidth('account')}: {ACCOUNT}\nrou\u200bting number\n"
    result = R.redact(flips, _sweep_copies=False)
    assert reads == [flips] and ACCOUNT not in result.text
    reads.clear()
    R.redact("account: 12\n", _sweep_copies=False)
    assert len(reads) == 1
    reads.clear()
    R.redact(flips, near=("the bank account is ours",), _sweep_copies=False)
    assert len(reads) == 1


def test_actions_of_a_text_whose_flag_flipped_are_counted_once():
    """Round 7 design nit: `RedactionResult.actions` ("how many times the redactor changed the text of this call") was about twice the real count
    after a flip (the second read re-masked from the raw text and `r.actions` was not reset). The same text with the context given up front
    (`near=`: no flip, one read) is the reference."""
    for flips in (
        f"{_fullwidth('account')}: {ACCOUNT}\nrou\u200bting number\n",
        f"{_fullwidth('account')}: {ACCOUNT}\nrou\u200bting number\n{_fullwidth('account')}: {ACCOUNT}2\n",
    ):
        flipped = R.redact(flips, _sweep_copies=False)
        given = R.redact(flips, near=("the bank account is ours",), _sweep_copies=False)
        assert flipped.text == given.text
        assert flipped.actions == given.actions > 0, (flipped.actions, given.actions)
    full = R.redact(flips)  # with the sweep and settle
    assert full.actions == R.redact(flips, near=("the bank account is ours",)).actions


def _flag_grid_texts() -> list[str]:
    texts = list(_hidden_bank_word_texts()) + _flip_items()
    for keyword in ("account", "acct", "BSB", "routing"):
        for bank in ("bank", "routing number", "\uff22\uff33\uff22"):
            for order in (0, 1):
                a, b = f"{_fullwidth(keyword)}: {ACCOUNT}", f"filler {bank[:4]}\u200b{bank[4:]}"
                texts.append("\n".join((a, b) if order == 0 else (b, a)) + "\n")
    return texts


def test_every_decision_of_a_find_sees_the_flag_as_it_is_when_that_find_ends(monkeypatch):
    """Round 7: the proof that makes the second read of round 6 redundant. `bank_near` is read by `_decide` alone; the fold scan sets it before
    anything is decided (its `_line_hits` and `_dry_hits` never decide), so in ONE `find` every `_decide` call sees the flag as it is when
    the `find` ends. Checked on a grid of keyword spellings x bank-word spellings x order (and the hidden-bank-word texts): at least 10 texts
    flip the flag inside their `find`, with decisions made in it, and none was made before the flip. A change that decides before the fold scan has set the flag
    (g7r7_mutants.py defers the write) fails here."""
    seen: list[tuple[bool, int]] = []
    state = {"calls": []}
    real_decide, real_find = R._Redactor._decide, R._Redactor.find

    def decide(self, m, label):
        state["calls"].append(self.bank_near)
        return real_decide(self, m, label)

    def find(self, text):
        state["calls"] = []
        out = real_find(self, text)
        seen.append((self.bank_near, len(state["calls"])))
        assert all(flag == self.bank_near for flag in state["calls"]), (text, state["calls"])
        return out

    monkeypatch.setattr(R._Redactor, "_decide", decide)
    monkeypatch.setattr(R._Redactor, "find", find)
    flipped = decided = 0
    for text in _flag_grid_texts():
        r = R._Redactor(None)
        r.find(text)
        flipped += r.bank_near
        decided += (
            seen[-1][1] if r.bank_near else 0
        )  # decisions made in a find that flipped the flag
    assert flipped >= 10 and decided >= 10, (flipped, decided)


# --- M-E: an entry the FIRST sweep registered counts as growth for the first round ----------------------------------------------------------


def test_a_union_registered_in_the_first_sweep_makes_the_first_round_sweep_every_string(
    monkeypatch,
):
    """Round 5 design M-E. The map holds `<SECRET_1>` (a seeded run map); `Bearer <SECRET_1>ab` and `Bearer xyz<SECRET_1>` register F1 and F2 in
    pass 1, and the LAST string `see xyz<SECRET_1>ab` registers the union during the FIRST sweep (strings 0 to 2 were swept before it
    existed). `settle` read the map size at the start of round 1, after the first sweep: the growth was invisible and round 1 swept only the
    strings its own pass changed (here none). Read before the first sweep, the entry counts as growth: every string is swept again."""
    calls: list[str] = []
    real = R._Redactor.sweep

    def spy(self, out, deadline=None):
        calls.append(out)
        return real(self, out, deadline)

    monkeypatch.setattr(R._Redactor, "sweep", spy)
    items = [
        "a plain line",
        "Bearer <SECRET_1>ab",
        "Bearer xyz<SECRET_1>",
        "see xyz<SECRET_1>ab end",
    ]
    out, mapping = R.redact_many(items, mapping={"<SECRET_1>": SHORT})
    union = [p for p, v in mapping.items() if v == "xyz" + SHORT + "ab"]
    assert len(union) == 1 and out[3] == f"see {union[0]} end", out
    first_sweep, later = calls[:4], calls[4:]
    assert first_sweep[0] == "a plain line"
    assert "a plain line" in later, (
        "round 1 swept string 0 again (the map grew during the first sweep)"
    )
    assert len(later) >= 4


def test_union_registration_is_counted_and_checked(monkeypatch):
    """Round 5 design M-E: `_place_union` (the text restore, the registration) was outside the deadline and the work counter: a union of 5,000 characters
    is 5,000 units (and a deadline check). The text is walked once for the forms (about 5,000 units) and once to register the union."""
    tail = "q" * 5000
    text = f"see xyz<SECRET_1>{tail} end"

    def fresh():  # a union is registered by the first sweep that meets the overlap: each call needs its own redactor
        r = R._Redactor({"<SECRET_1>": SHORT})
        r._place("BEARER", SHORT + tail, "<SECRET_1>" + tail)
        r._place("BEARER", "xyz" + SHORT, "xyz<SECRET_1>")
        return r

    monkeypatch.setattr(defaults, "SPELLED_MAX_WORK", 20_000)
    assert (
        fresh()._spelled_sweep(text, None).startswith("see <BEARER_")
    )  # the walk (about 5,000 units) and the union (5,000) fit
    monkeypatch.setattr(
        defaults, "SPELLED_MAX_WORK", 7_000
    )  # the walk alone fits, the walk and the union do not
    with pytest.raises(runmap.InputTooLarge, match="SpelledWorkTooMuch"):
        fresh()._spelled_sweep(text, None)
    monkeypatch.undo()
    with pytest.raises(runmap.InputTooLarge):
        fresh()._spelled_sweep(text, time.thread_time() - 1.0)
    assert fresh()._spelled_sweep(text, time.thread_time() + 600.0).startswith("see <BEARER_")


# --- G7 fix round 7 (G7 result review 6): registry memory limit, per-round growth record, smaller-side lookup, both-ends grid ----------------


def _hostile_memory_items(strings: int = 8) -> list[str]:
    """Line 1 gives `<SECRET_1>` a value; every other string is `password=<SECRET_1>` + 260,000 secret-class characters (a forged token the map
    already holds makes the written form differ from the value, so each string registers a form of its own: the strings differ in 3 characters)."""
    value = "hun" + "ter" + "22"
    tail = ("Ab3x" * 65_000)[:260_000]
    return ["password=" + value] + [f"password=<SECRET_1>Zq{i}" + tail for i in range(strings)]


def test_a_text_that_registers_about_a_million_characters_of_forms_is_refused_in_bounded_time_and_memory():
    """Round 7 design MAJOR (memory DoS). Before: the 8 strings registered 8 x 260,000 characters (about 185 bytes each): the call peaked at 2.3 GB
    under tracemalloc (79 s), nothing refused it. Now the registry counts the characters it holds per call and refuses the call past
    `defaults.SPELLED_MAX_CHARS` (1,000,000) at the REGISTRATION (never skipped): about 4 strings in, peak about 190 MB (3.6 s)."""
    items = _hostile_memory_items()
    held = {"<SECRET_1>": "hun" + "ter" + "22"}
    before = dict(held)
    tracemalloc.start()
    t0 = time.thread_time()
    try:
        with pytest.raises(runmap.InputTooLarge, match="SpelledMemoryTooMuch"):
            R.redact_many(items, held)
        took = time.thread_time() - t0
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    assert peak < 400_000_000, (
        f"peak {peak / 1e6:.0f} MB: the registry was not bounded"
    )  # 1.3 M nodes x 185 B is 240 MB; 2.3 GB before
    assert took < 40.0, took  # 3.6 s measured under tracemalloc; 79 s before
    assert held == before, "the caller's map is the caller's: a refused call changed nothing in it"


def test_one_string_of_the_hostile_shape_registers_once_and_is_masked_not_refused():
    """The single-string `redact` of the same shape registers ONE form of 260,000 characters (49 MB, under the limit): masked, not refused. The
    limit bounds the sum over the call's strings, not one string (that one is bounded by the input cap)."""
    value = "hun" + "ter" + "22"
    text = _hostile_memory_items(1)[1]
    result = R.redact(text, mapping={"<SECRET_1>": value})
    assert "Ab3xAb3x" not in result.text and result.text.startswith("password=<SECRET_")


def test_the_registry_counter_is_per_call_and_a_refusal_leaves_the_next_call_alone(monkeypatch):
    """One call may hold up to the limit; the counter starts at 0 in every call (a counter shared between calls would refuse the second)."""
    value = "hun" + "ter" + "22"
    items = [
        "password=" + value,
        "password=<SECRET_1>" + "q" * 1500,
        "password=<SECRET_1>" + "r" * 1500,
    ]
    monkeypatch.setattr(defaults, "SPELLED_MAX_CHARS", 4000)
    for _ in range(3):  # 3,000 characters of forms per call, under 4,000; three calls: 9,000 in all
        out, _ = R.redact_many(items)
        assert "q" * 100 not in "".join(out) and "r" * 100 not in "".join(out)
    monkeypatch.setattr(defaults, "SPELLED_MAX_CHARS", 2000)
    with pytest.raises(runmap.InputTooLarge, match="SpelledMemoryTooMuch"):
        R.redact_many(items)
    monkeypatch.setattr(defaults, "SPELLED_MAX_CHARS", 4000)
    assert "q" * 100 not in "".join(R.redact_many(items)[0])  # the refusal kept nothing
    assert R._Redactor(None)._spelled_chars == 0


def test_the_memory_limit_also_stops_the_union_of_an_overlap(monkeypatch):
    """The union registered by a sweep (`_place_union` -> `_place` -> `_spell`) is charged like any registration: F1 = `<SECRET_1>ab<SECRET_2>`,
    F2 = `b<SECRET_2>` + a 3,000-character tail overlap in the text, and their union adds the 3,000-character tail under a third trie path."""
    tail = "q" * 3000

    def fresh():
        r = R._Redactor({"<SECRET_1>": SHORT, "<SECRET_2>": "zz" + "q7"})
        r._place("BEARER", SHORT + "abzzq7", "<SECRET_1>ab<SECRET_2>")
        r._place("BEARER", "bzzq7" + tail, "b<SECRET_2>" + tail)
        return r

    text = "see <SECRET_1>ab<SECRET_2>" + tail + " end"
    monkeypatch.setattr(defaults, "SPELLED_MAX_CHARS", 7000)
    ok = fresh()
    assert ok._spelled_sweep(text, None).startswith("see <BEARER_")
    assert 3000 < ok._spelled_chars <= 7000
    registered = fresh()._spelled_chars
    assert 3000 < registered < 3100
    monkeypatch.setattr(
        defaults, "SPELLED_MAX_CHARS", registered + 100
    )  # the forms fit, the union's 3,000 more characters do not
    victim = fresh()
    with pytest.raises(runmap.InputTooLarge, match="SpelledMemoryTooMuch"):
        victim._spelled_sweep(text, None)


def test_the_counter_is_the_number_of_trie_nodes_after_registrations_and_rollbacks():
    """`_spelled_chars` is what the tries really hold: counted by walking both tries after 60 random registrations, then after the rollback of
    all of them (0). A registration over a path that exists adds only the missing nodes."""
    rng = random.Random(707)  # noqa: S311 - a seeded test generator

    def nodes(r) -> int:
        count, stack = 0, [t for pair in r._spelled.values() for t in pair]
        while stack:
            node = stack.pop()
            for key, child in node.items():
                if key and isinstance(child, dict):
                    count += 1
                    stack.append(child)
        return count

    r = R._Redactor({"<SECRET_1>": SHORT, "<SECRET_2>": "zz" + "q7"})
    counters = r._open_journal()
    for _ in range(60):
        token = rng.choice(["<SECRET_1>", "<SECRET_2>"])
        pre = "".join(rng.choice("abc") for _ in range(rng.randint(0, 6)))
        suf = "".join(rng.choice("xyz") for _ in range(rng.randint(0, 6)))
        original = f"{pre}{token}{suf}"
        full = original.replace("<SECRET_1>", SHORT).replace("<SECRET_2>", "zzq7")
        if len(full) >= 5 and original != full:
            r._place("BEARER", full, original)
            assert r._spelled_chars == nodes(r), original
    assert r._spelled_chars > 20
    r._rollback(counters)
    assert nodes(r) == 0 and r._spelled_chars == 0


def test_honest_shapes_hold_a_tiny_part_of_the_memory_limit():
    """Measured (evidence g7r7_registry.py): the grown jars hold 1,469 and 1,720 characters (shared nodes), 300 cookie lines 3,017; the limit is
    1,000,000. The jar is masked, not refused, with the REAL limit, in one `redact_many` call."""
    text, probe = _jar_log(275, 128)
    r = R._Redactor(None)
    r.find(text)
    assert 1000 < r._spelled_chars < defaults.SPELLED_MAX_CHARS // 100, r._spelled_chars
    out, _ = R.redact_many([text, probe[:2000]])
    assert JWT not in "".join(out)
    rows = [f"Cookie: _ga=GA1.2{'x' * k}; theme=dark; sid={JWT}" for k in range(300)]
    cookies = R._Redactor(None)
    cookies.find("\n".join(rows))
    assert cookies._spelled_chars < defaults.SPELLED_MAX_CHARS // 100, cookies._spelled_chars


# --- round 7 design nit: the growth record is made before the sweeps of EVERY round -------------------------------------------------------


def test_a_union_registered_by_a_sweep_of_a_later_round_puts_every_string_back(monkeypatch):
    """Round 6 read the map size before the sweeps of the first round only. A union a sweep registers in round 2 or later (a stand-in: the sweep of
    one string adds a map entry) is growth too: every string is read again and, in the next round, swept again (round 7: `known` is recorded before the
    sweep loop of every round). The strings: `s1` is never changed by anything, so only a sweep of every string reaches it."""
    r = R._Redactor(None)
    swept: list[tuple[int, str]] = []
    round_of = {"n": 0}

    def find(self, text):
        round_of["n"] += 1 if text in ("s0", "u0") else 0
        return {"s0": "t0", "u0": "v0"}.get(text, text)

    def sweep(self, text, deadline=None):
        swept.append((round_of["n"], text))
        if text == "v0":
            self.mapping["<SECRET_9>"] = "grown-by-a-sweep"
            return "w0"
        return {"t0": "u0"}.get(text, text)

    monkeypatch.setattr(R._Redactor, "find", find)
    monkeypatch.setattr(R._Redactor, "sweep", sweep)
    assert r.settle(["o0", "o1"], ["s0", "s1"]) == ["w0", "s1"]
    assert (2, "v0") in swept, swept
    assert [t for n, t in swept if n >= 2 and t == "s1"], (
        "the untouched string was swept again after the growth in round 2"
    )


def test_growth_by_a_sweep_in_the_last_round_is_not_settled(monkeypatch):
    """`NotSettled` stays the cap: a sweep that registers an entry in round 4 leaves every string in `todo`, and no round reads them again."""
    r = R._Redactor(None)
    calls = {"find": 0}

    def find(self, text):
        calls["find"] += 1
        return text + "x"  # changes every round: round 4 changes too

    def sweep(self, text, deadline=None):
        self.mapping[f"<SECRET_{len(self.mapping) + 1}>"] = "v" * (len(self.mapping) + 8)
        return text

    monkeypatch.setattr(R._Redactor, "find", find)
    monkeypatch.setattr(R._Redactor, "sweep", sweep)
    with pytest.raises(runmap.RedactionError, match="NotSettled"):
        r.settle(["o"], ["s"])


# --- round 7 codebase nit 6: the smaller side of the terminal lookup is iterated; both-ends grid ----------------------------------------


def _units_of_sweep(r, probe: str) -> int:
    lo, hi, held = 0, 10**9, defaults.SPELLED_MAX_WORK
    try:
        while hi - lo > 1024:
            mid = (lo + hi) // 2
            defaults.SPELLED_MAX_WORK = mid
            try:
                r._spelled_sweep(probe, None)
                hi = mid
            except runmap.InputTooLarge:
                lo = mid
    finally:
        defaults.SPELLED_MAX_WORK = held
    return hi


def test_many_matched_prefixes_and_a_one_entry_terminal_cost_the_one_entry_not_the_prefixes():
    """Round 6 codebase nit 6: `_spelled_sweep` looks the SMALLER side up in the larger at a terminal. 275 forms `a`*k + token + `Z`*k (275 nested
    prefixes, each with ITS OWN suffix): a token preceded by 275 `a` matches all 275 prefixes (M = 275) and every terminal of its suffix path holds ONE
    entry (T = 1). Iterating `matched` at every terminal would cost 275 units at each of 275 terminals (75,000 per token); the smaller side costs 1
    (about 830 per token: 275 + 275 + 275). 400 such tokens: about 330,000 units, and about 30 million with the mutant (`always iterate matched`,
    g7r7_mutants.py)."""
    forms = "\n".join(f"password={'a' * k}<SECRET_1>{'Z' * k}" for k in range(1, 276))
    r = R._Redactor({"<SECRET_1>": SHORT})
    r.find(forms)
    r.sweep("")
    assert len(r._spelled_at) == 275
    probe = ("a" * 275 + "<SECRET_1>" + "Z" * 275 + "\n") * 400
    units = _units_of_sweep(r, probe)
    assert units < 450_000, units  # 400 tokens x about 830
    assert units > 250_000, (
        units
    )  # the walks really ran (a vacuous pass would be a scan that matched nothing)
    r._spelled_sweep(probe, None)


def test_a_grid_that_grows_at_both_ends_costs_the_product_of_its_sides_per_token_and_is_refused_past_the_limit():
    """Round 6 design nit: an honest-looking shape that is not one of the four measured ones. Forms `a`*i + token + `Z`*j for every i <= F and
    j <= B (every combination a distinct value): each combination is a real match, so a token costs about F x B units. Measured (evidence
    g7r6_units.py): 20 x 20 takes 2.28 million units (8.7 per character of the text), 30 x 30 3.56 million; the limit refuses about 32 x 32. Pinned
    at 20 x 20 (fits, 400 forms) and 40 x 40 (refused)."""

    def grid(front: int, back: int) -> tuple[str, str]:
        forms = "\n".join(
            f"password={'a' * i}<SECRET_1>{'Z' * j}"
            for i in range(1, front + 1)
            for j in range(1, back + 1)
        )
        block = "a" * front + "<SECRET_1>" + "Z" * back + "\n"
        return forms, block * (defaults.MAX_REDACT_CHARS // len(block))

    forms, probe = grid(20, 20)
    r = R._Redactor({"<SECRET_1>": SHORT})
    r.find(forms)
    r.sweep("")
    assert len(r._spelled_at) == 400
    units = _units_of_sweep(r, probe)
    assert 1_500_000 < units < 3_500_000 and units / len(probe) > 5, units
    forms, probe = grid(40, 40)
    big = R._Redactor({"<SECRET_1>": SHORT})
    big.find(forms)
    big.sweep("")
    with pytest.raises(runmap.InputTooLarge, match="SpelledWorkTooMuch"):
        big._spelled_sweep(probe, None)


# --- G9 (ORDER 023, E10): the sweep to a fixed point over the text read back --------------------------------------------------------

_TOKEN = re.compile(r"<[A-Z][A-Z0-9]*_\d+>")
_A, _B = "abcd" + "efgh", "efgh" + "ijkl"  # two SECRET values that overlap by `efgh`


def _registering(mapping: dict[str, str] | None) -> R._Redactor:
    """A redactor that may register a union, as `redact` and `redact_many` make it."""
    r = R._Redactor(mapping)
    r._may_register = True
    return r


def _passes_per_sweep(monkeypatch) -> list[int]:
    """Wraps `_Redactor.sweep` and `_Redactor._overlaps` (class level: every redactor a call makes): the passes (read-backs) of each
    sweep call, in call order. A pass that found nothing but grew the map is followed by another; this counts both."""
    passes: list[int] = []
    real_sweep, real_overlaps = R._Redactor.sweep, R._Redactor._overlaps

    def sweep(self, out, deadline=None):
        passes.append(0)
        return real_sweep(self, out, deadline)

    def overlaps(self, out, deadline, work):
        passes[-1] += 1
        return real_overlaps(self, out, deadline, work)

    monkeypatch.setattr(R._Redactor, "sweep", sweep)
    monkeypatch.setattr(R._Redactor, "_overlaps", overlaps)
    return passes


def test_g9_an_overlap_completed_only_in_a_later_round_is_masked_whole():
    """E10 (b), REPLACES the round 3 pin: round 2 sweeps `xyz<SECRET_1>ab` to `xyz<F1>`; round 3 registers F2 `xyz<SECRET_1>`. The read-back of
    `xyz<F1>` is `xyz` + V + `ab`: F2's value covers `xyz` and part of F1, so the run is registered whole and replaced; nothing of it stays
    readable. Its number is not pinned (it depends on the order of registration); its value is, and its kind is SECRET (a union that holds a
    secret takes the SECRET kind, whatever kinds it holds: here BEARER)."""
    r = _registering({"<SECRET_1>": SHORT})
    f1 = r._place("BEARER", SHORT + "ab", "<SECRET_1>ab")
    round2 = r.sweep("xyz<SECRET_1>ab")
    assert round2 == f"xyz{f1}"
    f2 = r._place("BEARER", "xyz" + SHORT, "xyz<SECRET_1>")
    round3 = r.sweep(round2)
    assert _TOKEN.fullmatch(round3) and round3 not in (f1, f2), round3
    assert r.mapping[round3] == "xyz" + SHORT + "ab" and R._kind(round3) == "SECRET"
    assert r.sweep(round3) == round3


def test_g9_two_overlapping_values_in_raw_text_are_masked_whole():
    """E10 (a), REPLACES the raw pin: `abcdefgh` and `efghijkl` in `abcdefghijkl` (the literal sweep cut the second), and F1 = V+`ab`,
    F2 = `xyz`+V in a raw `xyz`+V+`ab`. Each run is one new value; the map gains exactly that entry."""
    plain = _registering({"<SECRET_1>": _A, "<SECRET_2>": _B})
    assert plain.sweep(_A + "ijkl") == "<SECRET_3>", "E10a: the raw overlap is not one entry"
    assert plain.mapping == {"<SECRET_1>": _A, "<SECRET_2>": _B, "<SECRET_3>": _A + "ijkl"}
    r = _registering({"<SECRET_1>": SHORT})
    f1 = r._place("BEARER", SHORT + "ab", "<SECRET_1>ab")
    f2 = r._place("BEARER", "xyz" + SHORT, "xyz<SECRET_1>")
    out = r.sweep("see xyz" + SHORT + "ab end")
    union = out.removeprefix("see ").removesuffix(" end")
    assert _TOKEN.fullmatch(union) and union not in (f1, f2), out
    assert r.mapping[union] == "xyz" + SHORT + "ab"


def test_g9_the_raw_overlap_through_redact_redact_many_and_redact_text():
    """The natural input (no seeded map): two secrets found by their keys, then a raw `abcdefghijkl`. Before G9: `see <SECRET_1>ijkl`."""
    lines = ["password=" + _A, "token=" + _B, "see " + _A + "ijkl"]
    text = "\n".join(lines)
    expected = ["password=<SECRET_1>", "token=<SECRET_2>", "see <SECRET_3>"]
    result = R.redact(text)
    assert result.text == "\n".join(expected)
    assert result.mapping == {"<SECRET_1>": _A, "<SECRET_2>": _B, "<SECRET_3>": _A + "ijkl"}
    assert result.restore(result.text) == text
    many, mapping = R.redact_many(lines)
    assert many == expected and mapping["<SECRET_3>"] == _A + "ijkl"
    assert runmap.redact_text(text, runmap.RunMap()) == "\n".join(expected)


def test_g9_every_key_of_the_map_is_read_back_whoever_wrote_it_and_nothing_else():
    """The read-back puts back a token that is an exact KEY of the map, whoever wrote it (this redactor, an earlier call, the fold scan
    reusing a placeholder): `<SECRET_1>` came in with the text. A token that is not a key (`<SECRET_9>`) is a separator: nothing is read
    across it (mutant G9-7)."""
    r = _registering({"<SECRET_1>": _A, "<SECRET_2>": _B})
    assert r.sweep("x <SECRET_1>ijkl y") == "x <SECRET_3> y", (
        "a key given with the text was not read back"
    )
    assert r.mapping["<SECRET_3>"] == _A + "ijkl"
    other = _registering({"<SECRET_1>": _A, "<SECRET_2>": _B})
    assert other.sweep("x <SECRET_9>ijkl y") == "x <SECRET_9>ijkl y"
    assert other.sweep("x efgh<SECRET_9>ijkl y") == "x efgh<SECRET_9>ijkl y"
    assert len(other.mapping) == 2
    # a value that holds a NUL (the separator's character): its NUL-free alias key is swept by the body, as at the base; no union
    nul = _registering({"<SECRET_1>": "\0" + "wxyz"})
    assert nul.sweep("a<SECRET_9>wxyz") == "a<SECRET_9><SECRET_1>" and len(nul.mapping) == 1


def test_g9_a_short_run_of_tokens_is_read_back_whole():
    """A run whose kept head and tail together reach its length is read back WHOLE (no separator in the middle): the value `abcdefgh`
    spans `ab`, the whole `<SECRET_1>` (`cdef`) and `gh`."""
    r = _registering({"<SECRET_1>": "cdef", "<SECRET_2>": _A})
    assert r.sweep("ab<SECRET_1>gh") == "<SECRET_2>", (
        "the short run was cut"
    )  # a reverse hit: the run's value is `<SECRET_2>`'s
    assert len(r.mapping) == 2


def test_g9_a_union_that_holds_a_secret_is_a_secret_even_when_an_identifier_comes_first():
    """An input that occurs: `0.5-Xyz9` is a password, `10.100.200.5` an address found by its pattern. The address is replaced first
    (longer, standalone there) and the secret's tail `-Xyz9` stood readable after `<IPV4_1>`. The run starts with an IPV4 token but holds a
    secret: its union is a SECRET (swept in every copy, never restored by the gate's side), not an IPV4 (mutant G9-8)."""
    secret = "0.5" + "-Xyz9"
    text = f"password={secret}\nhost 10.100.200.5-Xyz9 up"
    result = R.redact(text)
    assert result.text == "password=<SECRET_1>\nhost <SECRET_2> up", (
        "the union of an address and a secret is not a SECRET"
    )
    assert result.mapping == {
        "<SECRET_1>": secret,
        "<IPV4_1>": "10.100.200.5",
        "<SECRET_2>": "10.100.200.5-Xyz9",
    }
    r = _registering({"<IPV4_1>": "10.100.200.5", "<SECRET_1>": secret})
    assert r.sweep("10.100.200.5-Xyz9 y") == "<SECRET_2> y"


def test_g9_a_union_whose_value_the_map_holds_reuses_that_placeholder_whatever_its_kind():
    """Design M3 (v3): the run's value `abcdefghijkl` is already held, under TENANT. The union is that placeholder, as `_place_union` has
    always answered a held value: no second placeholder for one value, so `reverse` and runmap's `_rules_conflict` are not disturbed. The
    value was restorable before G9 already (its standalone copies are swept as TENANT_1); stated in section 11 (mutant G9-9)."""
    r = _registering({"<TENANT_1>": _A + "ijkl", "<SECRET_1>": _A, "<SECRET_2>": _B})
    assert r.sweep("z" + _A + "ijkl y") == "z<TENANT_1> y", "a held value got a second placeholder"
    assert len(r.mapping) == 3


def test_g9_a_union_of_identifiers_only_is_an_identifier():
    r = _registering({"<TENANT_1>": "acme-prod-01", "<TENANT_2>": "prod-01-eu"})
    assert r.sweep("acme-prod-01-eu") == "<TENANT_3>"
    assert r.mapping["<TENANT_3>"] == "acme-prod-01-eu"


def test_g9_a_union_registers_its_value_only_no_pieces_and_no_written_form():
    """A G9 union adds ONE entry (its value): no secret-shaped piece of its readable part, no written form. With pieces, the readable tail
    `hIjK1mNoPq2R` was registered and a hostile chain needed a pass more per link (measured: 3, 4, refused; mutant G9-10)."""
    s1, s2 = "xY7wV6uT5s" + "R4aB3dE5fG9", "G9" + "hIjK1mNoPq2R"
    r = _registering({"<SECRET_1>": s1, "<SECRET_2>": s2})
    assert r.sweep(s1 + "hIjK1mNoPq2R end") == "<SECRET_3> end"
    assert r.mapping == {"<SECRET_1>": s1, "<SECRET_2>": s2, "<SECRET_3>": s1 + "hIjK1mNoPq2R"}, (
        "the union registered more than its value"
    )
    assert r._spelled == {}


def _chain(depth: int) -> str:
    """The design critic's chain (round 1 M2): S1 ends with `G9`, S2 = `G9hIjK1mNoPq2R`; then `depth` lines `at <the first 12-k
    characters of hIjK1mNoPq2R><a secret starting with the next one>`: with pieces registered, the piece of pass k straddles line k+1's token."""
    tail = "hIjK1mNoPq2R"
    secrets = ["xY7wV6uT5s" + "R4aB3dE5fG9", "G9" + tail]
    rows = []
    for k in range(1, depth + 1):
        x = tail[12 - k] + ["sT7uVw9z", "wQ4eZ5tY", "kL8mN2bV", "pO3iU7yT"][k - 1]
        secrets.append(x)
        rows.append(f"at {tail[: 12 - k]}{x} ;")
    return "\n".join([f"password={s}" for s in secrets] + [f"see {secrets[0]}{tail} end", *rows])


def test_g9_the_hostile_chain_settles_in_two_passes(monkeypatch):
    """The chain that needs 3 passes (depth 1), 4 (depth 2) and is refused (depth 3, 4) when unions register pieces settles in at most
    2 passes per sweep here, every depth: a union adds only its own value."""
    passes = _passes_per_sweep(monkeypatch)
    for depth in range(5):
        passes.clear()
        out = R.redact(_chain(depth)).text
        assert "hIjK1mNoPq2R" not in out and out.count("see <SECRET_") == 1, out
        assert max(passes) <= 2, (depth, passes)


def test_g9_a_redactor_that_may_not_register_masks_an_overlap_with_the_existing_placeholders():
    """The gate's redactor (L-D1 default): it may not add to the map, so the run is masked with the placeholders of the values that cover
    its readable part (`<SECRET_1><SECRET_2>`): nothing readable, nothing invented, the map untouched (mutant G9-4)."""
    r = R._Redactor({"<SECRET_1>": _A, "<SECRET_2>": _B})
    assert r.sweep("x " + _A + "ijkl y") == "x <SECRET_1><SECRET_2> y", (
        "gate: not masked with existing placeholders"
    )
    assert (
        r.sweep("x <SECRET_1>ijkl y") == "x <SECRET_1><SECRET_2> y"
    )  # a placeholder already in the text (an earlier call's)
    assert r.sweep("x <SECRET_1><SECRET_2> y") == "x <SECRET_1><SECRET_2> y"
    assert r.mapping == {"<SECRET_1>": _A, "<SECRET_2>": _B}


def test_g9_a_redactor_that_may_not_register_masks_an_identifier_overlap_with_the_identifiers_placeholders():
    """Design M4 (v3): a readable character covered only by an identifier is replaced by that identifier's EXISTING placeholder, never a
    refusal (two identifiers that overlap refused every call carrying them in v2, and the result depended on the map order). Restored, the
    shared part appears twice (`acme-prod-01` + `prod-01-eu`): stated in 11. Where a secret also covers the character, the secret's
    placeholder is written (mutant G9-13)."""
    tenants = R._Redactor({"<TENANT_1>": "acme-prod-01", "<TENANT_2>": "prod-01-eu"})
    assert tenants.sweep("acme-prod-01-eu") == "<TENANT_1><TENANT_2>"
    assert len(tenants.mapping) == 2
    for m in (
        {"<SECRET_1>": "ab-cd", "<TENANT_1>": "cd-ef"},
        {"<TENANT_1>": "cd-ef", "<SECRET_1>": "ab-cd"},
    ):
        assert R._Redactor(m).sweep("x ab-cd-ef y") == "x <SECRET_1><TENANT_1> y", (
            m
        )  # the same whatever the map order
    both = R._Redactor({"<SECRET_1>": "ab-cd-ef", "<TENANT_1>": "ef-gh", "<SECRET_2>": "f-gh"})
    # `-gh` is covered by both: the secret is written
    assert both.sweep("x ab-cd-ef-gh y") == "x <SECRET_1><SECRET_2> y", (
        "an identifier was written where a secret covers"
    )


def test_g9_a_sweep_that_settles_in_the_fourth_pass_is_accepted(monkeypatch):
    r = _registering({"<SECRET_1>": SHORT})
    calls: list[str] = []

    def overlaps(out, deadline, work):
        calls.append(out)
        return [(0, len(out), "SECRET", None)] if len(calls) < defaults.SPELLED_MAX_PASSES else []

    monkeypatch.setattr(r, "_overlaps", overlaps)
    monkeypatch.setattr(r, "_close", lambda out, spans, deadline, work: out)
    assert r.sweep("x <SECRET_1> y") == "x <SECRET_1> y"
    assert len(calls) == defaults.SPELLED_MAX_PASSES == 4


def test_g9_a_sweep_that_has_not_settled_after_four_passes_is_refused(monkeypatch):
    r = _registering({"<SECRET_1>": SHORT})
    calls: list[str] = []

    def overlaps(out, deadline, work):
        calls.append(out)
        return [(0, len(out), "SECRET", None)]

    monkeypatch.setattr(r, "_overlaps", overlaps)
    monkeypatch.setattr(r, "_close", lambda out, spans, deadline, work: out)
    with pytest.raises(runmap.InputTooLarge, match="SpelledNotSettled"):
        r.sweep("x <SECRET_1> y")
    assert len(calls) == 4, f"passes {len(calls)}"


def test_g9_a_pass_that_grew_the_map_is_not_the_last(monkeypatch):
    """Converged means: nothing found AND nothing registered in the pass (a union of written forms in `_spelled_sweep` grows the map
    after the build the read-back used). Stubbed: the first body registers a value, the read-back finds nothing: a second pass runs."""
    r = _registering({"<SECRET_1>": SHORT})
    bodies: list[str] = []
    real = r._sweep_once

    def body(out, deadline, work):
        bodies.append(out)
        if len(bodies) == 1:
            r._place("SECRET", "qrstuvwx", "qrstuvwx")
        return real(out, deadline, work)

    monkeypatch.setattr(r, "_sweep_once", body)
    assert r.sweep("x qrstuvwx y") == "x <SECRET_2> y"
    assert len(bodies) == 2, f"bodies {len(bodies)}"


def test_g9_through_redact_a_refusal_is_raised_not_returned(monkeypatch):
    """Class-level stubs (every redactor the call makes): a read-back that always finds a run in a text with a `<`."""

    def never(self, out, deadline, work):
        return [(0, len(out), "SECRET", None)] if "<" in out else []

    monkeypatch.setattr(R._Redactor, "_overlaps", never)
    monkeypatch.setattr(R._Redactor, "_close", lambda self, out, spans, deadline, work: out)
    text = "password=" + SHORT + "qrstu"
    with pytest.raises(runmap.RedactionError, match="SpelledNotSettled"):
        R.redact(text)
    with pytest.raises(runmap.RedactionError, match="SpelledNotSettled"):
        R.redact_many([text, "clean"])
    with pytest.raises(runmap.RedactionError, match="SpelledNotSettled"):
        runmap.redact_text(text, runmap.RunMap())


def test_g9_an_honest_text_settles_in_one_pass(monkeypatch):
    r = _registering(None)
    out = r.find("password=" + SHORT + "qrstu and token=" + SHORT + " and again " + SHORT)
    calls: list[int] = []
    real = r._overlaps
    monkeypatch.setattr(r, "_overlaps", lambda *a: calls.append(1) or real(*a))
    swept = r.sweep(out)
    assert SHORT not in swept and len(calls) == 1, (swept, calls)


def test_g9_the_read_back_is_counted_per_piece_and_refused_before_it_is_built(monkeypatch):
    """Forged copies of a key whose value is long (`x<SECRET_1> ` 20,000 times, a 2,000-character value): read back whole E would be 40
    million characters. Every piece is counted BEFORE it is appended: with the limit at 100,000 the read-back is refused after about 50
    pieces and never holds more (peak traced memory under 1 MB; counted after building, the peak was 56 MB; mutant G9-5)."""
    long = ("Qz9" * 700)[:2000]
    r = R._Redactor({"<SECRET_1>": long})
    r.sweep("")
    text = "x<SECRET_1> " * 20_000
    monkeypatch.setattr(defaults, "SPELLED_MAX_WORK", 100_000)
    tracemalloc.start()
    try:
        with pytest.raises(runmap.InputTooLarge, match="SpelledWorkTooMuch"):
            r._overlaps(text, None, [0])
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    assert peak < 1_000_000, f"peak traced {peak}"
    with pytest.raises(runmap.InputTooLarge, match="SpelledWorkTooMuch"):
        r.sweep(text)


def test_g9_the_count_reads_the_clock_each_time_it_passes_a_multiple_of_1024(monkeypatch):
    """`_spend`, the one count of a sweep call: past `SPELLED_MAX_WORK` it refuses (`SpelledWorkTooMuch`); with a deadline it reads the
    clock when the count crosses a multiple of `_SPELL_CHECK_EVERY` (1,024), not otherwise (mutant G9-14). A deadline of -1.0 is spent at
    any reading."""
    r = R._Redactor(None)
    with pytest.raises(runmap.InputTooLarge, match="InputTooLarge"):
        r._spend([1000], 30, -1.0)  # 1,000 -> 1,030: crosses 1,024
    r._spend([0], 30, -1.0)  # 0 -> 30: no reading
    monkeypatch.setattr(defaults, "SPELLED_MAX_WORK", 100)
    with pytest.raises(runmap.InputTooLarge, match="SpelledWorkTooMuch"):
        r._spend([90], 11, None)


def test_g9_the_read_back_reads_the_deadline(monkeypatch):
    """The read-back reads the clock through the count (the body is stubbed so that it reads none; the gate's redactor registers nothing,
    so no `_build` reads it either). A spent deadline refuses at the first reading; a future one returns the text masked."""
    r = R._Redactor({"<SECRET_1>": _A, "<SECRET_2>": _B})
    r.sweep("")
    text = " ".join(["w<SECRET_1>ijkl"] * 200)  # read back: about 3,400 characters
    monkeypatch.setattr(r, "_sweep_once", lambda out, deadline, work: out)
    readings = _stepping_clock(monkeypatch)
    with pytest.raises(runmap.InputTooLarge, match="InputTooLarge"):
        r.sweep(text, 0.5)
    assert readings["n"] == 1
    assert r.sweep(text, 1e9) == " ".join(["w<SECRET_1><SECRET_2>"] * 200)


def test_g9_the_finder_groups_read_the_deadline_between_them():
    """Design M5 (v3): a finder pass over E is not counted (a map nested past `_MAX_NESTING` splits into up to 64 groups, and counting
    the text read back once per group refused honest texts); the deadline is read before each group instead. Here the text read back is too
    short for the count to read the clock, so only that reading refuses (mutant G9-16)."""
    comb = "".join(chr(97 + (i * 7) % 26) for i in range(260))
    nested = {f"<SECRET_{n + 10}>": comb[:n] + "Z" for n in range(4, 261)}
    r = R._Redactor({"<SECRET_1>": _A, "<SECRET_2>": _B, **nested})
    r.sweep("")
    assert len(r._finders) >= 2, len(r._finders)
    with pytest.raises(runmap.InputTooLarge, match="InputTooLarge"):
        r._overlaps("x <SECRET_1>ijkl y", -1.0, [0])
    assert [s[:2] for s in r._overlaps("x <SECRET_1>ijkl y", None, [0])] == [(2, 16)]


def test_g9_the_read_back_counts_its_pieces_and_its_occurrences():
    """The units of one read-back, exactly: one per character of E (`x abcdefghijkl y`, 16), one per occurrence found (`abcdefgh`,
    `efghijkl`: 2); the finder passes are not counted (design M5, v3). The union's characters are counted by `_close` (mutant G9-15)."""
    r = R._Redactor({"<SECRET_1>": _A, "<SECRET_2>": _B})
    r.sweep("")
    assert len(r._finders) == 1 and not r._slow
    work = [0]
    assert [s[:2] for s in r._overlaps("x <SECRET_1>ijkl y", None, work)] == [(2, 16)]
    assert work == [16 + 2], work


def test_g9_a_union_is_counted_with_its_whole_value_before_it_is_built():
    """Design B1 (v3): `_close` counts the union's VALUE (every token of the run put back), not the run's length in the text: a run of one
    token of a 1,000-character secret and 7 readable characters costs 1,007 units, not 17 (mutant G9-17)."""
    long = "".join(f"{n:03d}Q" for n in range(250))  # 1,000 characters
    r = _registering({"<SECRET_1>": long, "<SECRET_2>": long[-5:] + "XY00001"})
    work = [0]
    out = r._close("<SECRET_1>XY00001 end", [(0, 17, "SECRET", None)], None, work)
    assert out == "<SECRET_3> end" and r.mapping["<SECRET_3>"] == long + "XY00001"
    assert work == [1007], work


def _planted(lines: int, secret: int = 20_000) -> str:
    """Design B1's shape, scaled: one long secret found by its key, `lines` short secrets that each overlap its tail, and `lines` copies
    of its placeholder each followed by one of them: every line is a union of the whole long secret and a few characters."""
    rng = random.Random(29)  # noqa: S311 - a seeded test generator, not a secret
    t0 = "".join(
        rng.choice("ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789")
        for _ in range(secret)
    )
    keys = [f"token={t0[-5:]}XY{i:05d}" for i in range(lines)]
    return "\n".join([f"password={t0}", *keys, *(f"<SECRET_1>XY{i:05d}" for i in range(lines))])


def test_g9_the_unions_of_one_call_are_limited_in_characters_and_the_call_is_refused(monkeypatch):
    """Design B1 (v3): the characters of the unions one call registers are counted (`_union_chars`) and the CALL is refused past
    `defaults.SPELLED_MAX_UNION_CHARS` (`InputTooLarge("SpelledUnionTooMuch")`, nothing shown), as `SPELLED_MAX_CHARS` refuses a registry
    that grows too big. With the limit at 100,000: 4 unions of 20,007 characters pass, the 5th is refused (mutant G9-18). Measured at the
    real limit: the 130,000-character secret with 300 such lines held 39 MB of map values in v2 and is refused here (section 9.4)."""
    monkeypatch.setattr(defaults, "SPELLED_MAX_UNION_CHARS", 100_000)
    result = R.redact(_planted(4))
    assert (
        "XY00003" not in result.text and sum(len(v) == 20_007 for v in result.mapping.values()) == 4
    )
    with pytest.raises(runmap.InputTooLarge, match="SpelledUnionTooMuch"):
        R.redact(_planted(5))
    with pytest.raises(runmap.InputTooLarge, match="SpelledUnionTooMuch"):
        runmap.redact_text(_planted(5), runmap.RunMap())


def test_g9_a_union_does_not_rebuild_the_finders(monkeypatch):
    """Design M6 (v3): a G9 union needs no sweep rule (a copy of its value elsewhere holds the overlap that made it; the read-back finds
    it again and `_place_union` answers from `reverse`), so registering one does not rebuild the finders. A bundle with one overlap per
    string rebuilt them once per string before (1,000 strings: 85 s instead of 0.5 s, section 9.4; mutant G9-19)."""
    r = _registering({"<SECRET_1>": _A, "<SECRET_2>": _B})
    r.sweep("")
    builds: list[int] = []
    real = r._build
    monkeypatch.setattr(r, "_build", lambda: builds.append(1) or real())
    assert r.sweep("x " + _A + "ijkl y") == "x <SECRET_3> y"
    assert r.sweep("z " + _A + "ijkl " + _A + "ijkl") == "z <SECRET_3> <SECRET_3>"
    assert builds == [] and len(r.mapping) == 3, f"builds {builds}"


@pytest.mark.perf
def test_g9_the_read_back_costs_about_two_sweeps_of_the_text_it_reads():
    """The cookie log of 300 prefix lengths, its copies x 4 (the shape the scan's ratio test uses). The read-back of the swept text costs
    about what a sweep of the raw text it stands for costs (measured 2.1 times on the test machine); a read-back that walked every
    token's value again per occurrence is far over it. Perf-marked: a ratio of two timings (readiness nit)."""
    log = _cookie_log(300)
    probe = "\n".join([_copies_of(log)] * 4)
    r = R._Redactor(None)
    r.find(log)
    r.sweep("")
    swept = r._sweep_once(probe, None, [0])
    raw = R._PLACEHOLDER.sub(lambda m: r.mapping.get(m.group(1), m.group(1)), swept)
    read_back = _best_cpu(lambda: r._overlaps(swept, None, [0]))
    r._overlaps = lambda *a: []
    plain = _best_cpu(lambda: r.sweep(raw))
    assert plain > 0.015, plain
    assert read_back < 4 * plain + 0.01, (read_back, plain)


def test_g9_a_long_value_beside_readable_text_is_read_back_only_the_reach_deep():
    """Found by the whole suite on the v2 prototype (tests/test_k5_fixes4.py, 1.2 s -> 40 s): `x` x 262,143 + ` ` is one HIGHENTROPY token
    and a space (20,000 here); read back whole, the finder tried the long value at every position of a periodic E (quadratic). A run is read back at
    most `defaults.SPELLED_READBACK_REACH` (1,024) characters deep on each side that touches readable text; deeper, the anchored check
    searches its anchor in the long rule ONCE per distinct anchor (units: E = a separator, 1,024 `x`, the space; one per edge and long
    rule; 20,000 for the search; a second copy of the same edge adds its E and one unit, no second search; mutant G9-20).
    Since the E17 review the scan of the feasibility window is counted too (`hi - lo`, once per distinct window; the figures below were
    21,027 and 43,079 before): 1,025 for the first text (window [18,975, 20,000)); the second text has three edges, windows of 1,025,
    20,000 and 20,000 characters (the left edge of the second token can read the whole rule: 20,000), 41,025 in all."""
    r = R._Redactor({"<HIGHENTROPY_1>": "x" * 20_000})
    r.sweep("")
    reach = defaults.SPELLED_READBACK_REACH
    work = [0]
    assert r._overlaps("<HIGHENTROPY_1> ", None, work) == []
    assert work == [(1 + reach + 1) + 1 + 20_000 + 1_025], work
    work = [0]
    assert r._overlaps("<HIGHENTROPY_1> <HIGHENTROPY_1> ", None, work) == []
    # 2 distinct anchors (` ` after a token, ` ` before one): 2 searches, 3 edges
    assert work == [(1 + reach + 1 + reach + 1 + reach + 1) + 3 + 2 * 20_000 + 41_025], work


def test_g9_an_overlap_deeper_than_the_reach_is_found_by_the_anchored_check():
    """Design M1 (v3): a value that overlaps a token by more than `SPELLED_READBACK_REACH` characters is found by the anchored check
    (`_deep_hits`) and masked: on the right of a token, on its left, through a run of two tokens, and at the gate (masked with the existing
    placeholders). Before v3 the first was a stated limit (`<SECRET_1>TAIL1234`; mutant G9-21)."""
    base = "".join(f"{n:04x}Qz" for n in range(200))  # 1,200 characters, not periodic
    tail = "TAIL" + "1234"
    for depth in (1_100, 1_000):
        r = _registering({"<SECRET_1>": base, "<SECRET_2>": base[1200 - depth :] + tail})
        assert r.sweep(base + tail) == "<SECRET_3>", depth
        assert r.mapping["<SECRET_3>"] == base + tail
    left = _registering({"<SECRET_1>": base, "<SECRET_2>": "HEAD" + "5678" + base[:1_100]})
    assert left.sweep("HEAD5678" + base) == "<SECRET_3>"
    two = _registering(
        {"<SECRET_1>": base[:600], "<SECRET_2>": base[600:], "<SECRET_3>": base[50:] + tail}
    )
    assert two.sweep("<SECRET_1><SECRET_2>" + tail) == "<SECRET_4>"
    assert (
        runmap.enforce_map(base + tail, {"<SECRET_1>": base, "<SECRET_2>": base[100:] + tail})
        == "<SECRET_1><SECRET_2>"
    )


def test_g9_a_long_periodic_value_beside_its_own_period_is_refused_by_the_count():
    """The anchored check compares the rule at every place its anchor is found, at every edge; a PERIODIC long value (`x` x 1,100) beside
    readable text of the same period finds its anchor at 76 places, and each comparison at each of the 30 cut edges is counted
    (`2 x len(w) + 2` units): about 5 million, refused (`SpelledWorkTooMuch`), not walked (stated in 11; mutant G9-22)."""
    r = _registering({"<SECRET_1>": "x" * 1_100})
    with pytest.raises(runmap.InputTooLarge, match="SpelledWorkTooMuch"):
        # `<SECRET_9>` is not a key: the run of `<SECRET_1>` touches readable text on its right only, so it is cut at the reach there
        r.sweep(("<SECRET_9><SECRET_1>" + "x" * 200 + " end\n") * 30)


def test_g9_constants_hold_sane_values():
    """The G9 constants (defaults.py) are plain numbers with no validation at load; this pins the values a change must keep sane: at least
    two passes (a body and one read-back), a positive reach below the rule length the anchored check is for, positive limits, and the
    union limit at most the sweep's work limit times the characters a unit stands for (a plain bound check, not the effective limit:
    `MAX_MAP_CHARS` is, see defaults.py)."""
    assert defaults.SPELLED_MAX_PASSES >= 2
    assert 1 <= defaults.SPELLED_READBACK_REACH <= 65_536
    assert defaults.SPELLED_MAX_UNION_CHARS > 0 and defaults.SPELLED_MAX_WORK > 0
    assert defaults.SPELLED_MAX_UNION_CHARS >= defaults.MAX_REDACT_CHARS


def test_g9_the_anchored_check_searches_only_the_feasibility_window_and_counts_it():
    """E17 + G9 result review (design M1, M2): `_deep_hits` searches the anchor of an edge only in the window `[lo, hi)` of the long rule
    whose comparison could succeed (the text that can be read back on each side of the edge bounds it), and counts the scan of that window
    (`hi - lo` units, once per distinct window). Exact units (not a timing), `_overlaps` on a swept text, no clock:
    (a) `x<SECRET_2>`, SECRET_2 = `x` x 1,030 (the rule, 1,030 long, anchor = the free `x` + 1,024 of the run = 1,025 characters): the
    window is [0, 1,025) (hi = 1 - 1 + 1,025), one place, one comparison. Units: E 1,026 (the text read back) + 1 (edge, rule) + 1,030 (the
    anchor searched in the rule) + 1,025 (the window scan) + 1,025 (a place found) + 2,062 (2 x 1,030 + 2, the comparison) = 6,169; the
    hit is found. (b) a second long rule, `x` x 1,100, cannot fit beside `x` + a 1,030-character run (1 + 1,030 < 1,100): its window
    [69, 1,025) is shorter than the anchor: skipped, no scan, no place, no comparison: it adds exactly 1 + 1,100 = 1,101 units (7,270) and
    no hit. (c) `<SECRET_1>x` (the 1,100 rule, window [75, 1,100): lo = 1,100 - 1 - 1,024): 1,026 + 1 + 1,100 + 1,025 + 1,025 + 2,202 = 6,379.
    Mutants G9-25 .. G9-30 (the skip, lo and hi each moved by one, the scan not counted)."""
    word = "x" * 1_030
    r = R._Redactor({"<SECRET_2>": word})
    r.sweep("")
    work = [0]
    assert r._overlaps("x<SECRET_2>", None, work) == [(0, 11, "SECRET", "<SECRET_2><SECRET_2>")]
    assert work == [6_169], f"(a) {work}"
    r = R._Redactor({"<SECRET_1>": "x" * 1_100, "<SECRET_2>": word})
    r.sweep("")
    work = [0]
    assert r._overlaps("x<SECRET_2>", None, work) == [(0, 11, "SECRET", "<SECRET_2><SECRET_2>")]
    assert work == [7_270], f"(b) {work}"
    r = R._Redactor({"<SECRET_1>": "x" * 1_100})
    r.sweep("")
    work = [0]
    assert r._overlaps("<SECRET_1>x", None, work) == [(0, 11, "SECRET", "<SECRET_1>")]
    assert work == [6_379], f"(c) {work}"


def test_g9_the_read_back_judges_a_phone_copy_by_the_sweeps_joins():
    """G8 + G9 (ticket G8 v5, 8.1): the read-back judges a copy by the literal sweep's rule, `redact._joins`: the read-back
    `x` + `4155550132` is a copy of the known PHONE value (G8's sweep replaces it when it is written raw), `7` + it is not."""
    phone = "415" + "555" + "0132"
    r = _registering({"<TENANT_1>": phone[:8], "<PHONE_1>": phone})
    assert r.sweep("x<TENANT_1>32 y") == "x<PHONE_1> y"
    assert r.sweep("7<TENANT_1>32 y") == "7<TENANT_1>32 y"
    assert r.mapping == {"<TENANT_1>": phone[:8], "<PHONE_1>": phone}


def test_g9_a_gate_text_that_mentions_a_long_value_many_times_is_masked_not_refused():
    """Round 2 plan review (design, ticket G4 L26): at the gate a text that writes the placeholder of a long value many times
    (`step i see <SECRET_1> now.`, each read back next to readable text) is masked as before, not refused: the shared count of
    G9 v3 does not charge a finder pass per mention (the anchor of the anchored check is searched once). 300 mentions of a
    5,000-character value (about 2,000 units each, 0.6 million of the 4 million allowed)."""
    value = "".join(f"{n:04x}Qz" for n in range(700))  # 4,900 characters, not periodic
    text = "".join(f"step {i} see <SECRET_1> now.\n" for i in range(300))
    assert runmap.enforce_map(text, {"<SECRET_1>": value}) == text
    assert runmap.enforce_map(text + value, {"<SECRET_1>": value}) == text + "<SECRET_1>"
