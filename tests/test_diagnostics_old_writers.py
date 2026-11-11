"""The FAIL-BEFORE run: the hostile rows through today's writers (``run_tick`` and ``extract.extract``).

Nothing here tests the new code. It records, per row, whether today's writers leak the row's canaries (``leaked``), crash on the row
(``crashed``) or are clean. Rows that leak or crash are strict xfails that name the later row of the package that wires the writers
(R3c, P5b3), which turns each into a plain assert. The results on the P5a head equal the results on the branch base: P5a changes no writer.
"""

from __future__ import annotations

import contextlib
import logging

import pytest

from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.app import build
from hadavin_sdk.approvals import FakeChannel
from hadavin_sdk.extract import DeadLetter, extract
from hadavin_sdk.models import Reply
from hadavin_sdk.runtime.tick import TickStep, run_tick
from tests.conftest import qualify
from tests.data import c18a_hostile_corpus as corpus
from tests.data.c18a_old_writer_marks import OLD_WRITER_CRASHES, OLD_WRITER_LEAKS
from tests.data.c18a_oracle import leaks

SIG = "sig" + "-p5a-test"  # built from parts


class AdapterError(RuntimeError):
    """The writer did not run, so no verdict may be drawn."""


NO_OLD_WRITER_PATH: frozenset[str] = frozenset()

ROWS = [
    r for r in corpus.ROWS
    if r.status == "active" and r.expect != "propagates" and r.kind in ("exception", "validation")
]  # fmt: skip


@pytest.fixture
def app(live_cfg_dir, fake_system):
    from hadavin_sdk.config import load_config
    from hadavin_sdk.registry import load_registry

    qualify(load_registry(load_config(live_cfg_dir)))
    return build(
        live_cfg_dir,
        ["test-agent"],
        secrets=FakeSecretProvider({"fixture-token": fake_system.token}),
        channel=FakeChannel(SIG),
        timeout_s=0.5,
    )


class _Llm:
    def __init__(self, text: str) -> None:
        self.text = text

    def chat(self, messages, **kw):
        return Reply(text=self.text, model_id="x")


def _ctx(row: corpus.Row) -> contextlib.AbstractContextManager[None]:
    name = row.spec.get("ctx")
    return corpus.CONTEXTS[name]() if name else contextlib.nullcontext()  # type: ignore[index]


def outcome(row: corpus.Row, app, caplog) -> tuple[str, str]:
    """(``crashed`` | ``leaked`` | ``clean`` | ``no_path``, the escaping exception type name or empty)."""
    if row.kind == "validation":
        model = corpus.MODELS[row.spec["model"]]  # type: ignore[index]
        result = extract(_Llm(row.spec["document"]), b"doc", model, run_id="r", route="x")  # type: ignore[arg-type]
        if not isinstance(result, DeadLetter):
            return "no_path", ""
        return ("leaked" if leaks(" | ".join(result.errors), row.canaries) else "clean"), ""
    with _ctx(row):
        built = corpus.build_exception(row.spec)

        def fn(_ctx_: object) -> None:
            raise built

        caplog.clear()
        with caplog.at_level(logging.DEBUG):
            try:
                run_tick(app, steps=[TickStep("x", 0, fn)])
            except (SystemExit, RuntimeError, AttributeError) as e:
                return "crashed", type(e).__name__
        state = app.store.get_tick_state("x")
        records = [r.getMessage() for r in caplog.records if "step=x" in r.getMessage()]
        if (
            state is None
            or type(state.last_error) is not str
            or not state.last_error
            or not records
        ):
            raise AdapterError(f"the writer did not run for {row.id}")
        text = state.last_error + " | " + " | ".join(records)
    return ("leaked" if leaks(text, row.canaries) else "clean"), ""


def check_crash_type(row_id: str, got: str, crash_type: str) -> None:
    """The pinned crash type of a row must be the type that escaped. A mismatch is an ``AdapterError``, NOT an ``AssertionError``: the
    strict xfail of the row is ``raises=AssertionError``, so an assertion here would be swallowed as the expected failure."""
    if (
        row_id in OLD_WRITER_CRASHES
        and got == "crashed"
        and crash_type != OLD_WRITER_CRASHES[row_id]
    ):
        raise AdapterError(
            f"{row_id}: the escaping type is {crash_type}, the pin says {OLD_WRITER_CRASHES[row_id]}"
        )


def test_a_wrong_crash_type_is_an_adapter_error_the_xfail_does_not_swallow() -> None:
    row_id = next(iter(OLD_WRITER_CRASHES))
    check_crash_type(row_id, "crashed", OLD_WRITER_CRASHES[row_id])
    check_crash_type(row_id, "leaked", "")
    with pytest.raises(AdapterError):
        check_crash_type(row_id, "crashed", "ZeroDivisionError")


def _param(row: corpus.Row) -> pytest.param:
    marks = []
    if row.id in OLD_WRITER_LEAKS or row.id in OLD_WRITER_CRASHES:
        kind = "crashed" if row.id in OLD_WRITER_CRASHES else "leaked"
        marks.append(
            pytest.mark.xfail(
                strict=True,
                raises=AssertionError,
                reason=f"later: R3c (P5b3) wires the writers; outcome={kind}",
            )
        )
    return pytest.param(row, id=row.id, marks=marks)


@pytest.mark.parametrize("row", [_param(r) for r in ROWS])
def test_old_writers(row: corpus.Row, app, caplog) -> None:
    got, crash_type = outcome(row, app, caplog)
    check_crash_type(row.id, got, crash_type)
    if got == "no_path":
        assert row.id in NO_OLD_WRITER_PATH, row.id
        return
    assert got == "clean", f"{row.id}: today's writers: {got} {crash_type}"
