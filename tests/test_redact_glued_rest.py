"""Ticket G8: a value of kind IPV4, PHONE, IBAN, UUID or CREDITCARD glued to a letter, a digit or `_` is masked in the first call, the
glued character left outside the placeholder; the shapes G8 does not take are pinned as stated limits (strict xfail, so a
later fix shows up). Data and the leak rule: tests/g8_cases.py. Public names only, except `_has_bank_word` (one test)."""

from __future__ import annotations

import importlib
import time

import pytest

from hadavin_sdk.guard import runmap
from hadavin_sdk.guard.redact import redact, redact_many
from tests import g8_cases as G

R = importlib.import_module("hadavin_sdk.guard.redact")


def _rows(*classes: str) -> list:
    return [pytest.param(c, id=f"row{c['id']}") for c in G.CASES if c["cls"] in classes]


def _ids(*ids: int) -> list:
    return [pytest.param(G.BY_ID[i], id=f"row{i}") for i in ids]


GLUED_OUTSIDE = (2, 3, 4, 5, 7, 8, 9, 18, 19, 20, 36, 37, 47, 48, 49, 50, 51, 81, 82, 83, 84)
LIMITS = {
    10: "L1",
    13: "L2",
    25: "L3",
    27: "L3",
    38: "L4",
    39: "L4",
    40: "L4",
    45: "L4",
    76: "L5",
    87: "L4",
    88: "L4",
    89: "L4",  # v5: rows 89-92 (G8-review-4-design M1)
    90: "L4",
    91: "L4",
    92: "L4",
    93: "L4",  # v6: rows 93-96 (G8-review-5-design N2)
    94: "L4",
    95: "L4",
    96: "L4",
    97: "L14",  # v6: rows 97-99 (design M2)
    98: "L14",
    99: "L14",
    100: "L3",  # v6: rows 100, 101 (design N4)
    101: "L3",
    85: "L10",
    86: "L10",
}
LIMITS.update({i: "L6" for i in (67, 68, 69, 70, 78, 79, 80)})
OPAQUE = ("K75", "K76", "K77", "K83", "K84")


@pytest.mark.parametrize("c", _rows("closed", "changed"))
def test_glued_rows_are_masked(c):
    t = c["text"]
    many = redact_many([t, "other line"])[0][0]
    for where, out in (
        ("redact", redact(t).text),
        ("redact_many", many),
        ("redact_text", runmap.redact_text(t, runmap.RunMap())),
    ):
        assert out == c["expected"], f"ROW {c['id']} {where}: {out!r}"
        assert not G.leak(c["kind"], c["value"], out), f"ROW {c['id']} {where} leaks: {out!r}"


@pytest.mark.parametrize("c", _ids(*GLUED_OUTSIDE))
def test_glued_character_stays_outside_the_placeholder(c):
    r = redact(c["text"])
    ph = next(
        p for p, o in r.mapping.items() if o == c["value"]
    )  # StopIteration (red) when the value is not masked whole
    i = c["text"].index(c["value"])
    before, after = c["text"][:i], c["text"][i + len(c["value"]) :]
    assert r.text == before + ph + after, f"ROW {c['id']} glued: {r.text!r}"


@pytest.mark.parametrize("c", _rows("unchanged"))
def test_controls_and_untouched_rows_keep_their_output(c):
    out = redact(c["text"]).text
    assert out == c["expected"], f"ROW {c['id']} unchanged: {out!r}"
    if not (G.G4C_MERGED and c["kind"] == "host"):
        assert out == c["now"], f"ROW {c['id']} differs from the base: {out!r}"


@pytest.mark.parametrize(
    "c",
    [
        pytest.param(
            G.BY_ID[i],
            id=f"row{i}",
            marks=pytest.mark.xfail(strict=True, reason=f"stated limit {lim} (ticket G8)"),
        )
        for i, lim in sorted(LIMITS.items())
    ],
)
def test_limit_rows_are_pinned(c):
    """Asserts the DESIRED behaviour; strict xfail, so the day a limit is fixed the suite turns red and the row is moved."""
    out = redact(c["text"]).text
    assert not G.leak(c["kind"], c["value"], out), f"ROW {c['id']} limit: {out!r}"


@pytest.mark.parametrize(
    "c",
    [
        pytest.param(
            G.BY_ID[i],
            id=f"row{i}",
            marks=[]
            if G.G4C_MERGED
            else [pytest.mark.xfail(strict=True, reason="closed by G4c (ticket G4), not by G8")],
        )
        for i in (64, 71)
    ],
)
def test_host_glued_before_is_closed_by_g4c(c):
    out = redact(c["text"]).text
    assert out == "x <HOSTNAME_1> y", f"ROW {c['id']} g4c: {out!r}"


@pytest.mark.parametrize("k", [pytest.param(k, id=k["id"]) for k in G.KEEP])
def test_must_keep_rows(k):
    out = redact(k["text"])
    assert out.text == k["after"], f"ROW {k['id']} keep ({k['verdict']}): {out.text!r}"
    if k["after"] == k["text"]:
        assert out.mapping == {}, f"ROW {k['id']} keep: map {out.mapping!r}"


@pytest.mark.parametrize("fid,text,now,after", [pytest.param(*f, id=f[0]) for f in G.FULL_STOP])
def test_phone_before_a_full_stop_is_a_stated_limit(fid, text, now, after):
    """L7, found on the way (not glued): PHONE's end guard refuses `.`, so a number before a full stop is not masked
    (F1-F3, unchanged by G8) or only in part (F4: the last group stays readable, as on the base). Pinned as it is."""
    out = redact(text).text
    assert out == (after or text), f"ROW {fid} full stop: {out!r}"


@pytest.mark.parametrize("k", [pytest.param(k, id=k["id"]) for k in G.KEEP if k["id"] in OPAQUE])
def test_an_iban_never_starts_inside_an_opaque_token(k):
    """G8-review-2 F1 (L-D2): an IBAN-shaped tail inside a long letter-and-digit token is not an IBAN; the token is masked
    whole as before and the map holds one entry (a camelCase start split it and left up to 39 characters readable)."""
    out = redact(k["text"])
    assert out.text == k["after"] and len(out.mapping) == 1, (
        f"OPAQUE {k['id']}: {out.text!r} {sorted(out.mapping)!r}"
    )


@pytest.mark.parametrize("aid,text,now,after", [pytest.param(*a, id=a[0]) for a in G.AT_REST])
def test_at_rest_rows(aid, text, now, after):
    """G8-review-2 F6: what `redact()` writes to the map and what `runmap.storable` keeps of it. AT1-AT3 pin limit L11 (a
    piece of a secret with a stored kind's shape is stored), AT5 and AT6 the IBAN start's effect on stored originals,
    AT8 and AT9 a contiguous card number stored as PHONE (v6)."""
    r = redact(text)
    got = (r.text, sorted(r.mapping.items()), sorted(runmap.storable(dict(r.mapping)).items()))
    assert got == (after or now), f"AT {aid}: {got!r}"


@pytest.mark.parametrize("c", _rows("closed", "changed", "unchanged", "limit", "g4c"))
def test_second_call_changes_nothing(c):
    m = runmap.RunMap()
    once = runmap.redact_text(c["text"], m)
    snap = dict(m)
    assert runmap.redact_text(once, m) == once and dict(m) == snap, f"ROW {c['id']} second call"


@pytest.mark.parametrize("c", _rows("closed", "changed", "unchanged", "limit", "g4c"))
def test_untrusted_matches_redact_text(c):
    assert runmap.redact_untrusted(c["text"], runmap.RunMap()) == runmap.redact_text(
        c["text"], runmap.RunMap()
    )


@pytest.mark.parametrize("uid,call,text,want", [pytest.param(*u, id=u[0]) for u in G.UNTRUSTED])
def test_untrusted_placeholder_literal_keeps_its_number(uid, call, text, want):
    """G8-review-3-codebase M2: `redact_untrusted` escapes `<TENANT_4155550132>` to `\u2039TENANT_4155550132\u203a`
    before the patterns run; the number in the escaped literal is not a phone number (PHONE entry 7 refuses `\u203a`
    after, as it refuses `>`), so nothing is masked and the map stays empty."""
    m = runmap.RunMap()
    out = getattr(runmap, call)(text, m)
    assert out == want and dict(m) == {}, f"UNTRUSTED {uid}: {out!r} {dict(m)!r}"


@pytest.mark.parametrize(
    "c",
    [
        pytest.param(c, id=f"row{c['id']}")
        for c in G.CASES
        if c["kind"] in ("ipv4", "phone") and "UUID" not in c["after"]
    ],
)
def test_restore_round_trip_ipv4_and_phone(c):
    m = runmap.RunMap()
    out = runmap.redact_text(c["text"], m)
    assert runmap.restore_text(out, m) == c["text"], f"ROW {c['id']} restore"


def test_sweep_masks_a_letter_glued_copy_of_a_known_phone_only():
    """G8b: a copy of a known PHONE value is replaced when a letter or `_` touches it, not when a digit does; every
    other kind keeps the old rule (no ASCII letter or digit beside the copy)."""
    p = G.P10
    out = redact(f"phone={p} then x{p} now").text  # row 31
    assert out == "phone=<PHONE_1> then x<PHONE_1> now", f"SWEEP phone letter: {out!r}"
    out = redact(f"a x{p} and a{p}0b", mapping={"<PHONE_1>": p}).text
    assert out == f"a x<PHONE_1> and a{p}0b", (
        f"SWEEP phone digit: {out!r}"
    )  # a digit beside it: another number
    ip = G.V["IP1"]
    out = redact(f"known {ip} and v{ip}").text
    assert out == f"known <IPV4_1> and v{ip}", (
        f"SWEEP ipv4: {out!r}"
    )  # IPV4 is not in _JOINS (L-D1)
    out = redact("on printer7 and xprinter7", mapping={"<HOSTNAME_1>": "printer7"}).text
    assert out == "on <HOSTNAME_1> and xprinter7", f"SWEEP host: {out!r}"
    out = redact("t acme42 and acme42x", mapping={"<TENANT_1>": "acme42"}).text
    assert out == "t <TENANT_1> and acme42x", f"SWEEP tenant: {out!r}"


def test_gate_enforce_map_rewrites_a_letter_glued_copy_of_a_known_phone():
    """The gate's own sweep (`runmap.enforce_map`, the model-visible text) inherits G8b: the very shape the PHONE hash guard
    keeps in pass 1 (`build4155550132`) is rewritten once the number is a known value of the run."""
    m = {"<PHONE_1>": G.P10}
    for text, want in (
        ("build" + G.P10, "build<PHONE_1>"),
        ("x" + G.P10 + "_", "x<PHONE_1>_"),
        ("7" + G.P10, "7" + G.P10),
    ):
        out = runmap.enforce_map(text, m)
        assert out == want, f"GATE phone: {out!r}"
    out = runmap.enforce_map("t acme42x", {"<TENANT_1>": "acme42"})
    assert out == "t acme42x", f"GATE tenant: {out!r}"


def test_bank_word_check_ignores_a_glued_uuid():
    glued = "id x" + G.J(["123e4567-", "e89b-12d3-", "a456-", "aba123456789"])
    assert R._has_bank_word(glued) is False, (
        "BANK glued uuid"
    )  # True before G8: the UUID's tail read as an ABA number


def test_g9_read_back_follows_the_sweeps_joins():
    """Tripwire (ticket G8 v5, section 8.1): once G9 is in the tree (`_Redactor._overlaps`), its read-back must judge a
    copy of a known PHONE value by `_joins`, as the literal sweep does: `x` + the read-back `4155550132` is a copy (masked),
    `7` + it is not. Without G9 nothing is read back and both texts stay as written."""
    m = {"<TENANT_1>": G.P10[:8], "<PHONE_1>": G.P10}
    g9 = hasattr(R._Redactor, "_overlaps")
    out = redact("x<TENANT_1>32 y", mapping=dict(m))
    want = "x<PHONE_1> y" if g9 else "x<TENANT_1>32 y"
    assert out.text == want and dict(out.mapping) == m, (
        f"G9 read-back letter: {out.text!r} {dict(out.mapping)!r}"
    )
    out = redact("7<TENANT_1>32 y", mapping=dict(m))
    assert out.text == "7<TENANT_1>32 y", f"G9 read-back digit: {out.text!r}"


def test_row_counts_are_pinned():
    from collections import Counter

    assert (
        len(G.CASES) == 101
        and len(G.KEEP) == 84
        and len(G.FULL_STOP) == 4
        and len(G.AT_REST) == 9
        and len(G.UNTRUSTED) == 2
    )
    assert Counter(c["cls"] for c in G.CASES) == {
        "closed": 48,
        "unchanged": 15,
        "limit": 33,
        "changed": 3,
        "g4c": 2,
    }
    assert sorted(LIMITS) == sorted(c["id"] for c in G.CASES if c["cls"] == "limit")


HOSTILE = {
    "dots": "1.",
    "digits and spaces": "x1 2 3 4 5 6 7 8 9 ",
    "underscore digits": "_4155550132",
    "hex and dashes": "deadbeef-dead-beef-dead-",
    "iban-ish": "aDE89" + "A" * 40 + " ",
    "plus digits": "a+1 415-555-0132",
    "iban underscore": "ab_DE89" + "A" * 20 + "_x ",
}


CALLS = {
    "redact": lambda t: redact(t),
    "redact_text": lambda t: runmap.redact_text(t, runmap.RunMap()),
}


@pytest.mark.perf
@pytest.mark.parametrize("call", sorted(CALLS))
@pytest.mark.parametrize("name", sorted(HOSTILE))
def test_glued_patterns_are_linear(name, call):
    """CPU seconds (`time.thread_time`, best of 3) for 65,536 and 262,144 characters, through `redact()` and through
    `runmap.redact_text`: the ratio is at most 6.0 (4x the text) and the large text takes under 3.0 s. The base-vs-G8
    comparison is tests/g8_cost.py (ticket G8 v5 section 10), not this test."""

    def best(n: int) -> float:
        text = (HOSTILE[name] * (n // len(HOSTILE[name]) + 1))[:n]
        out = []
        for _ in range(3):
            t0 = time.thread_time()
            CALLS[call](text)
            out.append(time.thread_time() - t0)
        return min(out)

    small, large = best(65_536), best(262_144)
    assert large < 3.0, f"{name} {call}: {large:.2f} s"
    assert large / max(small, 1e-3) <= 6.0, f"{name} {call}: ratio {large / max(small, 1e-3):.2f}"
