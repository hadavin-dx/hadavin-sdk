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
    assert len(corpus.ROWS) == 161
    assert len({r.id for r in corpus.ROWS}) == 161
    assert sum(r.status == "active" for r in corpus.ROWS) == 135
    assert sum(r.status == "later" for r in corpus.ROWS) == 24
    assert sum(r.status == "not_applicable" for r in corpus.ROWS) == 2
    assert {r.cls for r in corpus.ROWS} == set(corpus.CLASSES)


def test_class_minimums() -> None:
    assert set(corpus.MINIMUMS) == set(corpus.CLASSES)
    for cls, minimum in corpus.MINIMUMS.items():
        assert sum(r.cls == cls for r in corpus.ROWS) >= minimum, cls
    assert sum(corpus.MINIMUMS.values()) <= len(corpus.ROWS)


@pytest.mark.parametrize("row", ACTIVE, ids=[r.id for r in ACTIVE])
def test_active_rows_hold_on_new_code(row: corpus.Row) -> None:
    if row.expect == "propagates":
        with pytest.raises(BaseException) as info, _ctx(row):
            diagnose(corpus.build_exception(row.spec), step=_step(row))  # type: ignore[arg-type]
        assert not isinstance(info.value, Exception)
        return
    out = _line(row)
    assert grammar_ok(out, "V" if row.kind == "validation" else "A"), out
    assert not leaks(out, row.canaries), out
    if (
        row.kind == "validation"
    ):  # the same error through the line writer, the way a caller prints it
        with _ctx(row):
            line = render(diagnose(corpus.build_validation_error(row.spec), step=Where.config_load))
        assert grammar_ok(line, "A") and not leaks(line, row.canaries), line
    if row.expect == "golden":
        assert re.fullmatch(str(row.spec["golden"]), out), out
    if row.expect_code is not None:
        assert f"code={row.expect_code.value} " in out, out
    if row.expect == "bounded":
        assert (
            len(out) <= 400
        )  # a size bound only: no clock is read (the bounds are algorithmic, see test_links_*)


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


def test_old_writer_marks_follow_their_later_row() -> None:
    from tests.data.c18a_old_writer_marks import OLD_WRITER_CRASHES, OLD_WRITER_LEAKS

    ids = {r.id for r in corpus.ROWS}
    assert set(OLD_WRITER_LEAKS) | set(OLD_WRITER_CRASHES) <= ids
    assert not set(OLD_WRITER_LEAKS) & set(OLD_WRITER_CRASHES)
    wiring = [r for r in corpus.ROWS if r.cls == "writer_wiring"]
    assert wiring and all(r.status == "later" for r in wiring)


def test_canaries_are_long_enough() -> None:
    """Every canary has at least 8 characters and every key of ``scan_keyset(canary)`` at least 6 (P1's digit-only needle minimum)."""
    from hadavin_sdk.guard.textnorm import scan_keyset

    for r in corpus.ROWS:
        for c in r.canaries:
            assert len(c) >= 8, (r.id, c)
            keys = scan_keyset(c)
            assert keys, (r.id, "a canary with no key can never be found")
            assert all(len(k) >= 6 for k in keys), (r.id, sorted(keys))


TEETH_EXEMPT_CAP = 15
BASE_ROWS = [
    r for r in ACTIVE if r.expect != "propagates" and r.kind in ("exception", "validation")
]
EXEMPT = [r for r in BASE_ROWS if r.expect in ("bounded", "grammar")]
TEETH_ROWS = [r for r in BASE_ROWS if r not in EXEMPT]


def _text(make: object) -> str:
    """One leaky subject, evaluated inside ``try/except Exception`` (BN-3): a subject that raises gives ``""``. Never ``BaseException``."""
    with contextlib.suppress(Exception):
        value = make()  # type: ignore[operator]
        return value if type(value) is str else str(value)
    return ""


def _leaky_subjects(e: BaseException, kind: str) -> list[str]:
    """The ten leaky subjects of the ticket (plus two for a validation error): each one is how today's writers print an exception."""
    subjects = [
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
    if kind == "validation":
        subjects += [lambda: f"{e}", lambda: str(e.errors())]  # type: ignore[attr-defined]
    return [_text(m) for m in subjects]


def _leaky_outputs(row: corpus.Row) -> list[str]:
    with _ctx(row):
        e = (
            corpus.build_validation_error(row.spec)
            if row.kind == "validation"
            else corpus.build_exception(row.spec)
        )
        return _leaky_subjects(e, row.kind)


def test_exempt_rows_are_chosen_by_the_field_and_capped() -> None:
    """The exemption is decided by ``Row.expect`` only (BN-3), the cap of 15 counts only ``bounded`` and ``grammar`` rows, and the ids are
    printed so a reviewer can see who is exempt."""
    print("teeth-exempt ids:", [r.id for r in EXEMPT])
    assert {r.expect for r in EXEMPT} <= {"bounded", "grammar"}
    assert len(EXEMPT) <= TEETH_EXEMPT_CAP, (
        f"{len(EXEMPT)} rows are exempt from the teeth test, the cap is {TEETH_EXEMPT_CAP}"
    )
    assert not any(r.expect == "propagates" for r in TEETH_ROWS)
    assert tuple(r.id for r in ACTIVE if r.expect == "propagates") == corpus.PROPAGATES_ROWS


@pytest.mark.parametrize("row", TEETH_ROWS, ids=[r.id for r in TEETH_ROWS])
def test_every_active_row_has_teeth(row: corpus.Row) -> None:
    """On every active exception or validation row that is not exempt, at least one of the leaky subjects makes ``leaks()`` alone True
    (``grammar_ok`` is not asked): the oracle can see the canary, so a clean result on the new code means something."""
    assert row.canaries, f"{row.id} is not exempt and has no canary"
    outputs = _leaky_outputs(row)
    assert any(leaks(o, row.canaries) for o in outputs), (
        f"{row.id}: none of {len(outputs)} leaky subjects makes the oracle see a canary"
    )


def _leaky_diagnose(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {exc}"


def test_reverse_check_fails_90_percent() -> None:
    """Hard gate (Appendix B): a deliberately leaky ``diagnose`` must make ``leaks()`` True for at least 90 percent of the same rows the
    teeth test runs on (the denominator is exact). The measured count is printed."""
    hit = 0
    missed: list[str] = []
    for row in TEETH_ROWS:
        with _ctx(row):
            e = (
                corpus.build_validation_error(row.spec)
                if row.kind == "validation"
                else corpus.build_exception(row.spec)
            )
            out = _text(lambda e=e: _leaky_diagnose(e))
        if leaks(out, row.canaries):
            hit += 1
        else:
            missed.append(row.id)
    print(f"reverse check: {hit} of {len(TEETH_ROWS)} rows leak; missed: {missed}")
    assert TEETH_ROWS and hit * 10 >= len(TEETH_ROWS) * 9, (hit, len(TEETH_ROWS), missed)


def test_reverse_check_with_a_clean_diagnose_hits_nothing() -> None:
    """The counter is not trivially high: the real ``render(diagnose())`` line hits (almost) no row."""
    hit = 0
    for row in TEETH_ROWS:
        if row.kind != "exception":
            continue
        with _ctx(row):
            out = render(diagnose(corpus.build_exception(row.spec), step=_step(row)))  # type: ignore[arg-type]
        hit += leaks(out, row.canaries)
    assert hit == 0, hit


def test_strict_oracle_is_a_superset() -> None:
    """On every active row and every leaky subject, ``leaks_literal`` True implies ``leaks`` True: a P1b change that weakens
    ``scan_keyset`` fails here instead of silently passing rows. Rows with ``expect="propagates"`` are excluded by the field."""
    from tests.data.c18a_oracle import leaks_literal

    checked = 0
    for r in ACTIVE:
        if r.expect == "propagates" or r.kind not in ("exception", "validation"):
            continue
        outputs = [*_leaky_outputs(r), *(f"x {c} y" for c in r.canaries), *r.canaries]
        for out in outputs:
            if leaks_literal(out, r.canaries):
                checked += 1
                assert leaks(out, r.canaries), (
                    f"{r.id}: the literal bound sees a canary, the oracle does not"
                )
    assert checked > 100, checked


def test_oracle_and_grammar_are_independent() -> None:
    assert not grammar_ok("ValueError: diag_v=1 code=x step=y at=- fp=zzzzzzzz")
    assert not leaks(
        "ValueError: diag_v=1 code=foreign_exception step=extract at=- fp=00000000", (corpus.NAME,)
    )
    assert leaks("x " + corpus.NAME + " y", (corpus.NAME,))


# --- more meta tests of the corpus (BN-3, BN-12, BN-15) --------------------------------------------------------------------
def test_status_and_owner_step_values_are_valid() -> None:
    for r in corpus.ROWS:
        assert r.status in ("active", "later", "not_applicable"), r.id
        assert r.owner_step in corpus.STEPS, r.id
        assert r.kind in ("exception", "validation", "source", "scenario"), r.id
        assert r.expect in ("no_canary", "grammar", "bounded", "golden", "propagates"), r.id
        assert r.cls in corpus.CLASSES, r.id


def test_a_not_applicable_or_later_row_has_a_reason_of_at_least_20_characters() -> None:
    for r in corpus.ROWS:
        if r.status in ("later", "not_applicable"):
            assert len(r.reason) >= 20, (r.id, r.reason)
        else:
            assert r.reason == "", (r.id, "an active row has no reason")


def test_no_two_rows_share_the_same_input_unless_marked_as_a_variant() -> None:
    seen: dict[object, str] = {}
    for r in corpus.ROWS:
        if r.status != "active":
            continue
        key = (
            (r.spec["factory"], repr(r.spec["args"]))
            if r.kind == "exception"
            else (r.spec["model"], r.spec["document"])
        )
        if key in seen:
            assert f"variant_of={seen[key]}" in r.why, (
                f"{r.id} repeats {seen[key]} without variant_of"
            )
        else:
            seen[key] = r.id


def test_every_ledger_id_has_exactly_one_base_row() -> None:
    for ledger_id in corpus.LEDGER_IDS:
        holders = [r.id for r in corpus.ROWS if ledger_id in r.ledger]
        assert len(holders) == 1, (ledger_id, holders)
    assert all(set(r.ledger) <= set(corpus.LEDGER_IDS) for r in corpus.ROWS)


def test_the_propagates_rows_are_the_frozen_tuple() -> None:
    """The set of rows with ``expect="propagates"`` is exactly this literal (``PROPAGATES_ROWS`` is computed from the rows, so it cannot
    be the check)."""
    assert corpus.PROPAGATES_ROWS == ("HC-hostile_class-16",)
    assert tuple(r.id for r in corpus.ROWS if r.expect == "propagates") == corpus.PROPAGATES_ROWS


def test_locator_rows_leave_no_trace() -> None:
    """The rows that run code in a real own module's namespace (``hadavin_sdk.stats``) restore it: the set of its names is equal before
    and after, and so is its ``__name__`` (BN-12)."""
    import hadavin_sdk.stats as stats_module

    before = (set(vars(stats_module)), stats_module.__name__)
    rows = [r for r in ACTIVE if r.cls == "locator_frames" or r.spec.get("ctx")]
    assert len(rows) >= 10
    for r in rows:
        _line(r)
    assert (set(vars(stats_module)), stats_module.__name__) == before
    assert not [n for n in vars(stats_module) if n.startswith("_p5a_probe_")]
