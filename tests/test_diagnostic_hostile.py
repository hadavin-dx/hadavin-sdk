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
    ledger = {x for r in corpus.ROWS for x in r.ledger}
    assert ledger >= set(corpus.LEDGER_IDS) - {"BL-core-c18a-%03d" % n for n in ()}, set(corpus.LEDGER_IDS) - ledger


@pytest.mark.parametrize("row", ACTIVE, ids=[r.id for r in ACTIVE])
def test_row(row: corpus.Row) -> None:
    if row.expect == "propagates":
        with pytest.raises(BaseException) as info, _ctx(row):  # noqa: PT012
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
