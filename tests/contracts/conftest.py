"""Contract suites: every check runs against every registered kind of its capability (design §6, §12.6)."""

import importlib
import inspect
import pkgutil
from pathlib import Path

import pytest

from hadavin_sdk.store.protocol import Store
from tests.contracts import kinds
from tests.contracts.kinds import KINDS
from tests.contracts.store_support import (
    RECORDER,
    RecordingStore,
    SessionState,
    new_state,
    public_methods,
    session_problems,
)

for _m in pkgutil.iter_modules(kinds.__path__):
    importlib.import_module(f"{kinds.__name__}.{_m.name}")


def _kinds(capability):
    return pytest.fixture(params=sorted(KINDS[capability]))


def _built(request, made):
    """A kind function may return its backend, or yield it and clean up after the test."""
    if not inspect.isgenerator(made):
        return made
    value = next(made)
    request.addfinalizer(lambda: next(made, None))
    return value


@_kinds("store")
def store(request, tmp_path):
    """One handle on the store of each backend, wrapped so that the session-end check sees which methods the
    test bodies call."""
    return RecordingStore(_built(request, KINDS["store"][request.param](tmp_path)), request.param)


@_kinds("store_pair")
def store_pair(request, tmp_path):
    """Two independent handles on the same data (memory: the same object twice; postgres: two connections)."""
    first, second = _built(request, KINDS["store_pair"][request.param](tmp_path))
    return RecordingStore(first, request.param), RecordingStore(second, request.param)


@_kinds("audit")
def audit(request, tmp_path):
    return _built(request, KINDS["audit"][request.param](tmp_path))


@_kinds("secrets")
def secrets_factory(request, tmp_path):
    return lambda seed: KINDS["secrets"][request.param](tmp_path, seed)


@_kinds("llm")
def llm_and_call(request, tmp_path):
    return KINDS["llm"][request.param](tmp_path)


@_kinds("llm_wire")
def wire(request, tmp_path):
    """A network llm kind against its fixtures (P5; `fake` has no network, so it is not one)."""
    harness = KINDS["llm_wire"][request.param](tmp_path)
    yield harness
    harness.close()


@_kinds("detector")
def detector(request, tmp_path):
    return KINDS["detector"][request.param](tmp_path)


@_kinds("detector_broken")
def broken_detector(request, tmp_path):
    """A detector kind whose backend fails (P6; `regex` has no backend to fail)."""
    return KINDS["detector_broken"][request.param](tmp_path)


@_kinds("channel")
def channel_factory(request, tmp_path):
    return lambda secret: _built(request, KINDS["channel"][request.param](tmp_path, secret))


# --- the session-end check (P4d-a1; the logic and its unit tests are in store_support.py) -------------------
_STATE: SessionState | None = None


def _uses_store(item) -> bool:
    """A test of this directory that is parametrized over the registered store kinds. (Hooks in a conftest see
    every collected item, also those of other directories, so the path is checked.)"""
    params = getattr(getattr(item, "callspec", None), "params", {})
    return item.path.is_relative_to(Path(__file__).parent) and (
        "store" in params or "store_pair" in params
    )


def _store_key(item) -> tuple[str, str]:
    params = item.callspec.params
    return f"{item.path}::{item.originalname}", params.get("store") or params.get("store_pair")


def pytest_sessionstart(session):
    global _STATE
    _STATE = new_state(session.config)
    RECORDER.called.clear()


def pytest_deselected(items):
    for item in items:
        if _STATE is not None and _uses_store(item):
            _STATE.items[item.nodeid] = _store_key(item)


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(config, items):
    if _STATE is None:
        return
    for item in items:
        if _uses_store(item):
            _STATE.items[item.nodeid] = _store_key(item)
            _STATE.selected.add(item.nodeid)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    RECORDER.in_body = True
    try:
        yield
    finally:
        RECORDER.in_body = False


def _note_skip(report):
    if _STATE is not None and report.skipped and isinstance(report.longrepr, tuple):
        _STATE.skip_reasons.append(str(report.longrepr[2]).removeprefix("Skipped: "))


def pytest_collectreport(report):
    _note_skip(report)


def pytest_runtest_logreport(report):
    if _STATE is None:
        return
    _note_skip(report)
    if (
        report.when == "call"
        and report.outcome in ("passed", "failed")
        and not hasattr(report, "wasxfail")
    ):
        _STATE.ran.add(report.nodeid)


def pytest_sessionfinish(session, exitstatus):
    if _STATE is None or exitstatus not in (0, 1):
        return
    _STATE.called = set(RECORDER.called)
    _STATE.methods = public_methods(Store)
    problems = session_problems(_STATE)
    if not problems:
        return
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    if reporter is not None:
        reporter.write_line("contract session-end check FAILED:", red=True)
        for problem in problems:
            reporter.write_line(f"  {problem}", red=True)
    session.exitstatus = pytest.ExitCode.TESTS_FAILED
