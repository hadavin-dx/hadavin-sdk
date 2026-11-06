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
from tests.data.c18a_oracle import leaks

SIG = "sig" + "-p5a-test"  # built from parts


class AdapterError(RuntimeError):
    """The writer did not run, so no verdict may be drawn."""


# Frozen from the evidence run (see evidence.md): row id -> outcome.
OLD_WRITER_LEAKS: tuple[str, ...] = (
    "HC-builtin_text-01",
    "HC-builtin_text-02",
    "HC-builtin_text-03",
    "HC-builtin_text-04",
    "HC-builtin_text-05",
    "HC-builtin_text-07",
    "HC-builtin_text-08",
    "HC-config_detail-01",
    "HC-config_detail-03",
    "HC-config_detail-04",
    "HC-email_unicode-02",
    "HC-email_unicode-03",
    "HC-email_unicode-06",
    "HC-field_forging-01",
    "HC-field_forging-02",
    "HC-field_forging-03",
    "HC-field_forging-04",
    "HC-field_forging-05",
    "HC-field_forging-06",
    "HC-field_forging-07",
    "HC-field_forging-08",
    "HC-field_forging-09",
    "HC-foreign_driver-02",
    "HC-foreign_driver-04",
    "HC-foreign_driver-05",
    "HC-foreign_driver-06",
    "HC-foreign_driver-07",
    "HC-foreign_driver-08",
    "HC-foreign_name-01",
    "HC-foreign_name-02",
    "HC-foreign_name-03",
    "HC-group-01",
    "HC-group-02",
    "HC-group-03",
    "HC-hostile_class-01",
    "HC-hostile_class-05",
    "HC-hostile_class-06",
    "HC-hostile_class-08",
    "HC-hostile_class-09",
    "HC-hostile_class-10",
    "HC-locator_frames-01",
    "HC-locator_frames-02",
    "HC-locator_frames-03",
    "HC-locator_frames-04",
    "HC-locator_frames-05",
    "HC-locator_frames-06",
    "HC-locator_frames-07",
    "HC-locator_frames-08",
    "HC-locator_frames-09",
    "HC-locator_frames-10",
    "HC-own_class_spoof-01",
    "HC-own_class_spoof-04",
    "HC-own_class_spoof-05",
    "HC-own_class_spoof-06",
    "HC-own_class_spoof-07",
    "HC-pii_encoded-08",
    "HC-pii_obfuscated-04",
    "HC-pii_obfuscated-06",
    "HC-pii_obfuscated-07",
    "HC-pii_obfuscated-09",
    "HC-pii_obfuscated-10",
    "HC-pii_plain-04",
    "HC-pydantic_input-01",
    "HC-pydantic_input-02",
    "HC-pydantic_input-04",
    "HC-pydantic_input-05",
    "HC-pydantic_input-06",
    "HC-pydantic_input-07",
    "HC-pydantic_input-08",
    "HC-pydantic_input-09",
    "HC-pydantic_input-11",
    "HC-size_time-02",
    "HC-size_time-05",
)
OLD_WRITER_CRASHES: dict[str, str] = {
    "HC-builtin_text-10": "SystemExit",
    "HC-hostile_class-02": "RuntimeError",
    "HC-hostile_class-03": "RuntimeError",
    "HC-hostile_class-04": "RuntimeError",
    "HC-hostile_class-11": "RecursionError",
    "HC-hostile_class-14": "AttributeError",
    "HC-hostile_class-15": "AttributeError",
    "HC-own_class_spoof-02": "AttributeError",
}
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
    if row.id in OLD_WRITER_CRASHES and got == "crashed":
        assert crash_type == OLD_WRITER_CRASHES[row.id], crash_type
    if got == "no_path":
        assert row.id in NO_OLD_WRITER_PATH, row.id
        return
    assert got == "clean", f"{row.id}: today's writers: {got} {crash_type}"
