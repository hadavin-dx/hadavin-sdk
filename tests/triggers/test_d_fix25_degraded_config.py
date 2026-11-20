"""d-fix25: a config error is never hidden by a store that is down at start; the settings fields are checked BEFORE
the store is built; the docs and scans of d-fix22/24 are tightened."""

from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

from hadavin_sdk.triggers import worker
from tests.triggers.test_worker import AGENT, PRINCIPAL, _settings

WORKER_SRC = Path(worker.__file__)


def _start_with_store_down(monkeypatch, settings, capsys):
    """`main` with a config that has `settings` and a `build` that cannot connect. Returns (exit code, stderr,
    number of `build` calls, whether the degraded server was started)."""
    import hadavin_sdk.app
    import hadavin_sdk.config
    import hadavin_sdk.registry

    builds: list[int] = []

    def build(*_a, **_kw):
        builds.append(1)
        raise OSError("cannot connect to private-host")

    degraded: list[int] = []
    monkeypatch.setattr(hadavin_sdk.app, "build", build)
    monkeypatch.setattr(
        hadavin_sdk.config,
        "load_config",
        lambda _d=None: SimpleNamespace(triggers=settings, environment="demo"),
    )
    good = SimpleNamespace(
        principals={PRINCIPAL: SimpleNamespace(kind="service")}
    )  # d-fix26: checked before build
    monkeypatch.setattr(hadavin_sdk.registry, "load_registry", lambda _c: good)
    monkeypatch.setattr(worker, "qualified_agents", lambda _r: [AGENT])
    monkeypatch.setattr(worker, "_serve_degraded", lambda *_a: degraded.append(1) or 99)
    code = worker.main(["--port", "0"])
    return code, capsys.readouterr().err, len(builds), bool(degraded)


@pytest.mark.parametrize("field", ["max_running", "conflict_events_per_minute"])
def test_a_missing_field_exits_2_even_when_the_store_is_down(monkeypatch, capsys, field):
    settings = _settings()
    delattr(settings, field)
    code, err, builds, degraded = _start_with_store_down(monkeypatch, settings, capsys)
    assert (code, degraded) == (2, False)
    assert f"triggers.{field} missing: core-b TriggerSettings required" in err
    assert builds == 0  # checked before the store is built


def test_a_connectivity_error_with_good_settings_still_goes_degraded(monkeypatch, capsys):
    code, _err, builds, degraded = _start_with_store_down(monkeypatch, _settings(), capsys)
    assert (code, degraded, builds) == (99, True, 1)


def test_the_module_text_names_the_conflict_setting():
    doc = worker.__doc__
    assert "at most 10 per sender per minute" not in doc
    assert "triggers.conflict_events_per_minute" in doc
    settings_para = doc[doc.index("Settings:") :]
    assert "conflict_events_per_minute" in settings_para.split("`host`")[0]


def test_the_ticket_does_not_say_endpoint_py_references_the_names():
    src = (WORKER_SRC.parents[1] / "triggers" / "endpoint.py").read_text()
    assert "conflict_events_per_minute" not in src and "max_running" not in src
    ticket = Path(__file__).parents[2] / "handover/core-a/tickets/D-signed-endpoint.md"
    if ticket.exists():
        text = ticket.read_text()
        para = text[text.index("d-fix24 ") :].split("\n", 1)[0]
        assert "endpoint.py" not in para


# --- the AST scans of d-fix22/24, stronger: `x or <int>`, `x if c else <int>`, `.get(name, <int>)`


def _is_int(node):
    return isinstance(node, ast.Constant) and isinstance(node.value, int)


def _mentions(node, name):
    for n in ast.walk(node):
        if isinstance(n, ast.Attribute | ast.Name):
            ident = n.attr if isinstance(n, ast.Attribute) else n.id
            if name in ident.lower():
                return True
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and name in n.value.lower():
            return True
    return False


def hidden_defaults(tree, name):
    """Line numbers where an expression that mentions `name` falls back to an int: `a or 4`, `4 if c else a`,
    `a if c else 4`, `get(name, 4)`, `getattr(x, name, 4)`."""
    found = []
    for n in ast.walk(tree):
        if isinstance(n, ast.BoolOp) and isinstance(n.op, ast.Or):
            if any(_is_int(v) for v in n.values) and any(_mentions(v, name) for v in n.values):
                found.append(n.lineno)
        elif isinstance(n, ast.IfExp):
            if (_is_int(n.body) or _is_int(n.orelse)) and _mentions(n, name):
                found.append(n.lineno)
        elif isinstance(n, ast.Call):
            fn = getattr(n.func, "attr", getattr(n.func, "id", ""))
            ints = any(_is_int(a) for a in n.args[1:])
            if (
                fn in ("get", "getattr", "setdefault")
                and ints
                and any(_mentions(a, name) for a in n.args[:2])
            ):
                found.append(n.lineno)
    return found


@pytest.mark.parametrize("name", ["max_running", "conflict_events_per_minute"])
def test_worker_source_has_no_hidden_int_fallback(name):
    assert hidden_defaults(ast.parse(WORKER_SRC.read_text()), name) == []


@pytest.mark.parametrize(
    "code",
    [
        "x = settings.max_running or 4",
        "x = settings.max_running if ok else 4",
        "x = 4 if ok else settings.max_running",
        "x = getattr(settings, 'max_running', 4)",
        "x = cfg.get('max_running', 4)",
    ],
)
def test_the_scan_catches_what_it_is_meant_to_catch(code):
    assert hidden_defaults(ast.parse(code), "max_running") != []


def test_the_scan_leaves_plain_code_alone():
    assert hidden_defaults(ast.parse("x = settings.max_running\ny = a or b"), "max_running") == []


# --- post-merge drift: the Runner's own default must be core-b's default


def _core_b_default():
    try:
        from hadavin_sdk import defaults
    except ImportError:
        return None
    return getattr(defaults, "TRIGGER_CONFLICT_EVENTS_DEFAULT", None)


@pytest.mark.skipif(
    _core_b_default() is None,
    reason="core-b's hadavin_sdk.defaults has no TRIGGER_CONFLICT_EVENTS_DEFAULT on this tree (post-merge check)",
)
def test_runner_default_equals_core_b_default():
    assert worker.CONFLICT_EVENTS_PER_MINUTE == _core_b_default()
