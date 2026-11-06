"""Helpers of the store contract suite that are not fixtures: the recording proxy, `utc_today`, and the
session-end check (P4d-a1). `conftest.py` wires them to pytest; the logic is here so that unit tests can feed it
a fake session (`tests/contracts/test_store_registry.py`).

Public names (blessed for P4d-a2 and later, order 101): `RECORDER`, `Recorder`, `RecordingStore`, `utc_today`,
`public_methods`, `SessionState`, `session_problems`, `xdist_active`, `new_state`, `POSTGRES_ONLY_BY_DESIGN`,
`XDIST_MESSAGE`. A change to one of them is a change to every store test, so it goes through review as such."""

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
    # nodeid -> (test function id, backend) for every SELECTED store test (a deselected one is not expected to run)
    items: dict[str, tuple[str, str]] = field(default_factory=dict)
    selected: set[str] = field(default_factory=set)
    ran: set[str] = field(default_factory=set)
    skip_reasons: list[str] = field(default_factory=list)
    called: set[tuple[str, str]] = field(default_factory=set)
    methods: Iterable[str] = ()


def session_problems(state: SessionState) -> list[str]:
    """The reasons to fail the run; empty when the check is off or everything holds.

    The check is off unless the fail rule is on (`HADAVIN_REQUIRE_PG` or `CI`). The rules, all under that rule:

    1. xdist is judged FIRST and whatever was selected: a process of an xdist run that collected nothing must not
       read as "nothing to check"; it fails with `XDIST_MESSAGE`. (A run that selects no store test and does not
       use xdist is silent: a `-m perf` run has nothing to check.) The xdist CONTROLLER never loads this
       directory's conftest and a worker's exit status does not reach the controller's, so this branch cannot be
       what stops a real xdist run: `tests/conftest.py` refuses it at configure time (`pytest.UsageError` with the
       same message), and this branch is the second line for a worker.
    2. Only SELECTED items count. A store test that `-m`, `-k` or `--deselect` removed from the run is not
       expected to have run, so a test marked `perf` or `live` does not fail every CI run for ever. A function is
       judged when at least one of its items is selected, and then every backend must have run all of its
       SELECTED items: `-k memory` (postgres items gone) fails by design, because the run no longer proves the
       contract for Postgres; do not set the fail rule for a narrowed local run.
    3. A selected item that is skipped fails the run whatever the reason (a mark, `pytest.skip`, a fixture): a
       store test runs on both backends or it is not a store test. The one exemption is
       `POSTGRES_ONLY_BY_DESIGN` (a named test that needs only Postgres), and a skip is not a way into it.
    4. A skip whose reason starts `require_backend:` (a backend missing) is reported as such.
    5. Every public `Store` method must have been called by some test BODY on every backend (a call made while a
       fixture sets up or tears down does not count)."""
    if not state.fail_rule:
        return []
    if state.xdist:
        return [XDIST_MESSAGE]
    if not state.selected:
        return []
    problems = [
        f"a backend was skipped silently: {reason}"
        for reason in state.skip_reasons
        if reason.startswith("require_backend:")
    ]
    by_function: dict[tuple[str, str], list[str]] = {}
    for nodeid in sorted(state.selected):
        by_function.setdefault(state.items[nodeid], []).append(nodeid)
    for function in sorted({fn for fn, _ in by_function}):
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
    """True in an xdist worker (the plugin sets `PYTEST_XDIST_WORKER` there) and in the controller of a run that
    asks for workers (`-n N`, or `--dist` other than `no`). `-n 0` and a plain run are not xdist."""
    if os.environ.get("PYTEST_XDIST_WORKER"):
        return True
    if not config.pluginmanager.hasplugin("xdist"):
        return False
    option = config.option
    return bool(getattr(option, "numprocesses", None)) or getattr(option, "dist", "no") not in (
        "no",
        None,
    )


def new_state(config) -> SessionState:
    return SessionState(
        fail_rule=_fail_rule(),
        xdist=xdist_active(config),
        backends=tuple(sorted(KINDS["store"])),
    )
