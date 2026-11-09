"""P1d-a rows and properties (ticket revision 5). One test per row and entry: ``test_row_<id>_<entry>``; every assertion
message starts ``ROW <id> <entry>:`` (the mutant runner's ``expect``). Made-up data only."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path

from markdown_it import MarkdownIt

from hadavin_sdk.approvals import channel, gate
from hadavin_sdk.guard import runmap
from tests.fixtures import p1d_cases as C

FIX = Path(__file__).resolve().parent / "fixtures"


@cache
def _base_rows() -> dict:
    return json.loads((FIX / "p1d_a_base_rows.json").read_text(encoding="utf-8"))["rows"]


@cache
def _gate_base() -> dict:
    return json.loads((FIX / "p1d_a_gate_base.json").read_text(encoding="utf-8"))["frozen"]


def _base_cell(row: C.Row, entry: str) -> str:
    cell = C.cell(row.base, entry)
    return _base_rows()[f"{row.id}/{entry}"] if cell == C.BS0 else cell


def expected_after(row: C.Row, entry: str) -> str | None:
    after = C.cell(row.after, entry)
    if after == C.ASSERTS:
        return None
    if after == C.BS0:
        return _base_rows()[f"{row.id}/{entry}"]
    if after == C.SAME:
        return _base_cell(row, entry)
    return after


def _make(row: C.Row, entry: str):
    def test():
        out, ctx = C.run_entry(row.id, entry, row.input)
        want = expected_after(row, entry)
        if want is not None:
            assert out == want, f"ROW {row.id} {entry}: expected {want!r}, got {out!r}"
        extra = C.check_extra(row.id, entry, out, ctx, after=True)
        assert not extra, f"ROW {row.id} {entry}: {extra} (output {out!r})"

    test.__name__ = f"test_row_{row.id}_{entry}"
    test.__qualname__ = test.__name__
    return test


for _row in C.ROWS:
    for _entry in _row.entries:
        _fn = _make(_row, _entry)
        globals()[_fn.__name__] = _fn
del _row, _entry, _fn


# --- properties --------------------------------------------------------------------------------------------------
def test_defang_text_idempotent():
    for x in C.texts("TXT-A"):
        once = gate.defang_text(x)
        assert gate.defang_text(once) == once, f"NOT IDEMPOTENT: {x!r}"


def test_defang_text_only_rewrites_dots():
    for x in C.texts("TXT-B"):
        assert gate.defang_text(x).replace("[.]", ".") == x, f"DOTS ONLY: {x!r}"


def test_sanitise_text_default_unchanged():
    frozen = _gate_base()
    lit = C.lit_strings()
    assert set(lit) == set(frozen), (
        "DEFAULT CHANGED: the collected literals differ from the frozen set"
    )
    for x in lit:
        a, b = gate.sanitise_text(x), gate.sanitise_text(x, defang=True)
        assert a == b == frozen[x], f"DEFAULT CHANGED: {x!r}: {a!r} / {b!r} / {frozen[x]!r}"


def _line_diff_ok(left: str, right: str) -> bool:
    ll, rl = left.split("\n"), right.split("\n")
    if len(ll) != len(rl):
        return False
    for a, b in zip(ll, rl, strict=True):
        if a == b:
            continue
        if (
            gate.WITHHELD in a
            and gate.WITHHELD not in b
            and b.startswith(a.split(gate.WITHHELD)[0])
        ):
            continue
        return False
    return True


def test_pre_redaction_differential():
    for x in [*C.lit_strings(), *C.texts("TXT-A")]:
        left = gate.defang_text(gate.withhold_commands(gate.sanitise_text(x, defang=False)))
        right = gate.defang_text(gate.withhold_commands(gate.sanitise_text(x)))
        assert _line_diff_ok(left, right), f"DIFFERENTIAL: {x!r}: {left!r} / {right!r}"


def _text_tokens(s: str):
    for tok in MarkdownIt("commonmark").parse(s):
        if tok.type == "inline":
            for ch in tok.children or []:
                if ch.type == "text":
                    yield ch.content


def test_no_link_outside_code_on_card():
    bad = (gate._DOMAIN, gate._NON_ASCII_HOST, gate._PLACEHOLDER_DOT, gate._WIDE_DOTS)
    for x in C.texts("TXT-A"):
        final = channel.clean(x)
        for text in _text_tokens(final):
            for rx in bad:
                assert not rx.search(text), (
                    f"LINK: {x!r} -> {final!r}: {text!r} matches {rx.pattern}"
                )


def test_card_masks_what_model_masks():
    for x in C.texts("EH"):
        mapping = runmap.RunMap()
        runmap.redact_text(x, mapping)
        shown = channel.clean(x).replace("[.]", ".")
        for ph, original in mapping.items():
            m = runmap.PLACEHOLDER.fullmatch(ph)
            if m and m.group(1) in ("EMAIL", "HOSTNAME"):
                assert original not in shown, f"CARD LEAK: {original!r} in {shown!r} for {x!r}"


def test_stored_card_round_trip():
    # G-TXT-B: a typed `[.]` between name characters is read as `.` by design (row L15), so it is not drawn.
    for x in C.texts("TXT-B"):
        stored = channel.clean(x)
        if len(stored) <= 2900:
            assert C.e_slack(stored) == stored, f"ROUND TRIP: {x!r}: {stored!r}"
