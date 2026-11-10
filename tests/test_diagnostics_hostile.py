"""Every active row of the hostile corpus: the rendered line obeys the grammar and carries no canary."""

from __future__ import annotations

import contextlib
import re
import traceback

import pytest

from hadavin_sdk.codes import Where
from hadavin_sdk.guard.diagnostic import diagnose, render, validation_text
from hadavin_sdk.guard.runmap import safe_head
from tests.data import c18a_hostile_corpus as corpus
from tests.data.c18a_oracle import grammar_ok, leaks

ACTIVE = [r for r in corpus.ROWS if r.status == "active"]


def _ctx(row: corpus.Row) -> contextlib.AbstractContextManager[None]:
    name = row.spec.get("ctx")
    return corpus.CONTEXTS[name]() if name else contextlib.nullcontext()  # type: ignore[index]


def _step(row: corpus.Row) -> object:
    name = row.spec["step"]
    return Where(name) if name in Where._value2member_map_ else name


def _line(row: corpus.Row) -> str:
    with _ctx(row):
        if row.kind == "validation":
            return validation_text(corpus.build_validation_error(row.spec))
        exc = corpus.build_exception(row.spec)
        return render(diagnose(exc, step=_step(row)))  # type: ignore[arg-type]


def test_corpus_shape() -> None:
    """Counts come from the data, never from a literal here (a later package appends rows): ids are unique, every row has a known
    status, there are active rows, every class has rows, and the minimum of each class holds."""
    assert len({r.id for r in corpus.ROWS}) == len(corpus.ROWS)
    assert {r.status for r in corpus.ROWS} <= {"active", "later", "not_applicable"}
    assert len(ACTIVE) == sum(r.status == "active" for r in corpus.ROWS) > 0
    assert {r.cls for r in corpus.ROWS} == set(corpus.CLASSES)
    for cls, minimum in corpus.MINIMUMS.items():
        assert sum(r.cls == cls for r in corpus.ROWS) >= minimum, cls


@pytest.mark.parametrize("row", ACTIVE, ids=[r.id for r in ACTIVE])
def test_row(row: corpus.Row) -> None:
    if row.expect == "propagates":
        with pytest.raises(BaseException) as info, _ctx(row):
            diagnose(corpus.build_exception(row.spec), step=_step(row))  # type: ignore[arg-type]
        assert not isinstance(info.value, Exception)
        return
    out = _line(row)
    assert grammar_ok(out, "V" if row.kind == "validation" else "A"), out
    assert not leaks(out, row.canaries), out
    if row.kind == "validation":
        # the same error also goes through ``diagnose`` and ``render`` (a rendered line, Grammar A), not only through ``validation_text``
        with _ctx(row):
            line = render(diagnose(corpus.build_validation_error(row.spec), step=Where.extract))
        assert grammar_ok(line, "A"), line
        assert not leaks(line, row.canaries), line
    if row.expect == "golden":
        assert re.fullmatch(str(row.spec["golden"]), out), out
    if row.expect_code is not None:
        assert f"code={row.expect_code.value} " in out, out
    if row.expect == "bounded":
        assert len(out) <= 400  # an algorithmic bound; no wall clock


# --- meta tests of the corpus and the oracle ----------------------------------------------------------------------------
def test_corpus_file_is_ascii() -> None:
    from pathlib import Path

    for name in ("c18a_hostile_corpus.py", "c18a_oracle.py"):
        raw = (Path(corpus.__file__).parent / name).read_bytes()
        assert all(b < 128 for b in raw), name


def test_every_ledger_id_is_covered() -> None:
    covered = {x for r in corpus.ROWS for x in r.ledger}
    assert covered == set(corpus.LEDGER_IDS), sorted(set(corpus.LEDGER_IDS) ^ covered)


def test_later_rows_are_not_overdue() -> None:
    now = corpus.STEPS.index(corpus.CORPUS_STEP)
    for r in corpus.ROWS:
        if r.status == "later":
            assert corpus.STEPS.index(r.owner_step) > now, r.id


def test_canaries_are_long_enough() -> None:
    """Every canary has at least 8 characters and every key of ``scan_keyset(canary)`` at least 6 (P1's digit-only needle minimum)."""
    from hadavin_sdk.guard.textnorm import scan_keyset

    for r in corpus.ROWS:
        for c in r.canaries:
            assert len(c) >= 8, (r.id, c)
            for key in scan_keyset(c):
                assert len(key) >= 6, (r.id, c, key)


def test_propagates_rows_are_exactly_the_frozen_set() -> None:
    assert {r.id for r in corpus.ROWS if r.expect == "propagates"} == set(corpus.PROPAGATES_ROWS)
    assert len(corpus.PROPAGATES_ROWS) == 1, "the frozen set has one member (BN-3)"


# --- the teeth of the corpus: the oracle must be able to see a canary in a deliberately leaky output ----------------------------
# What a hostile attribute or ``__str__`` of the corpus raises when a leaky reading touches it (RecursionError is a RuntimeError). An
# error of another class is not swallowed: the test fails and says which.
_HOSTILE_READ_ERRORS = (AttributeError, IndexError, KeyError, RuntimeError, TypeError, ValueError)
ONE_RUN = [r for r in ACTIVE if r.kind in ("exception", "validation") and r.expect != "propagates"]
EXEMPT = [
    r for r in ONE_RUN if r.expect in ("bounded", "grammar")
]  # by the field, never by text in ``why``
EXEMPT_CAP = 15  # author choice (P5a rev 3), UNVERIFIED as the right cap


def _teeth_subjects(row: corpus.Row, e: BaseException) -> list[str]:
    """The ten leaky readings of an exception (and two more for a validation row). A reading that raises gives an empty text."""
    readings = [
        lambda: f"{type(e).__name__}: {e}",
        lambda: repr(e),
        lambda: safe_head(str(e), 300),
        lambda: e.args[0],
        lambda: "".join(getattr(e, "__notes__", ())),
        lambda: getattr(e, "filename", ""),
        lambda: getattr(e, "doc", ""),
        lambda: getattr(e, "msg", ""),
        lambda: repr(e.args),
        lambda: "".join(traceback.format_exception(e)),
    ]
    if row.kind == "validation":
        readings += [lambda: f"{e}", lambda: str(e.errors())]  # type: ignore[attr-defined]
    out = []
    for read in readings:
        try:
            value = read()
        except (
            _HOSTILE_READ_ERRORS
        ):  # a subject that raises gives "" (BN-3); no helper catches BaseException
            value = ""
        out.append(value if type(value) is str else "")
    return out


def _built(row: corpus.Row) -> BaseException:
    return (
        corpus.build_validation_error(row.spec)
        if row.kind == "validation"
        else corpus.build_exception(row.spec)
    )


def test_every_active_row_has_teeth() -> None:
    """Each active row of kind exception or validation (a row that expects a propagating ``BaseException`` excepted) makes ``leaks()``
    alone True through at least one leaky reading, unless the row is exempt by its ``expect`` field. The exempt ids are printed."""
    print("exempt from the teeth test:", [r.id for r in EXEMPT])
    assert len(EXEMPT) <= EXEMPT_CAP, f"{len(EXEMPT)} rows are exempt; the cap is {EXEMPT_CAP}"
    blind = []
    for r in ONE_RUN:
        if r in EXEMPT:
            continue
        with _ctx(r):
            subjects = _teeth_subjects(r, _built(r))
        if not any(leaks(text, r.canaries) for text in subjects):
            blind.append(r.id)
    assert not blind, (
        f"the oracle cannot see the canary of these rows in any leaky reading: {blind}"
    )


def test_reverse_check_fails_90_percent() -> None:
    """A HARD GATE. A deliberately leaky ``diagnose`` (``f"{type(exc).__name__}: {exc}"``) must make ``leaks()`` True for at least 90 percent
    of the rows that are not exempt. The numerator and the denominator come from the same set, so the denominator is exact."""
    rows = [r for r in ONE_RUN if r not in EXEMPT]
    assert rows, "the set is empty: the gate would pass for nothing"
    caught = []
    for r in rows:
        with _ctx(r):
            e = _built(r)
            try:
                out = f"{type(e).__name__}: {e}"
            except (
                _HOSTILE_READ_ERRORS
            ):  # a hostile ``__str__`` raising: that leaky function produced no output for this row
                out = ""
        if leaks(out, r.canaries):
            caught.append(r.id)
    share = 100 * len(caught) / len(rows)
    print(f"reverse check: {len(caught)} of {len(rows)} rows caught ({share:.1f} percent)")
    missed = sorted({r.id for r in rows} - set(caught))
    assert len(caught) * 10 >= len(rows) * 9, f"{len(caught)} of {len(rows)}; not caught: {missed}"


def test_locator_rows_leave_no_trace() -> None:
    """BN-12: the rows that run code in a real own module's namespace define only ``_p5a_probe_`` names and delete them, and restore the
    temporary ``__name__`` swap: ``vars(hadavin_sdk.stats)`` is equal before and after."""
    from hadavin_sdk import stats

    before = dict(vars(stats))
    ran = 0
    for r in corpus.ROWS:
        if r.cls == "locator_frames" and r.status == "active" and r.kind == "exception":
            with _ctx(r):
                render(diagnose(corpus.build_exception(r.spec), step=Where.other))
            ran += 1
    assert ran > 0
    after = dict(vars(stats))
    assert set(before) == set(after), sorted(set(before) ^ set(after))
    assert before == after


def test_strict_oracle_is_a_superset() -> None:
    from tests.data.c18a_oracle import leaks_literal

    for r in ACTIVE:
        for c in r.canaries:
            for text in (c, "x " + c + " y"):
                if leaks_literal(text, (c,)):
                    assert leaks(text, (c,))


def test_oracle_and_grammar_are_independent() -> None:
    assert not grammar_ok("ValueError: diag_v=1 code=x step=y at=- fp=zzzzzzzz")
    assert not leaks(
        "ValueError: diag_v=1 code=foreign_exception step=extract at=- fp=00000000", (corpus.NAME,)
    )
    assert leaks("x " + corpus.NAME + " y", (corpus.NAME,))
