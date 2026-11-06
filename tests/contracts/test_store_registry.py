"""P4d-a1: the store kind registry, `require_backend`, the recording proxy and the session-end check.

The session-end check is unit-tested on a fake session (`SessionState`); one test runs a real nested pytest to
prove `conftest.py` wires the hooks. Imports of the new helpers sit inside the tests so that the fail-before test
(which needs only the old `pg_schema`) can run alone against the code before this change."""

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
    no_rule.setenv("CI", "1")
    no_rule.delenv("HADAVIN_TEST_PG_DSN", raising=False)
    pytest.importorskip("psycopg")
    kind, _ = _outcome(lambda: next(pg_schema()))
    assert kind == "Failed", f"expected a failure in CI, got {kind}"


def test_pg_schema_still_skips_on_a_laptop_without_a_database(no_rule):
    no_rule.delenv("HADAVIN_TEST_PG_DSN", raising=False)
    pytest.importorskip("psycopg")
    kind, msg = _outcome(lambda: next(pg_schema()))
    assert kind == "Skipped"
    assert msg.startswith("require_backend:")


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


# --- conftest.py wires the hooks (a real nested pytest) --------------------------------------------------------
def _nested(extra_env):
    env = {k: v for k, v in os.environ.items() if k not in RULE_VARS}
    env.update(extra_env)
    cmd = [
        sys.executable, "-m", "pytest", "tests/contracts/test_store.py", "-q", "-p", "no:cacheprovider",
        "-k", "memory and test_plan_round_trip",
    ]  # fmt: skip
    return subprocess.run(  # noqa: S603 - our own interpreter and a fixed command
        cmd, cwd=ROOT, env=env, capture_output=True, text=True, timeout=120, check=False
    )


def test_conftest_fails_a_memory_only_run_under_the_rule_and_not_without_it():
    quiet = _nested({})
    assert quiet.returncode == 0, quiet.stdout[-600:]
    assert "session-end check" not in quiet.stdout
    strict = _nested({"HADAVIN_REQUIRE_PG": "1"})
    assert strict.returncode == 1, strict.stdout[-600:]
    assert "contract session-end check FAILED" in strict.stdout
    assert (
        "test_plan_round_trip_replace_and_unknown_is_not_found did not run for backend postgres"
        in (strict.stdout)
    )
