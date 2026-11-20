"""Tests of `hadavin_sdk.testing.crash`: the crash points that later tests use to stop a run
half-way.

Case ids (N1..N7, E1..E6, H1..H6, P1) are those of the step E ticket. Everything runs on the memory
store or on plain objects, except P1, which needs HADAVIN_TEST_PG_DSN and is skipped without it. A
child process is always started with a timeout and has ended before its test returns.
"""

from __future__ import annotations

import ast
import inspect
import os
import re
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from hadavin_sdk.llm.protocol import ProviderError
from hadavin_sdk.models import Run, RunState
from hadavin_sdk.store import MemoryStore
from hadavin_sdk.store.protocol import NotFound
from hadavin_sdk.testing import crash as crash_mod
from hadavin_sdk.testing.crash import CRASH_EXIT_CODE, CRASH_MARKER, CrashPoints, SimulatedCrash
from tests.contracts.kinds.store_postgres import pg_schema
from tests.k5_support import ScriptLLM, build_runtime, handle, k5_cfg

PACKAGE = Path(__file__).resolve().parents[1] / "src" / "hadavin_sdk"
CRASH_FILE = PACKAGE / "testing" / "crash.py"
GATE = "PYTEST_CURRENT_TEST"
RID = "run-" + "ab12" * 8
POINT = "thing.step:before"
CHILD_TIMEOUT_S = 60

CHILD_HEAD = """
import atexit, os, sys, threading
from pathlib import Path
from hadavin_sdk.testing.crash import CrashPoints

class Thing:
    def step(self):
        return "done"

atexit.register(lambda: print("atexit ran", flush=True))
points = CrashPoints(mode="exit", flag_path=Path(sys.argv[1]))
thing = points.wrap(Thing(), "thing", ["step"])
"""
CHILD_ONE = (
    CHILD_HEAD
    + """
try:
    print("start", flush=True)
    thing.step()
    print("survived", flush=True)
finally:
    print("finally ran", flush=True)
"""
)
CHILD_THREADS = (
    CHILD_HEAD
    + """
gate = threading.Barrier(2)

def go():
    gate.wait(timeout=20)
    thing.step()

threads = [threading.Thread(target=go) for _ in range(2)]
for t in threads:
    t.start()
for t in threads:
    t.join(timeout=30)
print("survived", flush=True)
"""
)
CHILD_PG = """
import os, sys
from pathlib import Path
from hadavin_sdk.models import Run
from hadavin_sdk.store.postgres import PostgresStore, connect
from hadavin_sdk.testing.crash import CrashPoints

points = CrashPoints(mode="exit", flag_path=Path(sys.argv[1]))
store = points.wrap(PostgresStore(connect(os.environ["CRASH_CHILD_DSN"])), "store", ["create_run"])
store.create_run(Run(run_id=sys.argv[2], agent_id="test-agent", principal_id="svc:test-agent",
                     trigger_kind="event", trigger_ref="t"))
print("survived", flush=True)
"""


class Thing:
    """A plain target: counts its calls, can fail on request."""

    label = "plain"

    def __init__(self) -> None:
        self.calls = 0

    def step(self, fail: bool = False) -> int:
        self.calls += 1
        if fail:
            raise KeyError("own failure")
        return self.calls

    def other(self) -> str:
        return "other"


class Killed(BaseException):
    """Stands for the end of the process in the tests that must not really end this one."""


@pytest.fixture
def no_real_exit(monkeypatch):
    """Kill mode inside the pytest process: the exit call raises `Killed` instead of ending
    pytest."""

    def fake(code):
        raise Killed(code)

    monkeypatch.setattr(crash_mod.os, "_exit", fake)


def new_run(run_id: str = RID) -> Run:
    return Run(
        run_id=run_id,
        agent_id="test-agent",
        principal_id="svc:test-agent",
        trigger_kind="event",
        trigger_ref="t",
    )


def start_child(tmp_path: Path, source: str, flag: Path, *args: str, env: dict | None = None):
    script = tmp_path / "child.py"
    script.write_text(source, encoding="utf-8")
    return subprocess.run(  # noqa: S603 - this interpreter, a script written by this test, no shell
        [sys.executable, str(script), str(flag), *args],
        capture_output=True,
        check=False,
        text=True,
        timeout=CHILD_TIMEOUT_S,
        env=env,
    )


# --- normal ---------------------------------------------------------------------------------------


def test_n1_unarmed_wrap_behaves_as_the_target():
    """N1: an unarmed wrap of a MemoryStore gives the same run as the bare store; nothing fired."""
    plain, inner = MemoryStore(), MemoryStore()
    with CrashPoints() as cp:
        store = cp.wrap(inner, "store", ["create_run", "get_run"])
        run = new_run()
        plain.create_run(run)
        assert store.create_run(run) is None
        assert store.get_run(RID) == plain.get_run(RID) == run
        assert cp.fired == () and cp.armed() is None


def test_n2_before_crashes_and_nothing_was_written():
    """N2: armed `:before`, the call crashes and the store holds no run."""
    inner = MemoryStore()
    with CrashPoints() as cp:
        store = cp.wrap(inner, "store", ["create_run"])
        cp.arm("store.create_run:before")
        assert cp.armed() == "store.create_run:before"
        with pytest.raises(SimulatedCrash) as caught:
            store.create_run(new_run())
        assert caught.value.point == "store.create_run:before"
        with pytest.raises(NotFound):
            inner.get_run(RID)
        assert cp.fired == ("store.create_run:before",) and cp.armed() is None


def test_n3_after_crashes_and_the_write_is_there():
    """N3: armed `:after`, the call crashes and the run is in the store."""
    inner = MemoryStore()
    with CrashPoints() as cp:
        store = cp.wrap(inner, "store", ["create_run"])
        cp.arm("store.create_run:after")
        with pytest.raises(SimulatedCrash) as caught:
            store.create_run(new_run())
        assert caught.value.point == "store.create_run:after"
        assert inner.get_run(RID).run_id == RID
        assert cp.fired == ("store.create_run:after",)


def test_n4_one_arm_gives_one_crash():
    """N4: the second call of the same method passes; `fired` has one entry."""
    target = Thing()
    with CrashPoints() as cp:
        thing = cp.wrap(target, "thing", ["step"])
        cp.arm(POINT)
        with pytest.raises(SimulatedCrash):
            thing.step()
        assert thing.step() == 1 and thing.step() == 2
        assert cp.fired == (POINT,) and cp.armed() is None


def test_n5_nth_two_lets_the_first_call_pass():
    """N5: with nth=2 the first call passes and the second crashes."""
    target = Thing()
    with CrashPoints() as cp:
        thing = cp.wrap(target, "thing", ["step"])
        cp.arm("thing.step:after", nth=2)
        assert thing.step() == 1
        assert cp.armed() == "thing.step:after" and cp.fired == ()
        with pytest.raises(SimulatedCrash):
            thing.step()
        assert target.calls == 2 and thing.step() == 3


def test_n6_crash_before_the_model_call_leaves_the_run_working(tmp_path):
    """N6: through the real runtime the run stays WORKING, and a handler for `Exception` does not
    see the crash. An ordinary model error, for contrast, is tidied up into NEEDS_PERSON."""
    assert issubclass(SimulatedCrash, BaseException) and not issubclass(SimulatedCrash, Exception)
    store, llm = MemoryStore(), ScriptLLM([{"noaction": True}])
    with CrashPoints() as cp:
        rt, _ = build_runtime(k5_cfg(tmp_path), cp.wrap(llm, "llm", ["chat"]), store=store)
        cp.arm("llm.chat:before")
        with pytest.raises(SimulatedCrash):
            try:
                handle(rt, run_id=RID)
            except Exception:  # noqa: BLE001 - the point of the test: this must not catch the crash
                pytest.fail("an `except Exception` caught the simulated crash")
        assert cp.fired == ("llm.chat:before",)
    assert store.get_run(RID).state is RunState.WORKING
    assert llm.sent == []

    class Refusing:
        def chat(self, *args, **kwargs):
            raise ProviderError("refused")

    other = MemoryStore()
    rt, _ = build_runtime(k5_cfg(tmp_path / "plain"), Refusing(), store=other)
    assert handle(rt, run_id=RID).state is RunState.NEEDS_PERSON


def test_n6_store_wrapped_after_the_build_crashes_after_the_first_transition(tmp_path):
    """N6 (usage 2): the store is wrapped on the built runtime; the crash after the first
    transition leaves the run WORKING with no model call."""
    store, llm = MemoryStore(), ScriptLLM([{"noaction": True}])
    with CrashPoints() as cp:
        rt, _ = build_runtime(k5_cfg(tmp_path), llm, store=store)
        rt.store = cp.wrap(rt.store, "store", ["create_run", "transition"])
        cp.arm("store.transition:after", nth=1)
        with pytest.raises(SimulatedCrash):
            handle(rt, run_id=RID)
    assert store.get_run(RID).state is RunState.WORKING
    assert llm.sent == []


def test_n7_kill_mode_ends_a_child_process_once(tmp_path):
    """N7: the armed child exits with the crash code and the marker, runs no `finally` and no exit
    handler, and the flag is gone; started again it ends normally. Also pins that a child inherits
    the pytest variable."""
    assert GATE in os.environ
    flag = tmp_path / "flag"
    arming = CrashPoints(mode="exit", flag_path=flag)
    arming.arm(POINT)
    assert flag.read_text(encoding="utf-8") == POINT and arming.armed() == POINT
    done = start_child(tmp_path, CHILD_ONE, flag)
    assert done.returncode == CRASH_EXIT_CODE, done.stderr
    assert done.stdout.splitlines() == ["start", CRASH_MARKER]
    assert not flag.exists() and arming.armed() is None
    again = start_child(tmp_path, CHILD_ONE, flag)
    assert again.returncode == 0, again.stderr
    assert again.stdout.splitlines() == ["start", "survived", "finally ran", "atexit ran"]


CHILD_CLOSED_STDOUT = (
    CHILD_HEAD
    + """
os.close(1)  # the parent's end of the pipe is gone, or stdout was closed: the marker cannot be written
try:
    thing.step()
    os.write(2, b"survived\\n")
finally:
    os.write(2, b"finally ran\\n")
"""
)


def test_n7_kill_mode_still_exits_with_the_crash_code_when_the_marker_cannot_be_written(tmp_path):
    """A closed stdout: the flag is deleted before the marker is printed. If the print fails,
    the child must still end with the crash code and run no `finally`: not go on as an ordinary
    exception inside the code under test, with the flag already gone."""
    flag = tmp_path / "flag"
    CrashPoints(mode="exit", flag_path=flag).arm(POINT)
    done = start_child(tmp_path, CHILD_CLOSED_STDOUT, flag)
    assert done.returncode == CRASH_EXIT_CODE, (done.returncode, done.stderr)
    assert done.stdout == "" and not flag.exists()
    assert "survived" not in done.stderr and "finally ran" not in done.stderr


def test_the_module_text_holds_the_phrases_cp_fired_marker_and_exit_code():
    """Checks that the module text contains the phrases `cp.fired`, `marker` and `exit code`; it does not judge the
    sentences around them."""
    text = " ".join((crash_mod.__doc__ or "").split())
    assert "cp.fired" in text
    assert "marker" in text
    assert "exit code" in text


def test_f2_the_constants_are_the_ones_other_tests_assert_against():
    """F2: kills a changed exit code or marker text (a changed constant would still match itself in
    every other test)."""
    assert CRASH_EXIT_CODE == 137
    assert CRASH_MARKER == "simulate crash"


CHILD_BUFFERED = (
    CHILD_HEAD
    + """
print("start", flush=True)
sys.stdout.write("buffered")  # no flush: a real crash loses it
thing.step()
print("survived", flush=True)
"""
)


def test_f3_text_still_buffered_in_the_child_is_lost_but_the_marker_is_there(tmp_path):
    """F3 / invariant 7: nothing buffered is written by the crash; the marker still is."""
    flag = tmp_path / "flag"
    CrashPoints(mode="exit", flag_path=flag).arm(POINT)
    env = {k: v for k, v in os.environ.items() if k != "PYTHONUNBUFFERED"}  # stdout must buffer
    done = start_child(tmp_path, CHILD_BUFFERED, flag, env=env)
    assert done.returncode == CRASH_EXIT_CODE, done.stderr
    assert "buffered" not in done.stdout
    assert done.stdout.splitlines() == ["start", CRASH_MARKER]


def test_n7_kill_mode_counts_the_nth_call_from_the_flag(tmp_path, no_real_exit, capfd):
    """N7 (flag format): `<point>#<nth>` is written by arm and counted by hit; the marker is
    printed once."""
    flag = tmp_path / "flag"
    cp = CrashPoints(mode="exit", flag_path=flag)
    thing = cp.wrap(Thing(), "thing", ["step"])
    cp.arm("thing.step:after", nth=2)
    assert flag.read_text(encoding="utf-8") == "thing.step:after#2"
    assert thing.step() == 1 and flag.exists()
    with pytest.raises(Killed) as killed:
        thing.step()
    assert killed.value.args == (CRASH_EXIT_CODE,) and not flag.exists()
    assert capfd.readouterr().out == CRASH_MARKER + "\n"
    assert thing.step() == 3


# --- edge -----------------------------------------------------------------------------------------


def test_e1_everything_not_listed_is_the_targets():
    """E1: an unlisted method and a plain attribute pass through; a missing attribute is missing."""
    target = Thing()
    with CrashPoints() as cp:
        thing = cp.wrap(target, "thing", ["step"])
        cp.arm("thing.step:before")
        assert thing.other() == "other" and thing.other == target.other
        assert thing.label == "plain" and thing.calls == 0
        assert getattr(thing, "nope", None) is None
        with pytest.raises(AttributeError):
            thing.nope  # noqa: B018 - the access is the test
        assert cp.fired == ()
        with pytest.raises(SimulatedCrash):
            thing.step()


def test_e2_the_targets_own_error_passes_and_after_does_not_fire():
    """E2: the target's exception comes out unchanged and `:after` stays armed for the next good
    call."""
    target = Thing()
    with CrashPoints() as cp:
        thing = cp.wrap(target, "thing", ["step"])
        cp.arm("thing.step:after")
        with pytest.raises(KeyError, match="own failure"):
            thing.step(fail=True)
        assert cp.fired == () and cp.armed() == "thing.step:after"
        with pytest.raises(SimulatedCrash):
            thing.step()
        assert target.calls == 2


def test_e3_two_threads_at_once_give_one_crash():
    """E3 (same process): two threads reach the armed point together, exactly one crashes."""
    target, gate, crashed, passed = Thing(), threading.Barrier(2), [], []
    with CrashPoints() as cp:
        thing = cp.wrap(target, "thing", ["step"])
        cp.arm(POINT)

        def go():
            gate.wait(timeout=20)
            try:
                passed.append(thing.step())
            except SimulatedCrash as exc:
                crashed.append(exc.point)

        threads = [threading.Thread(target=go) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)
        assert not any(t.is_alive() for t in threads)
        assert crashed == [POINT] and len(passed) == 1 and cp.fired == (POINT,)


def test_e3_two_child_threads_and_one_flag_give_one_kill(tmp_path):
    """E3 (kill mode): two threads of one child and one flag: one kill, one marker."""
    flag = tmp_path / "flag"
    CrashPoints(mode="exit", flag_path=flag).arm(POINT)
    done = start_child(tmp_path, CHILD_THREADS, flag)
    assert done.returncode == CRASH_EXIT_CODE, done.stderr
    assert done.stdout.count(CRASH_MARKER) == 1 and "survived" not in done.stdout
    assert not flag.exists()


def test_e3_a_simulated_flag_taken_by_someone_else_means_no_crash(tmp_path, no_real_exit, monkeypatch):
    """E3 / invariant 5: if the flag cannot be deleted (another process took it), nothing fires. The race is
    simulated: `Path.unlink` is patched to raise FileNotFoundError."""
    flag = tmp_path / "flag"
    cp = CrashPoints(mode="exit", flag_path=flag)
    thing = cp.wrap(Thing(), "thing", ["step"])
    cp.arm(POINT)

    def gone(self, *args, **kwargs):
        raise FileNotFoundError(str(self))

    monkeypatch.setattr(Path, "unlink", gone)
    assert thing.step() == 1 and cp.fired == ()
    monkeypatch.undo()
    flag.unlink()


def test_e4_a_crash_in_a_pool_task_lands_in_the_future():
    """E4: SimulatedCrash raised inside a ThreadPoolExecutor task is kept by the future; the pool
    works on."""
    with CrashPoints() as cp, ThreadPoolExecutor(max_workers=1) as pool:
        thing = cp.wrap(Thing(), "thing", ["step"])
        cp.arm(POINT)
        future = pool.submit(thing.step)
        assert isinstance(future.exception(timeout=30), SimulatedCrash)
        with pytest.raises(SimulatedCrash):
            future.result(timeout=30)
        assert pool.submit(thing.step).result(timeout=30) == 1


def test_e5_arming_twice_without_a_hit_is_refused(tmp_path):
    """E5: a second arm while one is pending raises ValueError, in both modes; the first arm
    stays."""
    with CrashPoints() as cp:
        thing = cp.wrap(Thing(), "thing", ["step"])
        cp.arm(POINT)
        with pytest.raises(ValueError, match="already armed"):
            cp.arm("thing.step:after")
        with pytest.raises(SimulatedCrash):
            thing.step()
        cp.arm("thing.step:after")  # armed again after the hit: allowed
        with pytest.raises(SimulatedCrash):
            thing.step()
    flag = tmp_path / "flag"
    with pytest.raises(RuntimeError), CrashPoints(mode="exit", flag_path=flag) as kill:
        kill.arm(POINT)
        with pytest.raises(ValueError, match="already armed"):
            kill.arm(POINT)
    assert not flag.exists()


@pytest.mark.parametrize("content", [None, b"", b"\n", b"garbage", b"\xff\xfe\x00", b"a\nb\n"])
def test_e6_a_missing_empty_or_garbage_flag_never_fires(tmp_path, no_real_exit, content):
    """E6: kill mode with a missing, empty or garbage flag file: no crash, no error, the file is
    left alone."""
    flag = tmp_path / "flag"
    if content is not None:
        flag.write_bytes(content)
    with CrashPoints(mode="exit", flag_path=flag) as cp:
        thing = cp.wrap(Thing(), "thing", ["step"])
        assert thing.step() == 1 and thing.step() == 2
        assert cp.armed() is None and cp.fired == ()
    assert flag.exists() is (content is not None)


@pytest.mark.parametrize(
    "content",
    ["thing.other:before", POINT + "#0", POINT + "#-1", POINT + "#x", POINT + "#", POINT + "#01"],
)
def test_e6_a_flag_with_another_point_or_a_bad_count_never_fires(tmp_path, no_real_exit, content):
    """Kill mode, a flag holding another point or a bad count (zero, negative, letter, empty, a
    leading zero): no crash, no error inside the code under test, the file is left alone. The
    counts fail if the count pattern allowed a zero first or if the `#` check were dropped."""
    flag = tmp_path / "flag"
    flag.write_text(content, encoding="utf-8")
    cp = CrashPoints(mode="exit", flag_path=flag)  # no `with`: leaving it would delete the flag
    thing = cp.wrap(Thing(), "thing", ["step"])
    assert thing.step() == 1 and thing.step() == 2 and cp.fired == ()
    assert cp.armed() == (content if content == "thing.other:before" else None)
    assert flag.read_text(encoding="utf-8") == content


def test_e6_a_directory_as_flag_never_fires(tmp_path, no_real_exit):
    """E6: an unreadable flag (a directory at that path) means not armed."""
    with CrashPoints(mode="exit", flag_path=tmp_path) as cp:
        assert cp.wrap(Thing(), "thing", ["step"]).step() == 1 and cp.armed() is None


# --- hostile --------------------------------------------------------------------------------------


def test_h1_cannot_be_built_outside_a_pytest_run(tmp_path, monkeypatch):
    """H1: without the pytest variable the constructor raises, in both modes."""
    monkeypatch.delenv(GATE)
    with pytest.raises(RuntimeError, match="pytest"):
        CrashPoints()
    with pytest.raises(RuntimeError, match="pytest"):
        CrashPoints(mode="exit", flag_path=tmp_path / "flag")


def test_h1_a_child_without_the_pytest_variable_cannot_kill_itself(tmp_path):
    """H1: a child started with the variable stripped fails at the constructor; the armed flag
    stays."""
    flag = tmp_path / "flag"
    arming = CrashPoints(mode="exit", flag_path=flag)
    arming.arm(POINT)
    env = {k: v for k, v in os.environ.items() if k != GATE}
    done = start_child(tmp_path, CHILD_ONE, flag, env=env)
    assert done.returncode not in (0, CRASH_EXIT_CODE)
    assert "RuntimeError" in done.stderr and CRASH_MARKER not in done.stdout
    assert "start" not in done.stdout and flag.read_text(encoding="utf-8") == POINT
    flag.unlink()


def test_h2_left_armed_is_an_error_and_is_disarmed(tmp_path, no_real_exit):
    """H2: leaving the block armed raises RuntimeError naming the point; the point is dead
    afterwards; in kill mode the flag file is deleted. An error already in flight is not
    replaced."""
    target = Thing()
    with pytest.raises(RuntimeError, match="thing.step:before"), CrashPoints() as cp:
        thing = cp.wrap(target, "thing", ["step"])
        cp.arm(POINT)
    assert cp.armed() is None
    assert thing.step() == 1 and cp.fired == ()

    flag = tmp_path / "flag"
    with (
        pytest.raises(RuntimeError, match="thing.step:after"),
        CrashPoints(mode="exit", flag_path=flag) as kill,
    ):
        wrapped = kill.wrap(target, "thing", ["step"])
        kill.arm("thing.step:after")
        assert flag.exists()
    assert not flag.exists() and kill.armed() is None
    assert wrapped.step() == 2

    with pytest.raises(KeyError), CrashPoints() as third:
        third.arm(POINT)
        raise KeyError("in flight")
    assert third.armed() is None


class Counted:
    """A target whose call count is safe to read after a burst of threads (list append is atomic)."""

    def __init__(self) -> None:
        self.log: list[int] = []

    def step(self) -> int:
        self.log.append(1)
        return len(self.log)


class Gen:
    def count(self):
        yield 1

    async def fetch(self):
        return 1

    async def stream(self):
        yield 1

    def plain(self):
        return 1


def test_f9_a_flag_that_cannot_be_deleted_is_an_error_naming_the_path(tmp_path, monkeypatch):
    """F9: leaving the block, if the flag file is still there after the delete, raises RuntimeError
    naming the path (not the flag text); with an error in flight the error is not replaced."""
    flag = tmp_path / "flag"
    monkeypatch.setattr(Path, "unlink", lambda self, *a, **k: None)
    with (
        pytest.raises(RuntimeError, match="could not be deleted") as caught,
        CrashPoints(mode="exit", flag_path=flag) as cp,
    ):
        cp.arm(POINT)
    assert str(flag) in str(caught.value) and POINT not in str(caught.value)
    os.unlink(flag)  # the patched Path.unlink does nothing
    with pytest.raises(KeyError), CrashPoints(mode="exit", flag_path=flag) as cp:
        cp.arm(POINT)
        raise KeyError("in flight")
    monkeypatch.undo()
    flag.unlink()


def stub_unlink(monkeypatch, tmp_path, refusals):
    """Path.unlink refuses `refusals` times (None: always) with PermissionError, then works.
    Sleeping is recorded, not done. Returns the call counter and the pauses."""
    real, calls, pauses = Path.unlink, [], []
    monkeypatch.setattr(crash_mod.time, "sleep", pauses.append)

    def flaky(self, *args, **kwargs):
        calls.append(1)
        if refusals is None or len(calls) <= refusals:
            raise PermissionError("held open")
        real(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", flaky)
    return calls, pauses, lambda: monkeypatch.setattr(Path, "unlink", real)


def test_the_unlink_retry_is_20_tries_at_20_ms():
    assert crash_mod._UNLINK_TRIES == 20
    assert crash_mod._UNLINK_PAUSE_S == 0.02


def test_a_delete_refused_for_every_try_but_the_last_works_without_error(tmp_path, monkeypatch):
    """Leaving the block: the delete is refused for every try but the last; the number of calls is
    the tries constant and the only error is the usual 'never fired'."""
    flag = tmp_path / "flag"
    calls, pauses, restore = stub_unlink(monkeypatch, tmp_path, crash_mod._UNLINK_TRIES - 1)
    with (
        pytest.raises(RuntimeError, match="never fired"),
        CrashPoints(mode="exit", flag_path=flag) as cp,
    ):
        cp.arm(POINT)
    restore()
    assert len(calls) == crash_mod._UNLINK_TRIES and not flag.exists()
    assert pauses == [crash_mod._UNLINK_PAUSE_S] * (crash_mod._UNLINK_TRIES - 1)


def test_a_delete_refused_every_time_is_tried_the_tries_constant_then_named(tmp_path, monkeypatch):
    """Leaving the block: every try refused; the calls equal the tries constant and the error names
    the path."""
    flag = tmp_path / "flag"
    calls, _, restore = stub_unlink(monkeypatch, tmp_path, None)
    with (
        pytest.raises(RuntimeError, match="could not be deleted") as caught,
        CrashPoints(mode="exit", flag_path=flag) as cp,
    ):
        cp.arm(POINT)
    restore()
    assert len(calls) == crash_mod._UNLINK_TRIES and str(flag) in str(caught.value)
    flag.unlink()


def test_hit_retries_a_refused_delete_and_crashes_at_this_call(tmp_path, no_real_exit, monkeypatch):
    """A delete refused twice inside `hit` (a reader holds the file): the crash happens at THIS
    call, once, and the flag is gone."""
    flag = tmp_path / "flag"
    cp = CrashPoints(mode="exit", flag_path=flag)
    thing = cp.wrap(Thing(), "thing", ["step"])
    cp.arm(POINT)
    calls, _, restore = stub_unlink(monkeypatch, tmp_path, 2)
    with pytest.raises(Killed):
        thing.step()
    restore()
    assert len(calls) == 3 and not flag.exists() and cp.fired == (POINT,)
    assert thing.step() == 1  # the flag is gone: one arm, one crash


def test_hit_with_a_delete_refused_every_time_does_not_crash_and_leaves_the_flag(
    tmp_path, no_real_exit, monkeypatch
):
    """A delete refused on every try inside `hit`: no crash at this call, no exception in the code
    under test, the flag stays, the tries are the tries constant."""
    flag = tmp_path / "flag"
    cp = CrashPoints(mode="exit", flag_path=flag)
    thing = cp.wrap(Thing(), "thing", ["step"])
    cp.arm(POINT)
    calls, _, restore = stub_unlink(monkeypatch, tmp_path, None)
    assert thing.step() == 1 and cp.fired == ()
    restore()
    assert len(calls) == crash_mod._UNLINK_TRIES and flag.read_text(encoding="utf-8") == POINT
    with pytest.raises(Killed):  # the next matching call tries again and now crashes
        thing.step()
    assert not flag.exists()


def test_the_flag_path_must_be_a_path(tmp_path):
    """A str flag path is refused at the constructor, in both modes."""
    with pytest.raises(TypeError, match="flag_path"):
        CrashPoints(mode="exit", flag_path=str(tmp_path / "flag"))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="flag_path"):
        CrashPoints(flag_path=str(tmp_path / "flag"))  # type: ignore[arg-type]


def test_the_proxy_call_shows_the_targets_name_and_signature():
    """`wraps`: the method seen through the proxy has the target method's name and signature."""
    target = Thing()
    with CrashPoints() as cp:
        proxy = cp.wrap(target, "thing", ["step"])
        assert proxy.step.__name__ == target.step.__name__ == "step"
        assert inspect.signature(proxy.step) == inspect.signature(target.step)


BAD_POINTS = {
    "empty": "",
    "upper-name": "Thing.step:before",
    "upper-method": "thing.Step:before",
    "upper-edge": "thing.step:BEFORE",
    "no-edge": "thing.step",
    "unknown-edge": "thing.step:during",
    "no-method": "thing:before",
    "path": "a/b.step:before",
    "dots": "...:before",
    "newline-after": "thing.step:before\n",
    "newline-before": "\nthing.step:before",
    "hash-in-point": "thing.step:before#2",
    "hash-in-name": "thing#2.step:before",
    "too-many-parts": "thing.step.more:before",
    "digit-first": "1thing.step:before",
    "space": "thing.st ep:before",
    "300-chars-name": "t" * 300 + ".step:before",
    "300-chars-method": "thing." + "s" * 300 + ":before",
    "none": None,
    "bytes": b"thing.step:before",
}
BAD_NTH = {"zero": 0, "negative": -1, "huge": 10**9, "float": 1.0, "string": "2", "none": None}
BAD_NTH |= {"true": True, "false": False}
# (id, error, text the message has, what to do with the CrashPoints `cp` and the flag path `flag`)
WRAP = lambda target, name, methods: lambda cp, flag: cp.wrap(target, name, methods)
REFUSED = [
    *(
        pytest.param(ValueError, "point", lambda cp, f, v=v: cp.arm(v), id=f"point-{k}")
        for k, v in BAD_POINTS.items()
    ),
    *(
        pytest.param(
            (TypeError, ValueError), "nth", lambda cp, f, v=v: cp.arm(POINT, nth=v), id=f"nth-{k}"
        )
        for k, v in BAD_NTH.items()
    ),
    *(
        pytest.param(ValueError, "bad name", WRAP(Thing(), n, ["step"]), id=f"wrap-name-{i}")
        for i, n in enumerate(["", "Thing", "a.b", "a:b", "a#b", "a\n", "t" * 300])
    ),
    *(
        pytest.param(ValueError, "bad method", WRAP(Thing(), "t", [m]), id=f"wrap-method-{i}")
        for i, m in enumerate(["", "Step", "__init__\n", "st.ep", "step#1"])
    ),
    pytest.param(AttributeError, "nope", WRAP(Thing(), "t", ["step", "nope"]), id="wrap-missing"),
    pytest.param(TypeError, "not a method", WRAP(Thing(), "t", ["label"]), id="wrap-attribute"),
    pytest.param(TypeError, "collection", WRAP(Thing(), "t", "step"), id="wrap-string-as-methods"),
    pytest.param(TypeError, "count", WRAP(Gen(), "g", ["count"]), id="wrap-generator"),
    pytest.param(TypeError, "fetch", WRAP(Gen(), "g", ["fetch"]), id="wrap-coroutine"),
    pytest.param(TypeError, "stream", WRAP(Gen(), "g", ["stream"]), id="wrap-async-generator"),
    pytest.param(TypeError, "__len__", WRAP([1], "box", ["__len__"]), id="wrap-dunder"),
    pytest.param(TypeError, "__call__", WRAP(print, "fn", ["__call__"]), id="wrap-dunder-call"),
    pytest.param(
        ValueError, "flag_path", lambda cp, f: CrashPoints(mode="exit"), id="exit-no-flag"
    ),
    pytest.param(ValueError, "flag_path", lambda cp, f: CrashPoints(flag_path=f), id="raise-flag"),
    pytest.param(
        ValueError, "mode", lambda cp, f: CrashPoints(mode="kill", flag_path=f), id="mode"
    ),
]


@pytest.mark.parametrize(("exc", "match", "act"), REFUSED)
def test_h3_bad_input_is_refused_and_nothing_is_armed_or_written(tmp_path, exc, match, act):
    """H3, E5, E6, F6, F9: bad point or name, nth below 1 or not a whole number (a bool too), a
    dunder, async or generator method, one string as the methods, a wrong mode and flag pairing."""
    flag = tmp_path / "flag"
    cp = CrashPoints(mode="exit", flag_path=flag)
    with pytest.raises(exc, match=match):
        act(cp, flag)
    assert cp.armed() is None and not flag.exists()


def crash_importers(package: Path) -> list[str]:
    """Files of the package, outside its `testing` folder, that import the crash module."""
    found = []
    for path in sorted(package.rglob("*.py")):
        if package / "testing" in path.parents:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else []
            if isinstance(node, ast.ImportFrom):
                names = [node.module or ""] + [f"{node.module}.{a.name}" for a in node.names]
            if any(n.startswith("hadavin_sdk.testing.crash") for n in names):
                found.append(path.relative_to(package).as_posix())
    return sorted(set(found))


def test_h5_no_runtime_module_imports_the_crash_helper(tmp_path):
    """H5: invariant 2 as a class test, over the real package; the scan is shown to catch planted
    files."""
    assert crash_importers(PACKAGE) == []
    assert len(list(PACKAGE.rglob("*.py"))) > 20  # the scan looked at the real tree
    fake = tmp_path / "hadavin_sdk"
    (fake / "testing").mkdir(parents=True)
    (fake / "runtime").mkdir()
    (fake / "testing" / "own.py").write_text("import hadavin_sdk.testing.crash\n", encoding="utf-8")
    (fake / "clean.py").write_text("from hadavin_sdk.testing import mutation\n", encoding="utf-8")
    planted = {
        "a.py": "import hadavin_sdk.testing.crash\n",
        "b.py": "from hadavin_sdk.testing.crash import CrashPoints\n",
        "c.py": "from hadavin_sdk.testing import crash\n",
        "runtime/d.py": "def f():\n    import hadavin_sdk.testing.crash as c\n    return c\n",
    }
    for name, text in planted.items():
        (fake / name).write_text(text, encoding="utf-8")
    assert crash_importers(fake) == sorted(planted)


def test_h6_the_helper_file_keeps_its_own_rules():
    """H6: invariants 10 and 11 on our own file: no `chat` or `apply_guardrail` attribute call, no
    URL or host shaped text, standard library imports only, no assert, no dynamic import."""
    tree = ast.parse(CRASH_FILE.read_text(encoding="utf-8"))
    nodes = list(ast.walk(tree))
    called = {
        n.func.attr for n in nodes if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
    }
    assert not called & {"chat", "apply_guardrail", "import_module"}
    plain_calls = {
        n.func.id for n in nodes if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    }
    assert "__import__" not in plain_calls
    shaped = re.compile(
        r"https?://|www\.|\b[a-z0-9-]+\.(?:com|net|org|io|dev|ai|cloud|internal|local)\b",
        re.IGNORECASE,
    )
    texts = [n.value for n in nodes if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    assert len(texts) > 10 and [t for t in texts if shaped.search(t)] == []
    imported = set()
    for n in nodes:
        if isinstance(n, ast.Import):
            imported |= {a.name.split(".")[0] for a in n.names}
        if isinstance(n, ast.ImportFrom):
            assert n.level == 0
            imported.add((n.module or "").split(".")[0])
    assert imported == {
        "__future__",
        "functools",
        "inspect",
        "os",
        "re",
        "threading",
        "time",
        "collections",
        "pathlib",
        "typing",
    }
    assert imported - {"__future__"} <= sys.stdlib_module_names
    assert not any(isinstance(n, ast.Assert) for n in nodes)


# --- review fixes F2 to F9 -----------------------------------------------------------------------


def test_f2_arming_the_same_point_again_counts_from_the_start():
    """F2: after a point fired, arm it again with nth=2 on the same object: the first call passes,
    the second crashes. (Without the reset of the call count the first call would crash.)"""
    target = Thing()
    with CrashPoints() as cp:
        thing = cp.wrap(target, "thing", ["step"])
        cp.arm(POINT)
        with pytest.raises(SimulatedCrash):
            thing.step()
        cp.arm(POINT, nth=2)
        assert thing.step() == 1
        with pytest.raises(SimulatedCrash):
            thing.step()
        assert cp.fired == (POINT, POINT)


@pytest.mark.parametrize("nth", [1, 2, 3])
def test_f2_nth_is_exact_never_earlier_never_later(nth):
    """F2: with nth=k the calls 1..k-1 pass and call k crashes (kills `<` turned into `<=`)."""
    target = Thing()
    with CrashPoints() as cp:
        thing = cp.wrap(target, "thing", ["step"])
        cp.arm(POINT, nth=nth)
        for call in range(1, nth):
            assert thing.step() == call and cp.fired == ()
        with pytest.raises(SimulatedCrash):
            thing.step()
        assert cp.fired == (POINT,) and target.calls == nth - 1  # `:before`: the body did not run


def test_f2_many_threads_released_together_give_exactly_one_crash_each_time():
    """F2: a burst of threads, released together by a barrier, calls one armed point on a counted
    target; in every one of the bursts exactly one raises and the others reach the target."""
    threads_per_burst, bursts = 12, 300
    old = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)  # make a thread switch inside the helper likely
    try:
        with CrashPoints() as cp:
            target = Counted()
            thing = cp.wrap(target, "thing", ["step"])
            for burst in range(bursts):
                gate, crashed = threading.Barrier(threads_per_burst), []
                before = len(target.log)

                def go(gate=gate, crashed=crashed):
                    gate.wait(timeout=20)
                    try:
                        thing.step()
                    except SimulatedCrash as exc:
                        crashed.append(exc.point)

                cp.arm(POINT)
                threads = [threading.Thread(target=go) for _ in range(threads_per_burst)]
                for t in threads:
                    t.start()
                for t in threads:
                    t.join(timeout=30)
                assert not any(t.is_alive() for t in threads)
                assert crashed == [POINT], (burst, crashed)
                assert len(target.log) - before == threads_per_burst - 1, burst
            assert len(cp.fired) == bursts
    finally:
        sys.setswitchinterval(old)


def test_f9_a_flag_that_is_refused_twice_is_deleted_at_the_third_try(tmp_path, monkeypatch):
    """A delete refused twice: it is tried again (Windows can refuse while a reader holds the file);
    no "could not be deleted" error when a retry works."""
    flag, real, calls = tmp_path / "flag", Path.unlink, []

    def flaky(self, *args, **kwargs):
        calls.append(1)
        if len(calls) <= 2:
            raise PermissionError("held open")
        real(self, *args, **kwargs)

    with (
        pytest.raises(RuntimeError, match="never fired"),  # armed and left: this error, not "stuck"
        CrashPoints(mode="exit", flag_path=flag) as cp,
    ):
        cp.arm(POINT)
        monkeypatch.setattr(Path, "unlink", flaky)
    monkeypatch.undo()
    assert len(calls) == 3 and not flag.exists()


# --- real PostgreSQL (skipped without HADAVIN_TEST_PG_DSN) ----------------------------------------


@pytest.mark.parametrize("edge,row_is_there", [("after", True), ("before", False)])
def test_p1_kill_mode_on_a_real_database(tmp_path, edge, row_is_there):
    """P1: a child that opens the postgres store on a fresh schema is killed at
    `store.create_run:<edge>`; the parent then finds the row (after) or no row (before)."""
    for dsn in pg_schema():
        from hadavin_sdk.store.postgres import PostgresStore, connect

        flag = tmp_path / "flag"
        CrashPoints(mode="exit", flag_path=flag).arm(f"store.create_run:{edge}")
        done = start_child(
            tmp_path, CHILD_PG, flag, RID, env={**os.environ, "CRASH_CHILD_DSN": dsn}
        )
        assert done.returncode == CRASH_EXIT_CODE, done.stderr
        assert CRASH_MARKER in done.stdout and "survived" not in done.stdout
        assert not flag.exists()
        conn = connect(dsn)
        try:
            store = PostgresStore(conn)
            if row_is_there:
                assert store.get_run(RID).state is RunState.RECEIVED
            else:
                with pytest.raises(NotFound):
                    store.get_run(RID)
        finally:
            conn.close()


def test_e41_an_error_while_asking_if_the_flag_is_still_there_counts_as_still_there(
    tmp_path, no_real_exit, monkeypatch
):
    """E4-1 (Python 3.12 on Windows can raise PermissionError there): after a refused delete the error does not
    reach the code under test; the flag counts as still there, so nothing fires at this call."""
    flag = tmp_path / "flag"
    cp = CrashPoints(mode="exit", flag_path=flag)
    thing = cp.wrap(Thing(), "thing", ["step"])
    cp.arm(POINT)
    calls, _, restore = stub_unlink(monkeypatch, tmp_path, None)
    real_exists = os.path.exists

    def refuses(path):
        if os.fspath(path) == str(flag):
            raise PermissionError("not allowed to look")
        return real_exists(path)

    monkeypatch.setattr(os.path, "exists", refuses)
    assert crash_mod._still_there(flag) is True
    assert thing.step() == 1 and cp.fired == ()
    monkeypatch.setattr(os.path, "exists", real_exists)
    restore()
    assert len(calls) == crash_mod._UNLINK_TRIES and flag.exists()
    assert crash_mod._still_there(tmp_path / "nothing") is False
    flag.unlink()


def test_e41_leaving_the_block_with_a_refused_delete_and_a_failing_look_names_the_flag(
    tmp_path, monkeypatch
):
    flag = tmp_path / "flag"
    _, _, restore = stub_unlink(monkeypatch, tmp_path, None)
    real_exists = os.path.exists

    def refuses(path):
        if os.fspath(path) == str(flag):
            raise PermissionError("not allowed to look")
        return real_exists(path)

    with (
        pytest.raises(RuntimeError, match="could not be deleted"),
        CrashPoints(mode="exit", flag_path=flag) as cp,
    ):
        cp.arm(POINT)
        monkeypatch.setattr(os.path, "exists", refuses)
    monkeypatch.setattr(os.path, "exists", real_exists)
    restore()
    flag.unlink()
