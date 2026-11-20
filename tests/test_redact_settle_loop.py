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
def test_a_chain_that_changes_for_up_to_three_rounds_is_settled_with_the_real_cap(
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


# --- round 3 M4: the spelled-form scan is linear in the text, not entries x text --------------------------------------


def _uuid_lines(count: int) -> str:
    rng = random.Random(4242)  # noqa: S311 - a seeded test generator, not a secret
    return "\n".join(
        f"password={uuid.UUID(int=rng.getrandbits(128))}.k_{i % 10}" for i in range(count)
    )


def _best_cpu(fn, repeat: int = 3) -> float:
    best = None
    for _ in range(repeat):
        start = time.thread_time()
        fn()
        took = time.thread_time() - start
        best = took if best is None else min(best, took)
    return best


def test_5000_compound_secrets_at_the_size_cap_are_swept_in_linear_time():
    """5,000 `password=<uuid>.k_i` lines (250,000 characters, under the 262,144 cap) make 5,000 spelled forms
    (`<UUID_n>.k_i`). The old loop searched every form in the whole text, on every sweep: about 5,000 x 250,000 characters
    per sweep (0.17 s here), up to 5 sweeps of one call. Measured here as a RATIO to the same sweep with no spelled form, so
    a slow machine does not matter: linear is about 1.1x, the old loop about 13x."""
    text = _uuid_lines(5000)
    assert 240_000 < len(text) <= defaults.MAX_REDACT_CHARS
    r = R._Redactor(None)
    out = r.find(text)
    assert len(r.mapping) == 10_000  # a UUID and a compound secret per line
    r.sweep(out)  # builds the finders once, as the first sweep of a call does
    with_forms = _best_cpu(lambda: r.sweep(out))
    held, r._spelled = r._spelled, {}
    without = _best_cpu(lambda: r.sweep(out))
    r._spelled = held
    print(
        f"\nG7 spelled scan, 5,000 forms, {len(out):,} chars: {with_forms:.3f} s; no forms {without:.3f} s"
    )
    assert with_forms < 3 * without + 0.03


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
    # a text that needs no second pass is not refused by the check of the extra rounds
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


def test_the_deadline_trips_inside_the_value_loop_not_at_the_segment_check(monkeypatch):
    """Round 3 M6: the text is ONE segment, so a spent deadline trips at the segment check first and the old test could not tell the
    two apart. A stepping clock (one second per reading) with a deadline of 2.5 passes the build check (reading 1) and the segment check
    (reading 2) and trips at reading 3: the first check of the value loop."""
    from hadavin_sdk.guard.runmap import InputTooLarge

    values = {f"<TENANT_{n}>": f"val{n:04d}" for n in range(1, 300)}  # under 512: one build check
    text = " ".join(values.values())
    r = R._Redactor(values)
    readings = {"n": 0}

    def clock() -> float:
        readings["n"] += 1
        return float(readings["n"])

    monkeypatch.setattr(R.time, "thread_time", clock)
    with pytest.raises(InputTooLarge):
        r.sweep(text, 2.5)
    assert readings["n"] == 3


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
    # the first sweep is as before (no deadline); every sweep of a round carries the call's
    assert calls["deadlines"][0] is None and all(d == future for d in calls["deadlines"][1:])
    assert len(calls["deadlines"]) >= 3


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
    out = runmap.redact_text(f"password={word}\nref {word}123-45-6789", mapping := runmap.RunMap())
    assert out == "password=<SECRET_1>\nref <SECRET_1><SSN_1>"
    assert "123-45-6789" in mapping.values()
    fresh = runmap.redact_text(f"ref {word}123-45-6789", runmap.RunMap())
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
# The most rounds `settle` ran on any generated composition (measured 2026-11-20, round 3: 8,000 inputs of 4 to 8 lines,
# half from a pre-seeded map: 1 round 649, 2 rounds 6,788, 3 rounds 563). Pinned: a change that makes a chain deeper is looked at.
MAX_ROUNDS_SEEN = 3


def test_generated_compositions_match_the_reference_loop_and_leave_no_raw_copy(monkeypatch):
    rounds = _rounds_spy(monkeypatch)
    rng = random.Random(20261121)  # noqa: S311 - a seeded test generator, not a secret
    needed_third = needed_fourth = refused = most_rounds = 0
    for n in range(GENERATED):
        lines, seed, tails = _lines(rng)
        ref_texts, ref_map, last = _reference(lines, seed)
        needed_third += last >= 3
        needed_fourth += last >= 4
        label = f"input {n} (seed 20261121), {len(lines)} lines, {len(seed)} seeded"
        # redact_many: the lines as separate strings, from the seeded map
        rounds["n"] = 0
        try:
            out, mapping = R.redact_many(lines, dict(seed))
        except runmap.RedactionError:
            refused += 1
            raise AssertionError(f"{label}: refused by redact_many") from None
        most_rounds = max(most_rounds, rounds["n"])
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
    print(
        f"\ngenerated {GENERATED} compositions of 4 to 8 lines: reference loop needed a third pass for {needed_third}, a fourth for "
        f"{needed_fourth}; settle ran at most {most_rounds} rounds (cap {R._SETTLE_ROUNDS}); {refused} refused"
    )
    assert refused == 0
    assert needed_third > 0 and needed_fourth > 0  # the generator reaches the depth the cap is for
    assert most_rounds == MAX_ROUNDS_SEEN  # the pinned maximum ...
    assert (
        R._SETTLE_ROUNDS - most_rounds >= 1
    )  # ... with at least one round of headroom under the real cap


def test_the_raw_leak_checker_sees_a_tail_and_a_piece_of_a_secret():
    mapping = {"<SECRET_1>": "ab9x", "<BEARER_1>": "ab9xqrstu", "<IPV4_1>": "10.1.2.3"}
    assert raw_leaks("x <SECRET_1>qrstu y", mapping, ["qrstu"]) == ["<BEARER_1>", "tail"]
    assert raw_leaks("x <BEARER_1> y", mapping, ["qrstu"]) == []
    assert (
        raw_leaks("at 10.1.2.3", mapping, []) == []
    )  # not a secret kind: not this checker's business
    assert raw_leaks("a ab9x b", mapping, []) == ["<SECRET_1>", "<BEARER_1>"]


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
@pytest.mark.parametrize("budget", [None, 0.5])
def test_T4_a_text_at_the_cap_with_a_deep_chain_is_redacted_or_refused_within_budget_plus_one_unit(
    monkeypatch, keyword, budget
):
    """The claim (defaults.REDACT_BUDGET_S): the budget is checked between the units of work, so a call that crosses it is refused
    (`InputTooLarge`, nothing shown) after at most the budget PLUS ONE UNINTERRUPTIBLE UNIT: a pattern pass over the biggest
    string, or a sweep of it. The unit is measured here on this machine (one `find` and one `sweep` of the same text) and the
    bound is the budget + twice the unit + 0.5 s. With the real budget the text is redacted (V, the code and the account
    gone); with a budget of 0.5 s it must be REFUSED, so the refusal path is the one measured. `thread_time` is CPU time of the
    calling thread: a caller needs its own wall-clock guard (a blocked or starved thread does not advance it)."""
    text = _hostile_text(keyword)
    probe = R._Redactor(None)
    start = time.thread_time()
    found = probe.find(text)
    probe.sweep(found)
    unit = time.thread_time() - start  # one pattern pass and one sweep over the whole text
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
        f"\nG7 hostile {keyword!r} at the cap, budget {allowed} s: {took:.2f} s, "
        f"{'REFUSED (InputTooLarge)' if refused else 'redacted'}; one pass + sweep {unit:.2f} s"
    )
    if budget is None:
        assert not refused, "the real budget covers this text on the test machine"
        assert V not in out and ACCOUNT not in out and BSB not in out
    else:
        assert refused, "a budget of 0.5 s must refuse (the refusal path is what is measured)"
    assert took <= allowed + 2 * unit + 0.5
