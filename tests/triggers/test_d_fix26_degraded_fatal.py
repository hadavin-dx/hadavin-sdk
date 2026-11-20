"""d-fix26: with the store DOWN at start, every configuration error that is not a connectivity error ends the process
with exit 2 and a message that names the cause (no endless retry); connectivity errors with good settings still go
degraded and recover in process. Also: the one wording for a missing field, a stronger hidden-default scan, and a
drift check that cannot skip silently."""

from __future__ import annotations

import ast
import math
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from hadavin_sdk.errors import ConfigError as AnyConfigError
from hadavin_sdk.store.protocol import StoreUnavailable, is_connectivity_error
from hadavin_sdk.triggers import worker
from tests.triggers.test_worker import (
    AGENT,
    PRINCIPAL,
    SECRET,
    _app,
    _settings,
    rt,  # noqa: F401 - fixture
)

WORKER_SRC = Path(worker.__file__)
FIELDS = (
    "tenant",
    "senders",
    "max_body_bytes",
    "max_running",
    "conflict_events_per_minute",
    "ack_wait_s",
)


@pytest.fixture(autouse=True)
def _no_worker_log_handler():
    yield
    worker._unlog_stderr()


def _good_registry(kind="service", principal=PRINCIPAL):
    return SimpleNamespace(
        agents={AGENT: object()}, principals={principal: SimpleNamespace(kind=kind)}
    )


def _patch_start(monkeypatch, settings, build, registry=None, agents=None):
    import hadavin_sdk.app
    import hadavin_sdk.config
    import hadavin_sdk.registry

    monkeypatch.setattr(hadavin_sdk.app, "build", build)
    monkeypatch.setattr(
        hadavin_sdk.config,
        "load_config",
        lambda _d=None: SimpleNamespace(triggers=settings, environment="demo"),
    )
    monkeypatch.setattr(
        hadavin_sdk.registry,
        "load_registry",
        lambda _c: registry if registry is not None else _good_registry(),
    )
    monkeypatch.setattr(
        worker, "qualified_agents", lambda _r: [AGENT] if agents is None else agents
    )


def _down_at_start(monkeypatch, settings, capsys, **kw):
    """`main` with a `build` that cannot connect. (exit code, stderr, builds, degraded server started)."""
    builds: list[int] = []
    degraded: list[int] = []

    def build(*_a, **_k):
        builds.append(1)
        raise OSError("cannot connect to private-host")

    _patch_start(monkeypatch, settings, build, **kw)
    monkeypatch.setattr(worker, "_serve_degraded", lambda *_a: degraded.append(1) or 99)
    code = worker.main(["--port", "0"])
    return code, capsys.readouterr().err, len(builds), bool(degraded)


# --- presence: one wording everywhere --------------------------------------------------------------


@pytest.mark.parametrize("field", FIELDS)
def test_a_missing_field_exits_2_with_the_one_wording_while_the_store_is_down(
    monkeypatch, capsys, field
):
    settings = _settings()
    delattr(settings, field)
    code, err, builds, degraded = _down_at_start(monkeypatch, settings, capsys)
    assert (code, degraded, builds) == (2, False, 0)
    assert f"triggers.{field} missing: core-b TriggerSettings required" in err


@pytest.mark.parametrize("field", FIELDS)
def test_the_wording_is_the_same_in_make_app(rt, field):  # noqa: F811
    settings = _settings()
    delattr(settings, field)
    with pytest.raises(worker.ConfigError) as seen:
        worker.make_app(_app(rt, settings))
    assert str(seen.value) == f"triggers.{field} missing: core-b TriggerSettings required"


def test_check_fields_runs_before_any_secret_is_read(rt):  # noqa: F811
    settings = _settings()
    delattr(settings, "ack_wait_s")
    app = _app(rt, settings)
    reads: list[str] = []
    app.trigger_secret = lambda name: reads.append(name) or SECRET
    with pytest.raises(worker.ConfigError, match="triggers.ack_wait_s missing"):
        worker.make_app(app)
    assert reads == []


# --- values: the same rules as Runner.__init__ --------------------------------------------------------

BAD_MAX_RUNNING = [None, True, "2", 2.0, math.nan, 0, -1, worker.MAX_RUNNING_CEILING + 1]
BAD_CONFLICT = [None, True, "10", 10.0, math.nan, 0, -1]
BAD_ACK = [None, True, "5", math.nan, math.inf, 0, -1, worker.ACK_WAIT_S_CEILING + 0.5]


@pytest.mark.parametrize(
    ("field", "value"),
    [("max_running", v) for v in BAD_MAX_RUNNING]
    + [("conflict_events_per_minute", v) for v in BAD_CONFLICT]
    + [("ack_wait_s", v) for v in BAD_ACK],
)
def test_a_bad_value_exits_2_naming_the_field_while_the_store_is_down(
    monkeypatch, capsys, field, value
):
    code, err, builds, degraded = _down_at_start(monkeypatch, _settings(**{field: value}), capsys)
    assert (code, degraded, builds) == (2, False, 0)
    assert "config error" in err and field in err


@pytest.mark.parametrize(
    "settings",
    [
        _settings(max_running=worker.MAX_RUNNING_CEILING),
        _settings(ack_wait_s=worker.ACK_WAIT_S_CEILING),
        _settings(ack_wait_s=3),
        _settings(conflict_events_per_minute=1),
    ],
)
def test_the_edges_of_the_good_range_still_go_degraded(monkeypatch, capsys, settings):
    code, _err, builds, degraded = _down_at_start(monkeypatch, settings, capsys)
    assert (code, degraded, builds) == (99, True, 1)


def test_the_value_rules_are_the_runners_own_helper():
    """One source for the numbers: `check_fields` and `Runner.__init__` call the same function."""
    src = WORKER_SRC.read_text()
    tree = ast.parse(src)
    callers = {
        f.name
        for f in ast.walk(tree)
        if isinstance(f, ast.FunctionDef)
        and any(
            isinstance(c, ast.Call) and getattr(c.func, "id", "") == "check_run_values"
            for c in ast.walk(f)
        )
    }
    assert {"__init__", "check_fields"} <= callers


# --- senders: agent and principal, before the store ---------------------------------------------------


def test_an_unqualified_agent_exits_2_while_the_store_is_down(monkeypatch, capsys):
    code, err, builds, degraded = _down_at_start(monkeypatch, _settings(), capsys, agents=[])
    assert (code, degraded, builds) == (2, False, 0)
    assert f"agent {AGENT} is not qualified" in err


def test_an_unknown_principal_exits_2_while_the_store_is_down(monkeypatch, capsys):
    reg = _good_registry(principal="someone-else")
    code, err, builds, degraded = _down_at_start(monkeypatch, _settings(), capsys, registry=reg)
    assert (code, degraded, builds) == (2, False, 0)
    assert f"principal {PRINCIPAL} is not in principals.yaml" in err


def test_a_principal_that_is_not_a_service_exits_2_while_the_store_is_down(monkeypatch, capsys):
    reg = _good_registry(kind="human")
    code, err, builds, degraded = _down_at_start(monkeypatch, _settings(), capsys, registry=reg)
    assert (code, degraded, builds) == (2, False, 0)
    assert "is not of kind service" in err


# --- the distinction: StoreUnavailable is a connectivity error, a plain config error is not ---------------


def test_store_unavailable_is_an_sdk_config_error_but_not_the_workers_and_is_connectivity():
    assert issubclass(StoreUnavailable, AnyConfigError)
    assert not issubclass(StoreUnavailable, worker.ConfigError)
    assert is_connectivity_error(StoreUnavailable("down"))
    assert is_connectivity_error(OSError("refused"))
    assert not is_connectivity_error(worker.ConfigError("bad"))
    assert not is_connectivity_error(AnyConfigError("bad"))


# --- after the start: the store comes back, then the config problem shows; or never shows ------------------


def _run_main_in_thread(args, timeout=20.0):
    out: list[int] = []
    thread = threading.Thread(target=lambda: out.append(worker.main(args)), daemon=True)
    thread.start()
    thread.join(timeout)
    return out, thread


def _fast_recheck(monkeypatch):
    monkeypatch.setattr(worker, "HEALTH_RECHECK_S", 0.05)


def test_a_secret_read_failure_found_when_the_store_returns_ends_with_exit_2(
    monkeypatch,
    capsys,
    rt,  # noqa: F811
):
    _fast_recheck(monkeypatch)
    settings = _settings()
    app = _app(rt, settings)

    def broken(_name):
        raise KeyError("top-secret-value")

    app.trigger_secret = broken
    calls: list[int] = []

    def build(*_a, **_k):
        calls.append(1)
        if len(calls) < 3:
            raise OSError("down")
        return app

    _patch_start(monkeypatch, settings, build)
    out, thread = _run_main_in_thread(["--port", "0"])
    assert not thread.is_alive(), "the degraded worker kept retrying a configuration error"
    assert out == [2]
    err = capsys.readouterr().err
    assert "a secret could not be read" in err and "KeyError" in err
    assert "top-secret-value" not in err


@pytest.mark.parametrize(
    "error", [worker.ConfigError("sender x: bad thing"), AnyConfigError("some sdk config problem")]
)
def test_a_config_error_on_a_retry_ends_with_exit_2(monkeypatch, capsys, error):
    _fast_recheck(monkeypatch)
    calls: list[int] = []

    def build(*_a, **_k):
        calls.append(1)
        raise OSError("down") if len(calls) == 1 else error

    _patch_start(monkeypatch, _settings(), build)
    out, thread = _run_main_in_thread(["--port", "0"])
    assert not thread.is_alive()
    assert out == [2]
    assert "config error" in capsys.readouterr().err


@pytest.mark.parametrize("error", [OSError("down"), StoreUnavailable("still down")])
def test_connectivity_errors_on_retries_stay_degraded(monkeypatch, error):
    _fast_recheck(monkeypatch)
    calls: list[int] = []

    def fails(_args):
        calls.append(1)
        raise error

    monkeypatch.setattr(worker, "_recover", fails)
    degraded = worker._Degraded(SimpleNamespace())
    degraded.start()
    try:
        deadline = time.monotonic() + 10
        while len(calls) < 8 and time.monotonic() < deadline:
            time.sleep(0.01)
        assert len(calls) >= 8 and degraded._thread.is_alive()
        assert degraded.fatal is None
    finally:
        degraded.close()


# --- the scan, stronger ----------------------------------------------------------------------------------


def _is_value(node):
    """A number, a negated number, or an UPPER_CASE constant name: a fixed fallback value."""
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub | ast.UAdd):
        return _is_value(node.operand)
    if isinstance(node, ast.Constant):
        return isinstance(node.value, int | float) and not isinstance(node.value, bool)
    if isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", "")) in (
        "float",
        "int",
        "Decimal",
    ):  # float("inf"), Decimal("4"), int(4)
        return all(isinstance(a, ast.Constant) for a in node.args)
    if isinstance(node, ast.Attribute) and node.attr in ("inf", "nan"):  # math.inf
        return True
    return isinstance(node, ast.Name) and node.id.isupper()


def _mentions(node, name):
    for n in ast.walk(node):
        if isinstance(n, ast.Attribute | ast.Name):
            ident = n.attr if isinstance(n, ast.Attribute) else n.id
            if name in ident.lower():
                return True
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and name in n.value.lower():
            return True
    return False


def _names(handler_type):
    if handler_type is None:
        return set()
    items = handler_type.elts if isinstance(handler_type, ast.Tuple) else [handler_type]
    return {getattr(i, "id", getattr(i, "attr", "")) for i in items}


def hidden_defaults(tree, name):
    """Line numbers where code that mentions `name` falls back to a fixed number or constant: `a or 4`,
    `a or 4.0`, `a or CONST`, `a or -1`, `4 if c else a`, `get(name, 4)`, `getattr(x, name, CONST)`,
    `max(a, 4)` / `min(a, 4)`, and `try: a = x.name / except AttributeError: return 4`."""
    found = []
    for n in ast.walk(tree):
        if isinstance(n, ast.BoolOp) and isinstance(n.op, ast.Or):
            if any(_is_value(v) for v in n.values) and any(_mentions(v, name) for v in n.values):
                found.append(n.lineno)
        elif isinstance(n, ast.IfExp):
            if (_is_value(n.body) or _is_value(n.orelse)) and _mentions(n, name):
                found.append(n.lineno)
        elif isinstance(n, ast.Call):
            fn = getattr(n.func, "attr", getattr(n.func, "id", ""))
            if (
                fn in ("get", "getattr", "setdefault")
                and any(_is_value(a) for a in n.args[1:])
                and any(_mentions(a, name) for a in n.args[:2])
            ) or (
                fn in ("max", "min")
                and any(_is_value(a) for a in n.args)
                and any(_mentions(a, name) for a in n.args)
            ):
                found.append(n.lineno)
        elif isinstance(n, ast.Try) and any(_mentions(s, name) for s in n.body):
            for h in n.handlers:
                if "AttributeError" in _names(h.type) and any(
                    isinstance(s, ast.Return | ast.Assign | ast.AugAssign | ast.AnnAssign)
                    and s.value is not None
                    and _is_value(s.value)
                    for s in ast.walk(h)
                ):
                    found.append(h.lineno)
    return found


@pytest.mark.parametrize("name", ["max_running", "conflict_events_per_minute", "ack_wait_s"])
def test_worker_source_has_no_hidden_fallback(name):
    assert hidden_defaults(ast.parse(WORKER_SRC.read_text()), name) == []


@pytest.mark.parametrize(
    "code",
    [
        "x = settings.max_running or 4",
        "x = settings.max_running or 4.0",
        "x = settings.max_running or DEFAULT_RUNNING",
        "x = settings.max_running or -1",
        "x = settings.max_running if ok else 4",
        "x = 4 if ok else settings.max_running",
        "x = getattr(settings, 'max_running', 4)",
        "x = getattr(settings, 'max_running', DEFAULT)",
        "x = cfg.get('max_running', -1)",
        "x = max(settings.max_running, 4)",
        "x = min(4, settings.max_running)",
        "try:\n    x = s.max_running\nexcept AttributeError:\n    return 4",
        "try:\n    x = s.max_running\nexcept (KeyError, AttributeError):\n    return DEFAULT",
        "try:\n    x = s.max_running\nexcept AttributeError:\n    x = 4",
        "try:\n    x = s.max_running\nexcept AttributeError:\n    x = 4.0",
        "try:\n    x = s.max_running\nexcept AttributeError:\n    x: int = DEFAULT",
        "x = settings.max_running or float('inf')",
        "x = settings.max_running or Decimal('4')",
        "x = settings.max_running or math.inf",
        "x = getattr(settings, 'max_running', float('inf'))",
        "x = settings.max_running if ok else Decimal(4)",
    ],
)
def test_the_scan_catches_what_it_is_meant_to_catch(code):
    assert hidden_defaults(ast.parse(code), "max_running") != []


@pytest.mark.parametrize(
    "code",
    [
        "x = settings.max_running\ny = a or b",
        "x = max(settings.max_running, other)",
        "try:\n    x = s.max_running\nexcept AttributeError:\n    raise",
        "try:\n    x = s.max_running\nexcept OSError:\n    return 4",
        "try:\n    x = s.max_running\nexcept AttributeError:\n    x = other",
        "x = settings.max_running or float(other)",
        "x = other or 4",
    ],
)
def test_the_scan_leaves_plain_code_alone(code):
    assert hidden_defaults(ast.parse(code), "max_running") == []


# --- post-merge drift ------------------------------------------------------------------------------------


def drift_problems(defaults_module):
    """Every constant of the module whose name has both TRIGGER and CONFLICT must equal the Runner's default."""
    return [
        name
        for name in dir(defaults_module)
        if "TRIGGER" in name
        and "CONFLICT" in name
        and getattr(defaults_module, name) != worker.CONFLICT_EVENTS_PER_MINUTE
    ]


def test_the_drift_check_fails_on_a_different_value_and_passes_on_an_equal_one():
    same = SimpleNamespace(TRIGGER_CONFLICT_EVENTS_PER_MINUTE=worker.CONFLICT_EVENTS_PER_MINUTE)
    other = SimpleNamespace(TRIGGER_CONFLICT_EVENTS=worker.CONFLICT_EVENTS_PER_MINUTE + 1)
    assert drift_problems(same) == []
    assert drift_problems(other) == ["TRIGGER_CONFLICT_EVENTS"]


def test_runner_default_equals_core_b_default():
    from hadavin_sdk import defaults

    names = [n for n in dir(defaults) if "TRIGGER" in n and "CONFLICT" in n]
    if not names:
        pytest.skip("core-b defaults has no trigger conflict constant yet")
    assert drift_problems(defaults) == []
