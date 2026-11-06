"""Every active row of the hostile corpus: the rendered line obeys the grammar and carries no canary."""

from __future__ import annotations

import contextlib
import re
import time

import pytest

from hadavin_sdk.codes import Where
from hadavin_sdk.guard.diagnostic import diagnose, render, validation_text
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
    started = time.monotonic()
    out = _line(row)
    elapsed = time.monotonic() - started
    assert grammar_ok(out, "V" if row.kind == "validation" else "A"), out
    assert not leaks(out, row.canaries), out
    if row.expect == "golden":
        assert re.fullmatch(str(row.spec["golden"]), out), out
    if row.expect_code is not None:
        assert f"code={row.expect_code.value} " in out, out
    if row.expect == "bounded":
        assert len(out) <= 400
        assert elapsed < 5


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
    from tests.test_diagnostics_old_writers import OLD_WRITER_CRASHES, OLD_WRITER_LEAKS

    ids = {r.id for r in corpus.ROWS}
    assert set(OLD_WRITER_LEAKS) | set(OLD_WRITER_CRASHES) <= ids
    assert not set(OLD_WRITER_LEAKS) & set(OLD_WRITER_CRASHES)
    wiring = [r for r in corpus.ROWS if r.cls == "writer_wiring"]
    assert wiring and all(r.status == "later" for r in wiring)


def test_canaries_are_long_enough() -> None:
    for r in corpus.ROWS:
        for c in r.canaries:
            assert len(c) >= 8, (r.id, c)


def test_every_active_row_has_teeth() -> None:
    """Each row with canaries leaks through a deliberately leaky subject: the oracle can see the canary."""
    exempt = [
        r for r in ACTIVE if r.expect in ("bounded", "propagates", "golden") or not r.canaries
    ]
    assert len(exempt) <= 40
    for r in ACTIVE:
        if r.kind != "exception" or r.expect in ("propagates",) or not r.canaries:
            continue
        if r.spec.get("ctx") or r.spec["factory"] in ("meta_module", "meta_name", "meta_eq", "meta_mro", "str_raises", "repr_raises",
                                                      "str_recursion", "getattr_raises", "errno_keyboard_interrupt", "chain"):  # fmt: skip
            continue
        leaky = None
        try:
            e = corpus.build_exception(r.spec)
            leaky = f"{type(e).__name__}: {e} {getattr(e, 'doc', '')} {getattr(e, 'msg', '')}"
        except Exception:  # noqa: BLE001
            leaky = None
        if leaky is None:
            continue
        if (
            r.canaries
            and r.expect == "no_canary"
            and r.spec["factory"] not in ("dynamic", "dynamic_module")
        ):
            assert leaks(leaky, r.canaries), (
                f"{r.id}: the oracle cannot see the canary in {leaky[:80]!r}"
            )


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
