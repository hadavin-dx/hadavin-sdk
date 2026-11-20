"""G7 fix round 2 (ORDER 020 MJ-B, review findings dz-1 .. dz-4, cb-M2 .. M4): the capped fixed-point loop of `_Redactor.settle`.

After the first sweep the whole pattern table runs again over the strings the sweep changed; a round that grows the map
sweeps every string again, and the strings THAT sweep changed go round again; at most `_SETTLE_ROUNDS` (4) rounds, then
the call is REFUSED (RedactionError, nothing shown). Every round has a deadline from the same CPU clock as
`REDACT_BUDGET_S` (InputTooLarge, never a skipped pass). A compound secret found late is also swept by its
placeholder-spelled form (`<SECRET_1>xy`), so its other copies keep no tail.

What is here: the chains that used to leave a value readable (and the fail-before lines in evidence/G7-1.md), the cap
and the deadline, the cheap cases that pay nothing, the pattern nits (AZURESAS `sig=`, `"auth":`), the documented
boundary class, a generator aimed at the class compared with a reference fixed-point loop, and one perf test at the
size cap. Every credential is made up and built from parts.
"""

from __future__ import annotations

import importlib
import random
import sys
import time

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


def test_a_chain_that_needs_more_rounds_than_the_cap_is_refused_never_returned_half_masked(
    monkeypatch,
):
    assert R._SETTLE_ROUNDS == 4  # the cap of ORDER 020 MJ-B
    monkeypatch.setattr(
        R, "_SETTLE_ROUNDS", 1
    )  # the chain above needs 2: at a cap of 1 it must refuse
    with pytest.raises(runmap.RedactionError) as err:
        R.redact(CHAIN3)
    assert ACCOUNT not in str(err.value) and V not in str(err.value)
    with pytest.raises(runmap.RedactionError):
        R.redact_many([f"password={V}", f"BSB: {BSB}{V}", f"paid {BSB}/{ACCOUNT}"])
    with pytest.raises(runmap.RedactionError):
        runmap.redact_text(CHAIN3, runmap.RunMap())
    assert R._SETTLE_ROUNDS == 1  # (monkeypatched) and the shapes that need one round still work
    assert "<BANKACCT_1>" in R.redact(f"BSB: {BSB}\npaid {BSB}/{ACCOUNT}").text


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


def test_the_chain_of_three_is_three_pattern_passes_over_the_text_it_changed(monkeypatch):
    calls = _counted(monkeypatch)
    R.redact(CHAIN3)
    assert calls["find"] == 3 and calls["sweep"] == 3  # pass 1, then the changed text twice


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

    values = {f"<TENANT_{n}>": f"val{n:04d}" for n in range(1, 1500)}
    text = " ".join(values.values()) * 40
    r = R._Redactor(values)
    expected = R._Redactor(values).sweep(text)
    assert r.sweep(text, None) == expected  # None: as before
    assert r.sweep(text, time.thread_time() + 600.0) == expected
    with pytest.raises(InputTooLarge):
        r.sweep(text, time.thread_time() - 1.0)  # a spent deadline stops the sweep


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


# --- dz-4 / cb-M3: a generator aimed at the class, against a reference fixed-point loop ---------------------------------

_RARE = "qxzjkvw"


def _token(rng: random.Random, low: int, high: int) -> str:
    return "".join(rng.choice(_RARE) for _ in range(rng.randint(low, high)))


def _lines(rng: random.Random) -> tuple[list[str], list[str], list[str]]:
    """(lines, secret values, tails that must not stay readable). The first value is always declared by a key=V line."""
    value = "".join(rng.choice("abcdefghmnprstu") for _ in range(3)) + rng.choice("0123456789")
    lines, tails = [f"password={value}"], []
    pool = [
        "bank-glued",
        "account-after-code",
        "bearer",
        "basic",
        "authorization",
        "sig",
        "auth",
        "copy",
        "copy",
        "second-key",
    ]
    chosen = rng.sample(pool, rng.randint(1, 3))
    compound_tail = ""
    for kind in chosen:
        if kind == "bank-glued":
            lines.append(f"BSB: {BSB}{value}")
        elif kind == "account-after-code":
            lines.append(f"paid {BSB}/{ACCOUNT}")
        elif kind == "bearer":
            tail = _token(rng, 2, 7)
            tails.append(tail)
            compound_tail = compound_tail or tail
            lines.append(f"Bearer {value}{tail}")
        elif kind in ("basic", "authorization"):
            tail = _token(rng, 2, 3)
            tails.append(tail)
            lines.append(f"{'Basic ' if kind == 'basic' else 'authorization: '}{value}{tail}")
        elif kind == "sig":
            tail = _token(rng, 6, 11)
            tails.append(tail)
            lines.append(f"GET /x?sig={value}{tail}")
        elif kind == "auth":
            tail = _token(rng, 2, 3)
            tails.append(tail)
            lines.append(f'{{"auth":"{value}{tail}"}}')
        elif kind == "copy":
            if compound_tail:  # a copy of the compound value (and more) in another string
                lines.append(
                    f"note {value}{compound_tail}{''.join(rng.choice('ghl') for _ in range(rng.randint(2, 4)))} end"
                )
            else:
                lines.append(f"note {value} end")
        else:
            tail = _token(rng, 5, 8)
            tails.append(tail)
            lines.append(f"token={value}{tail}")
    rng.shuffle(lines)
    return lines, [value], tails


def _reference(lines: list[str], cap: int = 6) -> tuple[list[str], dict[str, str], int]:
    """A fixed point built from the redactor's pieces and nothing of `settle`: find every string, sweep every string, then
    find and sweep EVERY string again until neither the texts nor the map change. Returns (texts, map, the number of the
    last pattern pass that still changed something)."""
    r = R._Redactor(None)
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


GENERATED = 2500


def test_generated_compositions_match_the_reference_loop_and_leave_no_raw_copy():
    rng = random.Random(20261121)  # noqa: S311 - a seeded test generator, not a secret
    needed_third = needed_fourth = refused = 0
    for n in range(GENERATED):
        lines, _values, tails = _lines(rng)
        ref_texts, ref_map, last = _reference(lines)
        needed_third += last >= 3
        needed_fourth += last >= 4
        label = f"input {n} (seed 20261121), {len(lines)} lines"
        # redact_many: the lines as separate strings
        try:
            out, mapping = R.redact_many(lines)
        except runmap.RedactionError:
            refused += 1
            raise AssertionError(f"{label}: refused by redact_many") from None
        assert out == ref_texts, f"{label}: redact_many differs from the reference loop"
        assert set(mapping.values()) == set(ref_map.values()), label
        assert not raw_leaks("\n".join(out), mapping, tails), f"{label}: raw copy (redact_many)"
        # redact_text: the lines as one text, one run map, and a second call changes nothing
        run = runmap.RunMap()
        try:
            once = runmap.redact_text("\n".join(lines), run)
        except runmap.RedactionError:
            refused += 1
            raise AssertionError(f"{label}: refused by redact_text") from None
        assert once.split("\n") == ref_texts, (
            f"{label}: redact_text differs from the reference loop"
        )
        assert not raw_leaks(once, dict(run), tails), f"{label}: raw copy (redact_text)"
        held = dict(run)
        assert runmap.redact_text(once, run) == once and dict(run) == held, (
            f"{label}: not a fixed point"
        )
    print(
        f"\ngenerated {GENERATED} compositions: {needed_third} needed a third pattern pass, "
        f"{needed_fourth} a fourth, {refused} refused"
    )
    assert refused == 0
    assert needed_third > 0  # the generator reaches the class this loop is for


def test_the_raw_leak_checker_sees_a_tail_and_a_piece_of_a_secret():
    mapping = {"<SECRET_1>": "ab9x", "<BEARER_1>": "ab9xqrstu", "<IPV4_1>": "10.1.2.3"}
    assert raw_leaks("x <SECRET_1>qrstu y", mapping, ["qrstu"]) == ["<BEARER_1>", "tail"]
    assert raw_leaks("x <BEARER_1> y", mapping, ["qrstu"]) == []
    assert (
        raw_leaks("at 10.1.2.3", mapping, []) == []
    )  # not a secret kind: not this checker's business
    assert raw_leaks("a ab9x b", mapping, []) == ["<SECRET_1>", "<BEARER_1>"]


# --- dz-3: the size cap with the hostile keyword repeated --------------------------------------------------------------


@pytest.mark.perf
@pytest.mark.parametrize("keyword", ["password=", "curl -u "])
def test_T4_a_text_at_the_cap_of_a_hostile_keyword_repeated_with_planted_matches_stays_in_budget(
    keyword,
):
    """`password=` repeated up to the size cap (hostile: a pattern start at every 9 characters, almost none a value) plus planted
    matches that force the extra passes (a known secret, a compound tail, a code and an account), through
    `redact_untrusted` with the views (the text carries a backslash, so the second pass scans them too)."""
    planted = f"password={V}\nBearer {V}qrstu\nnote {V}qrstuvw\nBSB: {BSB}{V}\npaid {BSB}/{ACCOUNT}\nx\\ty\n"
    body = (keyword + " ") * ((defaults.MAX_REDACT_CHARS - len(planted)) // (len(keyword) + 1))
    text = (body + planted)[: defaults.MAX_REDACT_CHARS]
    assert len(text) <= defaults.MAX_REDACT_CHARS
    mapping = runmap.RunMap()
    start = time.thread_time()
    try:
        out = runmap.redact_untrusted(text, mapping)
        took = time.thread_time() - start
        print(f"\nG7 hostile {keyword!r} at the cap ({len(text):,} chars): {took:.2f} s, redacted")
        assert V not in out and ACCOUNT not in out
    except runmap.InputTooLarge:
        took = time.thread_time() - start
        print(
            f"\nG7 hostile {keyword!r} at the cap ({len(text):,} chars): {took:.2f} s, REFUSED (InputTooLarge)"
        )
    # refused or redacted, never past a fixed ceiling: the budget is 6 s of CPU and one pass is not interruptible
    assert took < 4 * defaults.REDACT_BUDGET_S
