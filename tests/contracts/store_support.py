"""Helpers of the store contract suite that are not fixtures: the recording proxy, `utc_today`, and the
session-end check (P4d-a1). `conftest.py` wires them to pytest; the logic is here so that unit tests can feed it
a fake session (`tests/contracts/test_store_registry.py`)."""

from __future__ import annotations

import os
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date

from hadavin_sdk.models import now
from tests.contracts.kinds import KINDS, _fail_rule

# Store tests that exist for one backend on purpose (a test of something only Postgres has). Empty today; a name
# goes here with a written reason, never to silence a skip.
POSTGRES_ONLY_BY_DESIGN: frozenset[str] = frozenset()

# The statement a test run prints when the check cannot work (A12).
XDIST_MESSAGE = "the contract session-end check cannot run under xdist: run without -n"


class Recorder:
    """Which (backend, method) pairs a test BODY called. Calls made while a fixture sets up or tears down are
    not recorded: `in_body` is true only between the start and the end of a test's call phase."""

    def __init__(self) -> None:
        self.in_body = False
        self.called: set[tuple[str, str]] = set()

    def record(self, backend: str, method: str) -> None:
        if self.in_body:
            self.called.add((backend, method))


RECORDER = Recorder()


class RecordingStore:
    """Forwards every attribute to the store it wraps and records the public method calls made in a test body."""

    def __init__(self, inner, backend: str, recorder: Recorder = RECORDER) -> None:
        self._inner, self.backend, self._recorder = inner, backend, recorder

    def __getattr__(self, name):
        attr = getattr(self._inner, name)
        if name.startswith("_") or not callable(attr):
            return attr
        backend, recorder = self.backend, self._recorder

        def call(*args, **kwargs):
            recorder.record(backend, name)
            return attr(*args, **kwargs)

        return call


def utc_today(store) -> date:
    """The UTC date the store's clock reports. Memory: the process clock (the fake clock arrives with P4d-b, which
    switches this). Postgres: the database's `now()`, asked through the owner login, so a test that plants a date
    near today agrees with the database whatever the machine clock says."""
    if getattr(store, "backend", "memory") != "postgres":
        return now().date()
    from tests.contracts.kinds.store_postgres import pg_driver

    drv = pg_driver()
    with drv.connect_admin(store.runtime_dsn) as conn:
        return drv.execute(conn, "SELECT (now() AT TIME ZONE 'UTC')::date")[0][0]


def public_methods(protocol) -> list[str]:
    """The public methods a protocol class declares (`vars(Store)`), not its machinery."""
    return sorted(n for n, v in vars(protocol).items() if not n.startswith("_") and callable(v))


@dataclass
class SessionState:
    """What the session-end check needs, as plain data (a unit test builds one without pytest)."""

    fail_rule: bool
    xdist: bool = False
    backends: tuple[str, ...] = ()
    # nodeid -> (test function id, backend) for every store test, selected or deselected
    items: dict[str, tuple[str, str]] = field(default_factory=dict)
    selected: set[str] = field(default_factory=set)
    ran: set[str] = field(default_factory=set)
    skip_reasons: list[str] = field(default_factory=list)
    called: set[tuple[str, str]] = field(default_factory=set)
    methods: Iterable[str] = ()


def session_problems(state: SessionState) -> list[str]:
    """The reasons to fail the run; empty when the check is off or everything holds. Off unless the fail rule is
    on (`HADAVIN_REQUIRE_PG` or `CI`) and at least one selected test uses `store` or `store_pair`."""
    if not state.fail_rule or not state.selected:
        return []
    if state.xdist:
        return [XDIST_MESSAGE]
    problems = [
        f"a backend was skipped silently: {reason}"
        for reason in state.skip_reasons
        if reason.startswith("require_backend:")
    ]
    by_function: dict[tuple[str, str], list[str]] = {}
    for nodeid, key in state.items.items():
        by_function.setdefault(key, []).append(nodeid)
    for function in sorted({fn for fn, _ in state.items.values()}):
        needed = (
            ("postgres",)
            if function.rsplit("::", 1)[-1] in POSTGRES_ONLY_BY_DESIGN
            else state.backends
        )
        for backend in needed:
            ids = by_function.get((function, backend), [])
            if not ids or not all(i in state.ran for i in ids):
                problems.append(f"store test {function} did not run for backend {backend}")
    for backend in state.backends:
        for method in state.methods:
            if (backend, method) not in state.called:
                problems.append(f"no test body called Store.{method} on backend {backend}")
    return problems


def xdist_active(config) -> bool:
    return bool(os.environ.get("PYTEST_XDIST_WORKER")) or (
        config.pluginmanager.hasplugin("xdist")
        and bool(getattr(config.option, "numprocesses", None))
    )


def new_state(config) -> SessionState:
    return SessionState(
        fail_rule=_fail_rule(),
        xdist=xdist_active(config),
        backends=tuple(sorted(KINDS["store"])),
    )
