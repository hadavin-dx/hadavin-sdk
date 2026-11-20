"""d-fix24: `triggers.conflict_events_per_minute` has ONE source, the config (core-b's `TriggerSettings`). `make_app`
reads it like `max_running` and hands it to the Runner; the worker has no number of its own on that path."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from hadavin_sdk.triggers import worker
from tests.k5_support import build_runtime, k5_cfg
from tests.triggers.test_d_fix6_e1 import _conflicts, _req
from tests.triggers.test_worker import (
    DOCUMENT,
    OTHER_DOCUMENT,
    GateLLM,
    _app,
    _free,
    _settings,
    _settle,
)

WORKER_SRC = Path(worker.__file__)


@pytest.fixture
def rt(tmp_path):
    runtime, _cards = build_runtime(k5_cfg(tmp_path), GateLLM())
    return runtime


def _runner(rt, cap, clock):
    app = _app(rt, _settings(conflict_events_per_minute=cap))
    app.audit = rt.audit
    _wsgi, runner = worker.make_app(app, rate_clock=lambda: clock[0])
    return runner


def _written(rt, cap):
    """Conflict events written when 30 conflicts arrive inside one minute, with the setting at `cap`."""
    clock = [1000.0]
    runner = _runner(rt, cap, clock)
    try:
        first, other = _req(DOCUMENT), _req(OTHER_DOCUMENT)
        assert runner.start(first)[0] in (200, 202)
        _settle(rt.store, first.run_id)
        _free(runner)
        for _ in range(30):
            clock[0] += 1.0
            assert runner.start(other) == (409, {})  # still answered beyond the cap
        return len(_conflicts(rt)), runner.conflict_events_dropped
    finally:
        runner.close(0)


def test_the_setting_caps_the_conflict_events_per_sender_per_minute(rt):
    assert _written(rt, 3) == (3, 27)


def test_changing_the_setting_changes_the_cap(tmp_path):
    results = []
    for cap in (3, 7):
        runtime, _cards = build_runtime(k5_cfg(tmp_path / str(cap)), GateLLM())
        results.append(_written(runtime, cap))
    assert results == [(3, 27), (7, 23)]


def test_a_settings_object_without_the_field_is_a_config_error(rt):
    settings = _settings()
    del settings.conflict_events_per_minute
    with pytest.raises(
        worker.ConfigError,
        match=r"triggers\.conflict_events_per_minute missing: core-b TriggerSettings required",
    ):
        worker.make_app(_app(rt, settings))


def test_make_app_takes_no_conflict_parameter():
    assert "conflict_events_per_minute" not in inspect.signature(worker.make_app).parameters


def _named(name: str | None) -> bool:
    return name is not None and "conflict_events_per_minute" in name.lower()


def test_worker_source_has_no_numeric_default_on_the_make_app_path():
    """No int default for a name like conflict_events_per_minute anywhere in worker.py except the one module
    constant that is the default of a directly built Runner; `make_app` itself has none."""
    tree = ast.parse(WORKER_SRC.read_text())
    bad: list[int] = []

    def is_int(node):
        return isinstance(node, ast.Constant) and isinstance(node.value, int)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign | ast.AnnAssign):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names = [t.id if isinstance(t, ast.Name) else getattr(t, "attr", None) for t in targets]
            if (
                any(_named(n) and n != "CONFLICT_EVENTS_PER_MINUTE" for n in names)
                and node.value
                and is_int(node.value)
            ):
                bad.append(node.lineno)
        elif isinstance(node, ast.keyword):
            if _named(node.arg) and is_int(node.value):
                bad.append(node.value.lineno)
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            a = node.args
            pos = a.posonlyargs + a.args
            pairs = list(zip(pos[len(pos) - len(a.defaults) :], a.defaults, strict=True))
            pairs += [(k, d) for k, d in zip(a.kwonlyargs, a.kw_defaults, strict=True) if d]
            for arg, d in pairs:
                if _named(arg.arg) and (is_int(d) or node.name == "make_app"):
                    bad.append(d.lineno)
        elif isinstance(node, ast.Call) and getattr(node.func, "id", "") == "getattr":
            if len(node.args) == 3 and any(
                isinstance(x, ast.Constant) and x.value == "conflict_events_per_minute"
                for x in node.args
            ):
                bad.append(node.lineno)
    assert bad == [], f"worker.py has its own default for conflict_events_per_minute at {bad}"
