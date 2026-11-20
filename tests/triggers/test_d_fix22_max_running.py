"""d-fix22: `max_running` has ONE source, the config (`config.triggers.max_running`, core-b's `TriggerSettings`;
its default is core-b's, not yet named in this tree's defaults.py). The worker holds no number of its own and refuses to start without the field."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from types import SimpleNamespace

import pytest

from hadavin_sdk.triggers import worker
from tests.triggers.test_worker import _app, _settings, rt  # noqa: F401

HERE = Path(__file__).parent
WORKER_SRC = Path(worker.__file__)


def _pool_bound(runner) -> int:
    return runner._pool._max_workers  # the real bound of the executor the Runner builds


def _make(rt, **over):  # noqa: F811
    _wsgi, runner = worker.make_app(_app(rt, _settings(**over)))
    return runner


@pytest.mark.parametrize("value", [7, 2])
def test_pool_size_is_the_configured_max_running(rt, value):  # noqa: F811
    runner = _make(rt, max_running=value)
    try:
        assert _pool_bound(runner) == value
        assert runner._slots._value == value
    finally:
        runner.close(0)


def test_changing_the_value_changes_the_worker(rt):  # noqa: F811
    bounds = []
    for value in (7, 2):
        runner = _make(rt, max_running=value)
        try:
            bounds.append(_pool_bound(runner))
        finally:
            runner.close(0)
    assert bounds == [7, 2]


def test_a_settings_object_without_max_running_is_a_config_error(rt):  # noqa: F811
    settings = _settings()
    del settings.max_running
    with pytest.raises(
        worker.ConfigError,
        match=r"triggers\.max_running missing: core-b TriggerSettings required",
    ):
        worker.make_app(_app(rt, settings))


def test_runner_has_no_default_for_max_running():
    param = inspect.signature(worker.Runner).parameters["max_running"]
    assert param.default is inspect.Parameter.empty
    assert not hasattr(worker, "MAX_RUNNING")


def _named_max_running(name: str | None) -> bool:
    """A name for the number of runs; the CEILING (an upper bound the config is checked against) is not a default."""
    return (
        name is not None and "max_running" in name.lower() and not name.lower().endswith("ceiling")
    )


def test_worker_source_has_no_numeric_default_for_max_running():
    tree = ast.parse(WORKER_SRC.read_text())
    bad: list[int] = []

    def is_int(node):
        return isinstance(node, ast.Constant) and isinstance(node.value, int)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign | ast.AnnAssign):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names = [t.id if isinstance(t, ast.Name) else getattr(t, "attr", None) for t in targets]
            if any(_named_max_running(n) for n in names) and is_int(node.value):
                bad.append(node.lineno)
        elif isinstance(node, ast.keyword):
            if _named_max_running(node.arg) and is_int(node.value):
                bad.append(node.value.lineno)
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            a = node.args
            pos = a.posonlyargs + a.args
            pairs = list(zip(pos[len(pos) - len(a.defaults) :], a.defaults, strict=True))
            pairs += [(k, d) for k, d in zip(a.kwonlyargs, a.kw_defaults, strict=True) if d]
            bad += [d.lineno for arg, d in pairs if _named_max_running(arg.arg) and is_int(d)]
        elif isinstance(node, ast.Call) and getattr(node.func, "id", "") == "getattr":
            if len(node.args) == 3 and any(
                isinstance(x, ast.Constant) and x.value == "max_running" for x in node.args
            ):
                bad.append(node.lineno)  # getattr(settings, "max_running", <default>)
    assert bad == [], f"worker.py has its own default for max_running at lines {bad}"


def test_the_stand_in_settings_of_the_trigger_tests_carry_max_running():
    """Every stand-in of `TriggerSettings` in tests/triggers (a dict or a SimpleNamespace with `max_body_bytes`)
    also names `max_running`."""
    missing = []
    for path in sorted(HERE.glob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            keys: set[str] = set()
            if isinstance(node, ast.Dict):
                keys = {k.value for k in node.keys if isinstance(k, ast.Constant)}
            elif isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "SimpleNamespace":
                keys = {k.arg for k in node.keywords if k.arg}
            if "max_body_bytes" in keys and "max_running" not in keys:
                missing.append(f"{path.name}:{node.lineno}")
    assert missing == []


def test_stand_in_helper_is_the_simplenamespace_shape(rt):  # noqa: F811
    assert isinstance(_settings(), SimpleNamespace) and _settings().max_running == 2
