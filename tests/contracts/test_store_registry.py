"""P4d-a1: the store kind registry, `require_backend`, the recording proxy and the session-end check.

The session-end check is unit-tested on a fake session (`SessionState`); the nested tests at the end run a real
pytest, with the CI command and NO file argument, on a throw-away project that holds a verbatim copy of
`conftest.py`, to prove the hooks are wired the way CI loads them. Imports of the new helpers sit inside the
tests so that the fail-before test (which needs only the old `pg_schema`) can run alone against the code before
this change."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.contracts.kinds import KINDS
from tests.contracts.kinds.store_postgres import pg_schema

ROOT = Path(__file__).resolve().parents[2]
RULE_VARS = ("HADAVIN_REQUIRE_PG", "CI")


def _outcome(fn):
    """What `fn` did: 'returned', or the class name of the pytest outcome or error it raised (a skip is a
    BaseException, so it is caught here instead of ending the test as skipped)."""
    try:
        fn()
    except (pytest.fail.Exception, pytest.skip.Exception, ValueError) as exc:
        return type(exc).__name__, getattr(exc, "msg", str(exc))
    return "returned", ""


@pytest.fixture
def no_rule(monkeypatch):
    for name in RULE_VARS:
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


# --- the registry (regression pin: the Postgres kind registers unconditionally) ------------------------------
def test_store_and_store_pair_are_registered_for_memory_and_postgres():
    assert set(KINDS["store"]) == {"memory", "postgres"}
    assert set(KINDS["store_pair"]) == {"memory", "postgres"}


# --- FAIL-BEFORE: on the code before P4d-a1 this generator skipped where it must fail ------------------------
def test_pg_schema_fails_instead_of_skipping_in_ci_without_a_database(no_rule):
    from tests.contracts.kinds import require_backend

    require_backend("postgres", dsn=False)  # no rule yet: skips where the driver is missing
    no_rule.setenv("CI", "1")
    no_rule.delenv("HADAVIN_TEST_PG_DSN", raising=False)
    kind, _ = _outcome(lambda: next(pg_schema()))
    assert kind == "Failed", f"expected a failure in CI, got {kind}"


def test_pg_schema_still_skips_on_a_laptop_without_a_database(no_rule):
    no_rule.delenv("HADAVIN_TEST_PG_DSN", raising=False)
    from tests.contracts.kinds import require_backend

    require_backend("postgres", dsn=False)
    kind, msg = _outcome(lambda: next(pg_schema()))
    assert kind == "Skipped"
    assert msg.startswith("require_backend:")


def test_the_driver_constant_names_the_module_the_namespace_loads():
    """`PG_DRIVER_MODULE` is the one place the contract helpers outside `store_postgres.py` name the driver; if it
    drifts from what `pg_driver()` imports, `require_backend` would look for the wrong module."""
    import sys

    from tests.contracts.kinds import PG_DRIVER_MODULE
    from tests.contracts.kinds.store_postgres import pg_driver

    pg_driver()
    assert PG_DRIVER_MODULE in sys.modules


# --- require_backend -------------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("env", "fails"),
    [
        ({}, False),
        ({"HADAVIN_REQUIRE_PG": "1"}, True),
        ({"HADAVIN_REQUIRE_PG": "yes"}, True),
        ({"HADAVIN_REQUIRE_PG": "0"}, False),
        ({"HADAVIN_REQUIRE_PG": ""}, False),
        ({"CI": "true"}, True),
        ({"CI": "1"}, True),
        ({"CI": "false"}, False),
        ({"HADAVIN_REQUIRE_PG": "0", "CI": "true"}, True),
    ],
)
def test_missing_database_fails_under_the_rule_and_skips_otherwise(no_rule, env, fails):
    from tests.contracts.kinds import require_backend

    for name, value in env.items():
        no_rule.setenv(name, value)
    no_rule.delenv("HADAVIN_TEST_PG_DSN", raising=False)
    no_rule.setattr("tests.contracts.kinds.importlib.util.find_spec", lambda name: object())
    kind, msg = _outcome(lambda: require_backend("postgres"))
    assert kind == ("Failed" if fails else "Skipped")
    assert msg.startswith("require_backend: postgres:")


def test_missing_driver_fails_under_the_rule_and_skips_otherwise(no_rule):
    from tests.contracts.kinds import require_backend

    no_rule.setattr("tests.contracts.kinds.importlib.util.find_spec", lambda name: None)
    no_rule.setenv("HADAVIN_TEST_PG_DSN", "postgresql://example.invalid/db")
    kind, msg = _outcome(lambda: require_backend("postgres"))
    assert (kind, "driver" in msg) == ("Skipped", True)
    no_rule.setenv("HADAVIN_REQUIRE_PG", "1")
    kind, _ = _outcome(lambda: require_backend("postgres", dsn=False))
    assert kind == "Failed"


def test_a_present_driver_and_database_return_and_dsn_false_ignores_the_database(no_rule):
    from tests.contracts.kinds import require_backend

    no_rule.setenv("HADAVIN_REQUIRE_PG", "1")
    no_rule.setattr("tests.contracts.kinds.importlib.util.find_spec", lambda name: object())
    no_rule.delenv("HADAVIN_TEST_PG_DSN", raising=False)
    assert _outcome(lambda: require_backend("postgres", dsn=False))[0] == "returned"
    assert _outcome(lambda: require_backend("postgres"))[0] == "Failed"
    no_rule.setenv("HADAVIN_TEST_PG_DSN", "postgresql://example.invalid/db")
    assert _outcome(lambda: require_backend("postgres"))[0] == "returned"
    assert _outcome(lambda: require_backend("sqlite"))[0] == "ValueError"


def test_module_level_skip_passes_allow_module_level(no_rule):
    from tests.contracts.kinds import require_backend

    seen = {}
    no_rule.setattr("tests.contracts.kinds.importlib.util.find_spec", lambda name: None)
    no_rule.setattr(pytest, "skip", lambda reason, **kw: seen.update(kw, reason=reason))
    require_backend("postgres", module_level=True)
    require_backend("postgres")
    assert seen["allow_module_level"] is False  # the last call
    seen.clear()
    require_backend("postgres", module_level=True)
    assert seen["allow_module_level"] is True


# --- the recording proxy ----------------------------------------------------------------------------------------
class _Fake:
    value = 3

    def __init__(self):
        self.calls = 0

    def work(self, x):
        self.calls += 1
        return x * 2

    def _private(self):
        return "p"


def test_proxy_records_public_calls_made_in_a_test_body_only():
    from tests.contracts.store_support import Recorder, RecordingStore

    recorder = Recorder()
    proxy = RecordingStore(_Fake(), "memory", recorder)
    assert proxy.work(2) == 4  # fixture time: not in a body
    assert recorder.called == set()
    recorder.in_body = True
    assert proxy.work(3) == 6
    assert proxy._private() == "p"  # private names pass through unrecorded
    assert proxy.value == 3  # data attributes pass through
    assert recorder.called == {("memory", "work")}


def test_proxy_records_per_backend():
    from tests.contracts.store_support import Recorder, RecordingStore

    recorder = Recorder()
    recorder.in_body = True
    RecordingStore(_Fake(), "postgres", recorder).work(1)
    assert recorder.called == {("postgres", "work")}


# --- the session-end check, on a fake session -------------------------------------------------------------------
def _state(**over):
    from tests.contracts.store_support import SessionState

    items = {}
    ran = set()
    for fn in ("t.py::test_a", "t.py::test_b"):
        for backend in ("memory", "postgres"):
            items[f"{fn}[{backend}]"] = (fn, backend)
            ran.add(f"{fn}[{backend}]")
    base = {
        "fail_rule": True,
        "backends": ("memory", "postgres"),
        "items": items,
        "selected": set(items),
        "ran": ran,
        "called": {(b, m) for b in ("memory", "postgres") for m in ("get_run", "add_cost")},
        "methods": ["get_run", "add_cost"],
    }
    base.update(over)
    return SessionState(**base)


def test_session_check_passes_a_complete_run():
    from tests.contracts.store_support import session_problems

    assert session_problems(_state()) == []


def test_session_check_is_off_without_the_fail_rule_even_when_everything_is_wrong():
    from tests.contracts.store_support import session_problems

    broken = _state(
        fail_rule=False, ran=set(), skip_reasons=["require_backend: postgres: x"], called=set()
    )
    assert session_problems(broken) == []


def test_session_check_is_off_when_no_store_test_is_selected():
    """A `-m perf` run selects none of them (their items are deselected): the check stays silent."""
    from tests.contracts.store_support import session_problems

    assert session_problems(_state(selected=set(), ran=set(), called=set())) == []


def test_session_check_catches_a_silent_backend_skip():
    from tests.contracts.store_support import session_problems

    state = _state(skip_reasons=["require_backend: postgres: HADAVIN_TEST_PG_DSN not set"])
    assert any("skipped silently" in p for p in session_problems(state))


def test_session_check_ignores_a_legitimate_skip_like_test_llm():
    from tests.contracts.store_support import session_problems

    state = _state(
        skip_reasons=["Stubber refuses a malformed Converse shape before the kind sees it"]
    )
    assert session_problems(state) == []


def test_session_check_catches_a_test_that_ran_for_one_backend_only():
    from tests.contracts.store_support import session_problems

    state = _state()
    state.ran.discard("t.py::test_a[postgres]")
    problems = session_problems(state)
    assert problems == ["store test t.py::test_a did not run for backend postgres"]


def test_session_check_fails_a_k_memory_run_by_design():
    """`-k memory`: the postgres items were deselected (so not selected, not run) but they exist."""
    from tests.contracts.store_support import session_problems

    state = _state()
    for fn in ("test_a", "test_b"):
        state.selected.discard(f"t.py::{fn}[postgres]")
        state.ran.discard(f"t.py::{fn}[postgres]")
    assert len(session_problems(state)) == 2


def test_session_check_needs_every_instance_of_a_parametrized_test():
    from tests.contracts.store_support import session_problems

    state = _state()
    for n in (1, 2):
        state.items[f"t.py::test_c[memory-{n}]"] = ("t.py::test_c", "memory")
        state.items[f"t.py::test_c[postgres-{n}]"] = ("t.py::test_c", "postgres")
        state.selected |= {f"t.py::test_c[memory-{n}]", f"t.py::test_c[postgres-{n}]"}
        state.ran |= {f"t.py::test_c[memory-{n}]", f"t.py::test_c[postgres-{n}]"}
    assert session_problems(state) == []
    state.ran.discard("t.py::test_c[postgres-2]")
    assert session_problems(state) == ["store test t.py::test_c did not run for backend postgres"]


def test_session_check_exempts_only_the_named_postgres_only_tests(monkeypatch):
    import tests.contracts.store_support as support

    state = _state()
    state.ran.discard("t.py::test_a[memory]")
    assert len(support.session_problems(state)) == 1
    monkeypatch.setattr(support, "POSTGRES_ONLY_BY_DESIGN", frozenset({"test_a"}))
    assert support.session_problems(state) == []
    state.ran.discard("t.py::test_a[postgres]")  # still needs postgres
    assert len(support.session_problems(state)) == 1


def test_session_check_wants_every_public_method_called_on_every_backend():
    from tests.contracts.store_support import session_problems

    state = _state()
    state.called.discard(("postgres", "add_cost"))
    assert session_problems(state) == ["no test body called Store.add_cost on backend postgres"]


def test_session_check_fails_under_xdist_with_the_rule_and_is_silent_without():
    from tests.contracts.store_support import XDIST_MESSAGE, session_problems

    assert session_problems(_state(xdist=True)) == [XDIST_MESSAGE]
    assert session_problems(_state(xdist=True, fail_rule=False)) == []


def test_public_methods_lists_only_public_callables():
    from tests.contracts.store_support import public_methods

    class P:
        x = 1

        def a(self): ...
        def _b(self): ...

    assert public_methods(P) == ["a"]


# --- the rule, as unit tests (order 101 item 2) -----------------------------------------------------------------
def test_session_check_under_xdist_fails_even_when_the_controller_selected_nothing():
    """The controller of an xdist run collects nothing itself: `selected` is empty there, and that must not
    read as "nothing to check"."""
    from tests.contracts.store_support import XDIST_MESSAGE, session_problems

    controller = _state(xdist=True, selected=set(), items={}, ran=set(), called=set())
    assert session_problems(controller) == [XDIST_MESSAGE]
    assert session_problems(_state(xdist=True, fail_rule=False, selected=set())) == []


def test_a_store_test_known_to_the_state_but_not_selected_is_not_expected_to_run():
    """`-m "not perf"` removes a perf-marked store test for both backends: it must not fail every CI run."""
    from tests.contracts.store_support import session_problems

    state = _state()
    for backend in ("memory", "postgres"):
        state.items[f"t.py::test_perf[{backend}]"] = ("t.py::test_perf", backend)
    assert session_problems(state) == []


def test_one_deselected_instance_of_a_parametrized_store_test_is_not_expected_to_run():
    from tests.contracts.store_support import session_problems

    state = _state()
    for backend in ("memory", "postgres"):
        for n in (1, 2):
            nodeid = f"t.py::test_c[{backend}-{n}]"
            state.items[nodeid] = ("t.py::test_c", backend)
            state.selected.add(nodeid)
            if (
                n == 1
            ):  # instance 2 was deselected after being recorded: it is selected but never ran
                state.ran.add(nodeid)
    assert session_problems(state) == [
        "store test t.py::test_c did not run for backend memory",
        "store test t.py::test_c did not run for backend postgres",
    ]
    for backend in ("memory", "postgres"):  # the same test with instance 2 truly deselected
        gone = f"t.py::test_c[{backend}-2]"
        state.selected.discard(gone)
        del state.items[gone]
    assert session_problems(state) == []


def test_a_selected_store_test_that_skips_itself_fails_the_run_whatever_the_reason():
    """The documented rule: a store test runs on both backends or it is not a store test."""
    from tests.contracts.store_support import session_problems

    state = _state(skip_reasons=["not on this Python"])  # a reason that is not `require_backend:`
    state.ran.discard("t.py::test_a[postgres]")
    assert session_problems(state) == ["store test t.py::test_a did not run for backend postgres"]


def test_xdist_active_reads_the_worker_variable_the_option_and_the_plugin(monkeypatch):
    from types import SimpleNamespace

    from tests.contracts.store_support import xdist_active

    def config(plugin, **option):
        return SimpleNamespace(
            pluginmanager=SimpleNamespace(hasplugin=lambda name: plugin and name == "xdist"),
            option=SimpleNamespace(**option),
        )

    monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)
    assert xdist_active(config(True, numprocesses=2, dist="load"))
    assert xdist_active(config(True, numprocesses=None, dist="loadfile"))
    assert not xdist_active(config(True, numprocesses=0, dist="no"))  # -n 0
    assert not xdist_active(config(True, numprocesses=None, dist="no"))
    assert not xdist_active(config(True))  # options absent
    assert not xdist_active(
        config(False, numprocesses=2, dist="load")
    )  # no plugin: the option is unknown
    monkeypatch.setenv("PYTEST_XDIST_WORKER", "gw0")
    assert xdist_active(config(False))


def test_the_root_conftest_refuses_an_xdist_run_under_the_fail_rule_and_only_then(monkeypatch):
    """The xdist controller never loads `tests/contracts/conftest.py`, so the refusal lives in `tests/conftest.py`
    (real xdist 3.8.0: with the refusal absent the planted defects passed under `-n 2` with exit 0)."""
    from types import SimpleNamespace

    import tests.conftest as root
    from tests.contracts.store_support import XDIST_MESSAGE

    def config(plugin=True, **option):
        return SimpleNamespace(
            pluginmanager=SimpleNamespace(hasplugin=lambda name: plugin and name == "xdist"),
            option=SimpleNamespace(**option),
        )

    for name in RULE_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)
    assert (
        root.pytest_configure(config(numprocesses=2, dist="load")) is None
    )  # no rule: not affected
    monkeypatch.setenv("HADAVIN_REQUIRE_PG", "1")
    with pytest.raises(pytest.UsageError, match="xdist") as caught:
        root.pytest_configure(config(numprocesses=2, dist="load"))
    assert str(caught.value) == XDIST_MESSAGE
    assert root.pytest_configure(config(numprocesses=0, dist="no")) is None  # rule on, no xdist
    monkeypatch.delenv("HADAVIN_REQUIRE_PG")
    monkeypatch.setenv("CI", "true")
    with pytest.raises(pytest.UsageError):
        root.pytest_configure(config(numprocesses=None, dist="loadfile"))


# --- conftest.py wires the hooks (real nested pytests, order 101 item 1) ------------------------------------------
CI_COMMAND = [
    "-q",
    "-m",
    "not live and not perf",
    "-p",
    "no:cacheprovider",
]  # as ci.yml, no file argument
FAKE_KINDS = """
from tests.contracts.kinds import kind


class Fake:
    def __getattr__(self, name):
        return lambda *args, **kwargs: None


for _name in ("alpha", "beta"):
    kind("store", _name)(lambda tmp_path: Fake())
"""
CALLS_EVERYTHING = """
from hadavin_sdk.store.protocol import Store
from tests.contracts.store_support import public_methods


def test_calls_every_method(store):
    for name in public_methods(Store):
        getattr(store, name)()
"""
# touch is called only while a fixture sets up and get_tick_state only while it tears down, never in a body
WITH_DEFECTS = """
import pytest

from hadavin_sdk.store.protocol import Store
from tests.contracts.store_support import public_methods

ONLY_AROUND = ("touch", "get_tick_state")


@pytest.fixture
def noisy(store):
    store.touch()
    yield store
    store.get_tick_state()


def _body(store):
    for name in public_methods(Store):
        if name not in ONLY_AROUND:
            getattr(store, name)()


def test_first(noisy):
    _body(noisy)


def test_second(noisy):
    _body(noisy)


def test_skips_for_beta(store):
    if store.backend == "beta":
        pytest.skip("require_backend: beta: planted silent skip")


@pytest.mark.perf
def test_perf_marked_and_deselected(store):
    raise AssertionError("deselected by -m, must never run")
"""


def _project(tmp_path, test_source):
    """A throw-away project: the real `conftest.py` and `store_support.py` copied verbatim, the kind registry
    module, two fake store kinds, and one test file."""
    proj = tmp_path / "proj"
    contracts = proj / "tests" / "contracts"
    (contracts / "kinds").mkdir(parents=True)
    (proj / "tests" / "__init__.py").write_text("", encoding="utf-8")
    (contracts / "__init__.py").write_text("", encoding="utf-8")
    here = Path(__file__).parent
    for name in ("conftest.py", "store_support.py"):
        (contracts / name).write_text((here / name).read_text(encoding="utf-8"), encoding="utf-8")
    (contracts / "kinds" / "__init__.py").write_text(
        (here / "kinds" / "__init__.py").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (contracts / "kinds" / "fake_store.py").write_text(FAKE_KINDS, encoding="utf-8")
    (contracts / "test_nested.py").write_text(test_source, encoding="utf-8")
    (proj / "pyproject.toml").write_text(
        '[tool.pytest.ini_options]\ntestpaths = ["tests"]\npythonpath = ["."]\n'
        'markers = ["live: x", "perf: y"]\n',
        encoding="utf-8",
    )
    return proj


def _nested(cwd, extra_env, args):
    """Run pytest in `cwd` with a clean environment (the rule variables, xdist and any pytest options of the
    outer run removed)."""
    env = {
        k: v
        for k, v in os.environ.items()
        if k not in RULE_VARS and not k.startswith(("PYTEST_", "HADAVIN_TEST_"))
    }
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(ROOT / "src"), env.get("PYTHONPATH")]))
    env.update(extra_env)
    cmd = [sys.executable, "-m", "pytest", *args]
    return subprocess.run(  # noqa: S603 - our own interpreter and a fixed command
        cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=120, check=False
    )


def test_conftest_fails_a_memory_only_run_under_the_rule_and_not_without_it():
    """With a file argument (the conftest is then loaded before the session starts, the case that always worked)."""
    args = ["tests/contracts/test_store.py", "-q", "-p", "no:cacheprovider"]
    args += ["-k", "memory and test_plan_round_trip"]
    quiet = _nested(ROOT, {}, args)
    assert quiet.returncode == 0, quiet.stdout[-600:]
    assert "session-end check" not in quiet.stdout
    strict = _nested(ROOT, {"HADAVIN_REQUIRE_PG": "1"}, args)
    assert strict.returncode == 1, strict.stdout[-600:]
    assert "contract session-end check FAILED" in strict.stdout
    assert (
        "test_plan_round_trip_replace_and_unknown_is_not_found did not run for backend postgres"
        in (strict.stdout)
    )


def test_a_plain_run_with_no_file_argument_passes_when_every_method_is_called_on_every_backend(
    tmp_path,
):
    """The CI command. A pass proves nothing by itself; the next test proves the checks are alive."""
    proj = _project(tmp_path, CALLS_EVERYTHING)
    for rule in ({"HADAVIN_REQUIRE_PG": "1"}, {"CI": "true"}):
        done = _nested(proj, rule, CI_COMMAND)
        assert done.returncode == 0, done.stdout[-800:]
        assert "session-end check" not in done.stdout


def test_a_plain_run_with_no_file_argument_reports_a_silent_skip_a_missing_test_and_uncalled_methods(
    tmp_path,
):
    """BLOCKER of order 101: a conftest in a directory that does not start with `test` is loaded during
    collection, after `pytest_sessionstart`, so state made there was never made and every check was inert. Also
    the wiring of what counts as "called by a test body": `touch` is called only while a fixture sets up and
    `get_tick_state` only while it tears down, so both must be reported as never called; the lines below are the
    complete list of what the run reports."""
    proj = _project(tmp_path, WITH_DEFECTS)
    strict = _nested(proj, {"HADAVIN_REQUIRE_PG": "1"}, CI_COMMAND)
    out = strict.stdout
    assert strict.returncode == 1, out[-800:]
    assert "contract session-end check FAILED:" in out
    reported = sorted(line.strip() for line in out.splitlines() if line.startswith("  "))
    nodeid = "tests/contracts/test_nested.py::test_skips_for_beta"
    assert reported == sorted(
        [
            "a backend was skipped silently: require_backend: beta: planted silent skip",
            f"store test {proj / nodeid} did not run for backend beta",
            "no test body called Store.get_tick_state on backend alpha",
            "no test body called Store.get_tick_state on backend beta",
            "no test body called Store.touch on backend alpha",
            "no test body called Store.touch on backend beta",
        ]
    ), out
    # the perf-marked store test was deselected by -m: it neither ran nor is reported
    assert "test_perf_marked_and_deselected" not in out


def test_the_same_defects_are_silent_without_the_fail_rule(tmp_path):
    proj = _project(tmp_path, WITH_DEFECTS)
    done = _nested(proj, {}, CI_COMMAND)
    assert done.returncode == 0, done.stdout[-800:]
    assert "session-end check" not in done.stdout


def test_a_run_that_selects_no_store_test_is_silent_under_the_rule(tmp_path):
    proj = _project(tmp_path, WITH_DEFECTS)
    done = _nested(proj, {"HADAVIN_REQUIRE_PG": "1"}, [*CI_COMMAND, "-k", "no_such_test_name"])
    assert done.returncode == 5, done.stdout[-800:]  # nothing collected
    assert "session-end check" not in done.stdout
