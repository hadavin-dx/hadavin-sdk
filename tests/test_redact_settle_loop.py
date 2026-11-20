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


def test_5000_compound_secrets_at_the_size_cap_the_trie_walk_is_not_dict_misses():
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
    with_forms = _best_cpu(lambda: r.sweep(probe))
    held, r._spelled = r._spelled, {}
    without = _best_cpu(lambda: r.sweep(probe))
    r._spelled = held
    assert with_forms < 4 * without + 0.05, (with_forms, without)


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
    return _best_cpu(lambda: r.sweep(probe))


def _copies_of(log: str) -> str:
    """The cookie lines of `log` as the first sweep leaves other copies: `Cookie: <prefix>; sid=<JWT_1>`."""
    return "\n".join(line.replace(JWT, "<JWT_1>") for line in log.splitlines()[1:])


def test_the_scan_does_not_depend_on_how_many_distinct_prefix_lengths_are_registered():
    """The cost of a token is the prefix that really matches before it, not the number of offsets registered under it: the copies of 300
    DIFFERENT prefix lengths cost about what the copies of ONE length cost. A scan that walks every offset for every token (round 4's)
    is far slower on the first and fails the ratio (a mutant of the scan, recorded in evidence G7-1.md)."""
    many, one = _cookie_log(300), _cookie_log(300, same_prefix=True)
    with_many = _swept_cpu(_copies_of(many), many)
    with_one = _swept_cpu(_copies_of(one), one)
    assert with_many < 4 * with_one + 0.05, (with_many, with_one)


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
    assert with_forms < 4 * without + 0.1, (with_forms, without)  # measured 1.1 times


def _deep_hostile() -> tuple[str, str]:
    """(forms, probe): 300 forms `a^k<SECRET_1>Z^60`, then 130 KB that matches the prefix of every one and 59 of the 60 suffix characters
    of each: every token walks 300 prefixes x 59 suffix steps (about 5e6 units over the whole text)."""
    block = "a" * 300 + "<SECRET_1>" + "Z" * 59 + "\n"
    return _hostile_forms(300, 60), block * (130_000 // len(block))


def test_the_work_of_the_scan_is_bounded_a_hostile_text_is_refused_not_walked_to_the_end(
    monkeypatch,
):
    """The total work of a scan (steps of both walks, and tokens) is counted and refused past `defaults.SPELLED_MAX_WORK`
    (InputTooLarge("SpelledWorkTooMuch")). The deep text needs about 5e6 units: refused at the real limit, and scanned to the end when the limit
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
    """The limit is derived from a measurement: the honest logs at the size cap (cookie copies of 300 prefix lengths, signed ids with 300
    suffixes) need under a tenth of it (about 6 percent and 2 percent measured, evidence G7-1.md): they scan to the end with the limit cut
    to a tenth."""
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
    """The limit is not the only bound: with it raised the same deep text would cost about half a second, and a deadline 0.05 s away stops it
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
    """The steps of a walk are counted too: the deep hostile text (about 5e6 units) reads the clock thousands of times, not once per token."""
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


def test_an_overlap_completed_only_in_a_later_round_leaves_the_swallowed_part_readable_a_stated_limit():
    """The part of the overlap that is NOT fixed (stated in `_spelled_sweep`, defaults.py and the ticket): round 2 registers F1 `<SECRET_1>ab`
    and sweeps `xyz<SECRET_1>ab` to `xyz<F1>`; round 3 registers F2 `xyz<SECRET_1>` (a chain through another line). The text is now
    `xyz<F1>`: F2 no longer matches it and `xyz`, three characters of a value the map holds, stands readable. Pinned so that a change is looked
    at; the size of the leak is the literal prefix (or tail) of the later form."""
    r = R._Redactor({"<SECRET_1>": SHORT})
    f1 = r._place("BEARER", SHORT + "ab", "<SECRET_1>ab")
    round2 = r._spelled_sweep("xyz<SECRET_1>ab", None)
    assert round2 == f"xyz{f1}"
    f2 = r._place("BEARER", "xyz" + SHORT, "xyz<SECRET_1>")
    round3 = r._spelled_sweep(round2, None)
    assert (
        round3 == f"xyz{f1}" != f2
    )  # `xyz` stays: nothing re-reads a text an earlier sweep consumed
    assert r.mapping[f2] == "xyz" + SHORT


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

    monkeypatch.setattr(R.time, "thread_time", clock)
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
    """Item 1 holds a bank word only in a folded view (full-width BSB): `bank_near` flips while it is read. Items 0 and 1 are re-read, 2 and 3 are not."""
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
    items = _flip_items()
    calls: list[str] = []
    real = R._Redactor.find

    def find(self, text):
        calls.append(text)
        return real(self, text)

    monkeypatch.setattr(R._Redactor, "find", find)
    out, mapping = R.redact_many(items)
    assert [calls.count(i) for i in items] == [2, 2, 1, 1]  # not [2, 2, 2, 2]
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
# The most rounds `settle` ran on any generated composition. The depth distribution is NOT repeated here: it is printed by the test below
# (with -s) and recorded, from a real run, in handover/core-c/evidence/G7-1.md ("G7 fix round 4", raw tail). Pinned: a change that makes a
# chain deeper is looked at.
MAX_ROUNDS_SEEN = 3


def test_generated_compositions_match_the_reference_loop_and_leave_no_raw_copy(monkeypatch):
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
    # Output only (shown with `pytest -s`; no assertion reads it): the distribution that handover/core-c/evidence/G7-1.md quotes.
    print(
        f"\ngenerated {GENERATED} compositions of 4 to 8 lines (seed 20261121): settle rounds run {dict(sorted(rounds_hist.items()))} "
        f"(cap {R._SETTLE_ROUNDS}, most {most_rounds}); reference loop, pass that last changed something, exactly "
        f"{dict(sorted(last_hist.items()))}; cumulative: third pass or more {needed_third}, fourth or more {needed_fourth}; {refused} refused"
    )
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
