"""PEEL-run-id: `Runtime.handle(..., run_id=...)` starts a run with a caller-chosen id (ticket PEEL-run-id)."""

import inspect
import re

import pytest

from hadavin_sdk import models
from hadavin_sdk.models import RunState
from hadavin_sdk.runtime import agent_loop
from hadavin_sdk.runtime.agent_loop import Runtime
from hadavin_sdk.store.protocol import NotFound, StaleState
from tests.test_s5_runtime import _doc, build

# Looked up by name so that on the base commit (which has neither) the tests FAIL by assertion or TypeError,
# not by a collection error.
# ORACLE is written out here on purpose: the tests must not use the pattern under test to judge itself.
ORACLE = re.compile(r"run-[0-9a-f]{32}")
RUN_ID_PATTERN = getattr(models, "RUN_ID_PATTERN", ORACLE)
InvalidRunId = getattr(agent_loop, "InvalidRunId", type("InvalidRunId", (ValueError,), {}))

AGENT, PRINCIPAL = "test-agent", "svc:test-agent"
GOOD = "run-" + "0123456789abcdef" * 2
# The shape AK-G2's run_id_for gives: "run-" + 28 hex + 4 hex = 36 characters.
AK_G2_SHAPE = "run-" + "a1b2c3d" * 4 + format(7, "04x")


def _count_rows(rt):
    return len(rt.audit.events(GOOD))


def test_t1_given_id_is_the_run_id(cfg_dir):
    rt, cfg = build(cfg_dir)
    run = rt.handle(AGENT, PRINCIPAL, _doc(cfg, "chat.txt"), run_id=GOOD)
    assert run.run_id == GOOD
    assert rt.store.get_run(GOOD).run_id == GOOD


def test_t2_same_id_twice_is_refused_and_nothing_else_happens(cfg_dir):
    rt, cfg = build(cfg_dir)
    doc = _doc(cfg, "chat.txt")
    rt.handle(AGENT, PRINCIPAL, doc, trigger_ref="m-1", run_id=GOOD)
    calls, notes = len(rt.llm.calls), _count_rows(rt)
    assert calls == 1 and notes > 0
    with pytest.raises(StaleState):
        rt.handle(AGENT, PRINCIPAL, doc, trigger_ref="m-1", run_id=GOOD)
    assert len(rt.llm.calls) == calls  # no second model call, so no second spend
    assert _count_rows(rt) == notes  # no second "received" note
    assert rt.store.get_run(GOOD).state == RunState.NO_ACTION  # the first run is untouched


def test_t3_without_run_id_ids_are_fresh_and_well_formed(cfg_dir):
    rt, cfg = build(cfg_dir)
    doc = _doc(cfg, "injected.txt")  # stops before the model, so the recording is not used up
    a = rt.handle(AGENT, PRINCIPAL, doc)
    b = rt.handle(AGENT, PRINCIPAL, doc, run_id=None)
    assert a.run_id != b.run_id
    assert ORACLE.fullmatch(a.run_id) and ORACLE.fullmatch(b.run_id)


HOSTILE = [
    "",
    "run-",
    "run-" + "a" * 31,
    "run-" + "a" * 33,
    "run-" + "A" * 32,
    "run-" + "g" * 32,
    "../" + "a" * 33,
    GOOD + "\n",
    "\n" + GOOD,
    GOOD + " ",
    "run-" + "a" * 31 + "\x00",
    "run-" + "a" * 31 + chr(0x661),  # Arabic-Indic digit one
    GOOD + ":1",
    "a" * 36,
    "ru-" + "a" * 33,
    "run_" + "a" * 32,
    123,
    GOOD.encode(),
    ["x"],
]


@pytest.mark.parametrize("bad", HOSTILE, ids=[repr(h)[:30] for h in HOSTILE])
def test_t4_hostile_ids_are_refused_before_any_write(cfg_dir, bad):
    rt, cfg = build(cfg_dir)
    with pytest.raises(InvalidRunId):
        rt.handle(AGENT, PRINCIPAL, _doc(cfg, "chat.txt"), run_id=bad)
    assert rt.llm.calls == []
    assert rt.audit.events() == []  # no note of any run: nothing was written
    if isinstance(bad, str):
        with pytest.raises(NotFound):
            rt.store.get_run(bad)


def test_t5_accepts_exactly_the_pattern(cfg_dir):
    """Every one-character damage (replace, insert, cut) of a valid id, at every position, with an awkward alphabet."""
    alphabet = "0123456789abcdefABCDEFg-_:/. \n\x00" + chr(0x661)
    rt, cfg = build(cfg_dir)
    doc = _doc(cfg, "injected.txt")  # stops before the model, so the recording is not used up
    cases = {GOOD}
    for k in range(len(GOOD) + 1):
        cases.add(GOOD[:k] + GOOD[k + 1 :])
        for c in alphabet:
            cases.add(GOOD[:k] + c + GOOD[k + 1 :])
            cases.add(GOOD[:k] + c + GOOD[k:])
    ok = bad = 0
    for text in sorted(cases):
        if ORACLE.fullmatch(text):
            assert rt.handle(AGENT, PRINCIPAL, doc, run_id=text).run_id == text
            ok += 1
        else:
            with pytest.raises(InvalidRunId):
                rt.handle(AGENT, PRINCIPAL, doc, run_id=text)
            bad += 1
    assert ok > 5 and bad > 500  # both branches were really exercised


def test_t6_the_ak_g2_id_shape_is_accepted(cfg_dir):
    rt, cfg = build(cfg_dir)
    assert len(AK_G2_SHAPE) == 36
    assert (
        rt.handle(AGENT, PRINCIPAL, _doc(cfg, "chat.txt"), run_id=AK_G2_SHAPE).run_id == AK_G2_SHAPE
    )


def test_t7_run_id_is_keyword_only_with_default_none():
    p = inspect.signature(Runtime.handle).parameters["run_id"]
    assert p.kind is inspect.Parameter.KEYWORD_ONLY and p.default is None


def test_t8_model_pattern_is_the_written_out_oracle():
    assert RUN_ID_PATTERN.pattern == ORACLE.pattern
